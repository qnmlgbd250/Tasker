# -*- coding: utf-8 -*-
# @Time    : 2022/4/23 17:03
# @Author  : huni
# @Email   : zcshiyonghao@163.com
# @File    : task.py
# @Software: PyCharm
import random
import requests
from tools import Log
import os
import hashlib
from dotenv import load_dotenv
import re
import base64
import cv2
import numpy as np
import encrypt_tools

load_dotenv()
from Redis import RedisTool
import send_msg
import time
from schedule import every, repeat, run_pending
import schedule
import ddddocr


class SignCunHua(object):
    def __init__(self):
        self._url = os.getenv('CUNHUA_WEBSITE')
        self.username = os.getenv('CUNHUA_USERNAME')
        self.password = os.getenv('CUNHUA_PASSWORD')
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br', 'accept-language': 'zh-CN,zh;q=0.9',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36 Edg/100.0.1185.50'}
        self.requests_ = requests.session()
        self.RedisTool = RedisTool()
        self.log = Log()
        self.notice = send_msg.send_dingding

    def Identify_code(self):
        OCR = ddddocr.DdddOcr(show_ad = False)
        with open('code.jpg', 'rb') as f:
            text = OCR.classification(f.read())
        return text

    def _login(self):
        for _ in range(5):
            self.requests_.get(self._url, headers = self.headers)
            resp_ = self.requests_.get(
                f'{self._url}/member.php?mod=logging&action=login&infloat=yes&handlekey=login&inajax=1&ajaxtarget=fwin_content_login',
                headers = self.headers).text

            loginhash = re.findall(r'id="loginform_(.*?)"', resp_)[0]
            formhash = re.findall(r'name="formhash" value="(\S{8})"', resp_)[0]
            seccodehash = re.findall(r'<span id="seccode_(\S{9})"></span>', resp_)[0]

            resp_1 = self.requests_.get(
                f'{self._url}/misc.php?mod=seccode&action=update&idhash={seccodehash}&{random.random()}&modid=member::logging',
                headers = self.headers)

            id_ = re.findall(r'update=(\d+)', resp_1.text)[0]

            resp2 = self.requests_.get(f'{self._url}/misc.php?mod=seccode&update={id_}&idhash={seccodehash}',
                                       headers = self.headers)
            with open('code.jpg', 'wb') as f:
                f.write(resp2.content)
            pic_str = self.Identify_code()
            varify_code = self.requests_.get(
                f'{self._url}/misc.php?mod=seccode&action=check&inajax=1&modid=member::logging&idhash={seccodehash}&secverify={pic_str}',
                headers = self.headers)
            if 'succeed' in varify_code.text:
                self.log.success(f'验证码识别成功,验证码识别结果:{pic_str}')
            else:
                self.log.error(f'验证码错误,验证码识别结果:{pic_str}')
                continue

            login_url = f'{self._url}/member.php?mod=logging&action=login&loginsubmit=yes&handlekey=login&loginhash={loginhash}&inajax=1'
            data = {'formhash': formhash, 'referer': self._url, 'loginfield': 'username',
                    'username': self.username, 'password': self.password, 'questionid': '0',
                    'answer': '', 'seccodehash': seccodehash, 'seccodemodid': 'member::logging',
                    'seccodeverify': pic_str}

            resp3 = self.requests_.post(login_url, data = data, headers = self.headers)
            if '验证码填写错误' in resp3.text:
                self.log.error('验证码错误,返回结果:{}'.format(resp3.text))
            if '密码错误次数过多，请 15 分钟后重新登录' in resp3.text:
                self.log.error('密码错误次数过多，请 15 分钟后重新登录')
                break
            if '登录失败' in resp3.text:
                self.log.error('登录失败')

            else:
                self.log.success('自助登录成功')
                cookies = self.requests_.cookies.get_dict()
                cookie = ''
                for key, value in cookies.items():
                    cookie += key + '=' + value + ';'
                self.RedisTool.redis_set('Cookie_cunhua', cookie)
                self.log.success('Cookie保存到redis成功')
                break

    def login_with_cookie(self):
        cookie = self.RedisTool.redis_get('Cookie_cunhua')
        self.headers.update({'Cookie': cookie})
        resp = self.requests_.get(self._url, headers = self.headers)
        if '签到' in resp.text:
            self.log.success('cookie缓存登录成功')
            self.sign_today()
        else:
            self.log.error('cookie缓存登录失败')
            self._login()
            self.login_with_cookie()

    def sign_today(self):
        massage = '签到出错啦！！！'
        resp_ = self.requests_.get(self._url, headers = self.headers)
        if '今日已签' in resp_.text:
            self.log.info('今日已签到')
            massage = f'账号{os.getenv("CUNHUA_USERNAME")}今日已签,\n时间{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))}'
        else:
            formhash = re.findall(r'name="formhash" value="(\S{8})"', resp_.text)[0]
            resp = self.requests_.get(
                f'{self._url}/k_misign-sign.html?operation=qiandao&format=global_usernav_extra&formhash={formhash}&inajax=1&ajaxtarget=k_misign_topb',
                headers = self.headers)
            if '今日已签' in resp.text:
                self.log.info('今日已签到')
                massage = f'账号{os.getenv("CUNHUA_USERNAME")}今日已签,\n时间{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))}'
        self.log.success(massage)
        self.notice(massage)



class YunDong(object):
    def __init__(self):
        self.headers = {
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'referer': 'https://yd.shuabu.net/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36 Edg/100.0.1185.44'
        }
        self.url = os.getenv('YUNDONG_WEBSITE')
        self.log = Log()
        self.notice = send_msg.send_dingding

    def init_dict(self):
        phone_list_str = os.environ.get('PHONE_NUMBER')
        password_list_str = os.environ.get('PASSWORD')
        phone_list = phone_list_str.split(',')
        password_list = password_list_str.split(',')
        ppdict = dict(zip(phone_list, password_list))
        return ppdict

    def make_step(self, step_):
        ppdict = self.init_dict()
        massage = ''
        for phone, password in ppdict.items():
            for i in range(4):
                tim1 = str(int(time.time()))
                step1 = str(step_ + random.randint(1, 200))
                data1 = self.get_md5data(phone = phone, password = password, tim = tim1, step = step1)
                rep = requests.post(self.url, headers = self.headers, data = data1).json()
                self.log.success(f"返回信息>> {rep['msg']} ")
                if rep['msg'] == "同步成功":
                    massage += f'用户{phone}修改步数{step1}成功,重试次数{i}.\n时间{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))} \n\n'
                    break
                else:
                    self.log.info(f'第{i + 1}次修改步数失败,重试')
                    continue
        self.log.info(massage)
        self.notice(massage)

    def get_md5data(self, step, tim, phone, password):
        data_str = f'{phone}1{password}2{step}xjdsb{tim}'
        bt = base64.b64encode(data_str.encode('utf-8')).decode("utf-8")
        md5_val = hashlib.md5(bt.encode('utf8')).hexdigest()
        data = f'time={tim}&phone={phone}&password={password}&step={step}&key={md5_val}'
        return data

class Feige(object):
    def __init__(self):
        self.requests_ = requests.Session()
        self.url = os.getenv('FEIGE_WEBSITE')
        self.requests_.get(self.url)
        self.log = Log()
        self.notice = send_msg.send_dingding

    def get_yzm(self):
        json_data = {
            "captchaType": "blockPuzzle",
            "clientUid": "slider-477ad1f5-c470-45e8-ba3a-f997bef1b55c",
            "ts": str(int(time.time() * 1000))
        }
        res_captcha = self.requests_.post(f"{self.url}/captcha/get", json=json_data, verify=False)
        res_json = res_captcha.json()
        jigsaw_base64 = original_base64 = secret_key = token = ''
        if res_json["success"]:
            rep_data = res_json["repData"]
            token = rep_data["token"]
            secret_key = rep_data["secretKey"]
            jigsaw_base64 = rep_data["jigsawImageBase64"]  # 滑块图片
            original_base64 = rep_data["originalImageBase64"]  # 背景图片
            with open('test.png', 'wb') as f:
                f.write(base64.b64decode(original_base64))
        move_left_distance = self.get_captcha_distance(original_base64, jigsaw_base64)
        distance_msg = '{"x":%s,"y":5}' % move_left_distance
        point_json = self.aes_encrypt(distance_msg, secret_key)
        json_check_captcha = {
            "captchaType": "blockPuzzle",
            "clientUid": "slider-477ad1f5-c470-45e8-ba3a-f997bef1b55c",
            "ts": str(int(time.time() * 1000)),
            "pointJson": point_json,
            "token": token,
        }
        res_check_captcha = self.requests_.post(f"{self.url}/captcha/check", json=json_check_captcha)
        if res_check_captcha.json()["success"]:
            captcha_ver = self.aes_encrypt(token + "---" + distance_msg, secret_key)
            return captcha_ver

    def get_captcha_distance(self, original_base64, jigsaw_base64):
        """调用opencv识别滑块验证码"""
        # cv读取返回的图片数据
        image_cut = self.base64_to_image(jigsaw_base64)
        image_bg = self.base64_to_image(original_base64)
        # 寻找最佳匹配
        res = cv2.matchTemplate(self._tran_canny(image_cut), self._tran_canny(image_bg), cv2.TM_CCOEFF_NORMED)
        # 最小值，最大值，并得到最小值, 最大值的索引
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        top_left = max_loc[0]  # 横坐标
        return top_left

    def base64_to_image(self, base64_code):
        # base64解码
        img_data = base64.b64decode(base64_code)
        # 转换为np数组
        img_array = np.frombuffer(img_data, np.uint8)
        # 转换成opencv可用格式
        img = cv2.imdecode(img_array, cv2.IMREAD_GRAYSCALE)
        return img

    def _tran_canny(self, image):
        """消除噪声"""
        image = cv2.GaussianBlur(image, (3, 3), 0)
        return cv2.Canny(image, 50, 150)

    def aes_encrypt(self, word, key):
        """AES加密"""

        aes_cipher = encrypt_tools.AESCipher(key)
        encrypted = aes_cipher.encrypt(word)
        return encrypted

    def login_(self):
        post_data = {
            'email': os.environ.get('FEIGE_USER'),
            'password': os.environ.get('FEIGE_NUMBER'),
            'rememberMe': '1',
        }
        rep = self.requests_.post(f'{self.url}/login',data=post_data)
        self.log.info('飞鸽登录返回信息'+ str(rep.text))
    def sign_(self):
        self.login_()
        json_data = {"captchaVerification": self.get_yzm()}
        headers = {
            'content-type': 'application/json;charset=UTF-8',
        }
        res_sign = self.requests_.post(f"{self.url}/signIn", json=json_data,
                                       headers=headers)
        self.log.info('飞鸽内网穿透签到返回信息'+ str(res_sign.json()))
        if res_sign.json()['success']:

            msg = '飞鸽内网穿透签到返回信息:' + res_sign.json()['success'] + '连续签到天数:' + res_sign.json()['days'] + '积分:' + res_sign.json()['points']
            self.notice(msg)





SignCunHua = SignCunHua()
YunDong = YunDong()
Feige = Feige()


def do_cunhua_sign():
    SignCunHua.login_with_cookie()


def do_yundong(steps):
    YunDong.make_step(steps)

def do_feige():
    Feige.sign_()




schedule.every().day.at("07:30").do(do_cunhua_sign)
schedule.every().day.at("08:00").do(do_feige)


schedule.every().day.at("08:30").do(do_yundong, steps = random.randint(400, 1400))
schedule.every().day.at("09:30").do(do_yundong, steps = random.randint(1600, 2200))
schedule.every().day.at("10:30").do(do_yundong, steps = random.randint(2301, 2600))
schedule.every().day.at("11:30").do(do_yundong, steps = random.randint(2701, 3100))

schedule.every().day.at("15:30").do(do_yundong, steps = random.randint(4000, 5000))
schedule.every().day.at("16:30").do(do_yundong, steps = random.randint(5201, 5700))
schedule.every().day.at("17:30").do(do_yundong, steps = random.randint(6000, 8000))
schedule.every().day.at("18:30").do(do_yundong, steps = random.randint(9000, 12999))
schedule.every().day.at("19:30").do(do_yundong, steps = random.randint(13000, 17000))
schedule.every().day.at("20:30").do(do_yundong, steps = random.randint(17987, 22000))


def run():
    while True:
        schedule.run_pending()
        time.sleep(1)

# 测试用
# Feige.sign_()
# SignCunHua.login_with_cookie()

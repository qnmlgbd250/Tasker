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
import base64
from dotenv import load_dotenv
import re

load_dotenv()
from Redis import RedisTool
import send_msg
import time
from schedule import every, repeat, run_pending
import schedule


class Sign(object):
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
        import ddddocr
        OCR = ddddocr.DdddOcr(show_ad = False)
        with open('code.jpg', 'rb') as f:
            text = OCR.classification(f.read())
        return text

    def _login(self):
        for _ in range(5):
            self.requests_.get(self._url, headers = self.headers)
            resp_ = self.requests_.get(
                f'{self._url}/member.php?mod=logging&action=login&infloat=yes&handlekey=login&inajax=1&ajaxtarget=fwin_content_login', ).text

            loginhash = re.findall(r'id="loginform_(.*?)"', resp_)[0]
            formhash = re.findall(r'name="formhash" value="(\S{8})"', resp_)[0]
            seccodehash = re.findall(r'<span id="seccode_(\S{9})"></span>', resp_)[0]

            resp_1 = self.requests_.get(
                f'{self._url}/misc.php?mod=seccode&action=update&idhash={seccodehash}&{random.random()}&modid=member::logging')

            id_ = re.findall(r'update=(\d+)', resp_1.text)[0]

            resp2 = self.requests_.get(f'{self._url}/misc.php?mod=seccode&update={id_}&idhash={seccodehash}', )
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

            resp3 = self.requests_.post(login_url, data = data)
            if '验证码填写错误' in resp3.text:
                self.log.error('验证码错误,返回结果:{}'.format(resp3.text))
            if '密码错误次数过多，请 15 分钟后重新登录' in resp3.text:
                self.log.error('密码错误次数过多，请 15 分钟后重新登录')
                break
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
        if '登录' not in resp.text:
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
            massage = f'账号{os.getenv("CUNHUA_USER")}今日已签,时间{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))}'
        else:
            formhash = re.findall(r'name="formhash" value="(\S{8})"', resp_.text)[0]
            resp = self.requests_.get(
                f'{self._url}/k_misign-sign.html?operation=qiandao&format=global_usernav_extra&formhash={formhash}&inajax=1&ajaxtarget=k_misign_topb',
                headers = self.headers)
            if '今日已签' in resp.text:
                self.log.info('今日已签到')
                massage = f'账号{os.getenv("CUNHUA_USER")}今日已签,时间{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))}'
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
                    self.log.info(f'第{i+1}次修改步数失败,重试')
                    continue
        self.log.info(massage)
        self.notice(massage)

    def get_md5data(self, step, tim, phone, password):
        data_str = f'{phone}1{password}2{step}xjdsb{tim}'
        bt = base64.b64encode(data_str.encode('utf-8')).decode("utf-8")
        md5_val = hashlib.md5(bt.encode('utf8')).hexdigest()
        data = f'time={tim}&phone={phone}&password={password}&step={step}&key={md5_val}'
        return data


Sign = Sign()
YunDong = YunDong()


def do_sign():
    Sign.login_with_cookie()


def do_yundong(steps):
    YunDong.make_step(steps)


schedule.every().day.at("07:30").do(do_sign)

schedule.every().day.at("07:40").do(do_yundong, steps = random.randint(0, 600))
schedule.every().day.at("08:30").do(do_yundong, steps = random.randint(800, 1400))
schedule.every().day.at("09:30").do(do_yundong, steps = random.randint(1600, 2200))
schedule.every().day.at("10:30").do(do_yundong, steps = random.randint(2301, 2600))
schedule.every().day.at("11:30").do(do_yundong, steps = random.randint(2701, 3100))

schedule.every().day.at("14:30").do(do_yundong, steps = random.randint(3201, 3700))
schedule.every().day.at("15:30").do(do_yundong, steps = random.randint(4000, 5000))
schedule.every().day.at("16:30").do(do_yundong, steps = random.randint(5201, 5700))
schedule.every().day.at("17:30").do(do_yundong, steps = random.randint(5701, 6500))
schedule.every().day.at("18:30").do(do_yundong, steps = random.randint(10000, 11000))
schedule.every().day.at("19:30").do(do_yundong, steps = random.randint(13000, 15000))
schedule.every().day.at("20:30").do(do_yundong, steps = random.randint(17987, 21000))


def run():
    while True:
        schedule.run_pending()
        time.sleep(1)

# 测试用
# Sign._login()
# Sign.login_with_cookie()

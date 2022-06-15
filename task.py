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
# import cv2
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


# class SignMoXing(object):
#     def __init__(self):
#         self._url = os.getenv('MOXING_WEBSITE')
#         self.username = os.getenv('MOXING_USERNAME')
#         self.password = os.getenv('MOXING_PASSWORD')
#         self.headers = {
#             'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
#             'accept-encoding': 'gzip, deflate, br', 'accept-language': 'zh-CN,zh;q=0.9',
#             'upgrade-insecure-requests': '1',
#             'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36 Edg/100.0.1185.50'}
#         self.requests_ = requests.session()
#         self.RedisTool = RedisTool()
#         self.log = Log()
#         self.notice = send_msg.send_dingding
#
#     def _login(self):
#         for _ in range(10):
#             resp1 = self.requests_.get(f'{self._url}/member.php?mod=logging&action=login', headers = self.headers)
#             loginhash = re.findall(r'loginhash=(.*?)', resp1.text)[0]
#             formhash = re.findall(r'name="formhash" value="(\S{8})"', resp1.text)[0]
#
#             verify_code = self.requests_.get(f'{self._url}/captcha/tncode.php?t={random.random()}',
#                                              headers = self.headers)
#             with open('verify_code.webp', 'wb') as f:
#                 f.write(verify_code.content)
#             self.cut_webp_to_png()
#             code_distance = self.Identify_code()
#             skip_code = self.requests_.get(f'{self._url}/captcha/check.php?tn_r={code_distance}',
#                                            headers = self.headers)
#             if 'error' in skip_code.text:
#                 self.log.error('验证码错误')
#                 continue
#             else:
#                 clicaptcha_submit_info = skip_code.text
#             login_params = {
#                 'mod': 'logging',
#                 'action': 'login',
#                 'loginsubmit': 'yes',
#                 'loginhash': loginhash,
#                 'inajax': '1',
#             }
#             login_data = {
#                 'formhash': formhash,
#                 'referer': f'{self._url}/home.php?mod=space&do=friend',
#                 'username': self.username,
#                 'password': self.password,
#                 'questionid': '0',
#                 'answer': '',
#                 'clicaptcha-submit-info': clicaptcha_submit_info,
#             }
#             login_resp = self.requests_.post(f'{self._url}/member.php', params = login_params, data = login_data,
#                                              headers = self.headers)
#             if '欢迎您回来' in login_resp.text:
#                 self.log.success('登录成功')
#                 cookies = self.requests_.cookies.get_dict()
#                 cookie = ''
#                 for key, value in cookies.items():
#                     cookie += key + '=' + value + ';'
#                 self.RedisTool.redis_set('Cookie_moxing', cookie)
#                 self.log.success('Cookie保存到redis成功')
#                 break
#
#     def login_with_cookie(self):
#         cookie = self.RedisTool.redis_get('Cookie_moxing')
#         self.headers.update({'Cookie': cookie})
#         resp = self.requests_.get(f'{self._url}/forum.php', headers = self.headers)
#         if '登录' not in resp.text:
#             self.log.success('cookie缓存登录成功')
#             # self.sign_today()
#         else:
#             self.log.error('cookie缓存登录失败')
#             self._login()
#             self.login_with_cookie()
#
#     def sign_today(self):
#         resp = self.requests_.get(f'{self._url}/plugin.php?id=dsu_paulsign:sign', headers = self.headers)
#         if '今日已签到' in resp.text:
#             self.log.success('今日已签到')
#         else:
#             self.log.success('今日签到成功')
#
#     def cut_webp_to_png(self):
#         # 裁剪图片
#         img = cv2.imread('verify_code.webp')
#         bg_img = img[0:150, 0:240]
#         sk_img = img[300:450, 0:240]
#         path = os.path.abspath('.')
#         cv2.imwrite(path + '/bg_1.png', bg_img)
#         cv2.imwrite(path + '/bg_2.png', sk_img)
#         self.log.info('裁剪完成')
#
#     def Identify_code(self):
#         det = ddddocr.DdddOcr(det = False, ocr = False, show_ad = False)
#         with open('bg_1.png', 'rb') as f:
#             target_bytes = f.read()
#         with open('bg_2.png', 'rb') as f:
#             background_bytes = f.read()
#         res = det.slide_comparison(target_bytes, background_bytes)
#         self.log.info('识别结果：' + str(res))
#         return res.get('target', [0])[0]


class SignBZJ(object):
    def __init__(self):
        self._url = os.getenv('BZJ_WEBSITE')
        self.username = os.getenv('BZJ_USERNAME')
        self.password = os.getenv('BZJ_PASSWORD')
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36 Edg/102.0.1245.30',
        }
        self.requests_ = requests.session()
        self.RedisTool = RedisTool()
        self.log = Log()
        self.notice = send_msg.send_dingding

    def init_dict(self):
        phone_list_str = os.environ.get('BZJ_USERNAME')
        password_list_str = os.environ.get('BZJ_PASSWORD')
        phone_list = phone_list_str.split(',')
        password_list = password_list_str.split(',')
        ppdict = dict(zip(phone_list, password_list))
        return ppdict

    def _login(self, username, password):
        # ppdict = self.init_dict()
        # for username, password in ppdict.items():
        data = {
            'nickname': '',
            'username': username,
            'password': password,
            'code': '',
            'img_code': '',
            'invitation_code': '',
            'token': '',
            'smsToken': '',
            'luoToken': '',
            'confirmPassword': '',
            'loginType': '',
        }
        res = requests.post(f'{self._url}/wp-json/jwt-auth/v1/token', data = data, headers = self.headers)
        if 'token' in str(res.json()):
            return res.json()['token']
            # self.RedisTool.redis_set(f'Token_BZJ_{username}', res.json()['token'])
            # self.log.success(f'Token_BZJ_{username}保存到redis成功')

    def sign_with_cookie(self):
        manage = ''
        ppdict = self.init_dict()
        for username, password in ppdict.items():
            # token = self.RedisTool.redis_get(f'Token_BZJ_{username}')
            token = self._login(username, password)
            try:
                self.requests_.get(f'{self._url}/mission/today', headers = self.headers)
                self.headers.update({'authorization': 'Bearer {}'.format(token)})
                data = {
                    'ref': 'null',
                }
                self.requests_.post(f'{self._url}/wp-json/b2/v1/getUserInfo', headers = self.headers, data = data)
                data = []
                self.requests_.post(f'{self._url}/wp-json/b2/v1/getLatestAnnouncement', headers = self.headers,data = data)
                data = {
                    'count': '10',
                    'paged': '1',
                }
                self.requests_.post(f'{self._url}/wp-json/b2/v1/getUserMission', headers = self.headers,
                                      data = data)
                self.requests_.post(f'{self._url}/wp-json/b2/v1/tjuser', headers = self.headers)
                resp = self.requests_.post(f'{self._url}/wp-json/b2/v1/userMission', headers = self.headers)
                self.log.info(f'账号{username}今日签到获得积分' + str(resp.json()))
                manage += f'账号{username}今日签到获得积分' + (str(resp.json().get("credit",'')) if isinstance(resp.json(),dict) else  str(resp.json()))+ '\t'
                data = {
                    'ref': 'null',
                }
                res = self.requests_.post(f'{self._url}/wp-json/b2/v1/getUserInfo', headers = self.headers, data = data)
                self.log.info(f'账户积分' + str(res.json()['credit']))
                manage += f'账户积分' + str(res.json()[
                                            'credit']) + f'\n时间{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))} \n\n'
            except:
                self._login(username, password)
                self.sign_with_cookie()
        self.notice(manage)


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


SignCunHua = SignCunHua()
# SignMoXing = SignMoXing()
SignBZJ = SignBZJ()
YunDong = YunDong()


def do_cunhua_sign():
    SignCunHua.login_with_cookie()


def do_bzj_sign():
    SignBZJ.sign_with_cookie()


def do_yundong(steps):
    YunDong.make_step(steps)


schedule.every().day.at("07:30").do(do_cunhua_sign)
schedule.every().day.at("07:35").do(do_bzj_sign)

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
# SignBZJ.sign_with_cookie()
# SignCunHua.login_with_cookie()

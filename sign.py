# -*- coding: utf-8 -*-
# @Time    : 2022/4/23 17:03
# @Author  : huni
# @Email   : zcshiyonghao@163.com
# @File    : sign.py
# @Software: PyCharm
import random
import requests
from tools import Log
import os
from dotenv import load_dotenv
import re

load_dotenv()
from Redis import RedisTool
import send_msg
import time


class Sign(object):
    def __init__(self):
        self._url = os.getenv('CUNHUA_WEBSITE')
        self.username = os.getenv('CUNHUA_USERNAME')
        self.password = os.getenv('CUNHUA_PASSWORD')
        self.headers = {
            'Cookie': '',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br', 'accept-language': 'zh-CN,zh;q=0.9',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36 Edg/100.0.1185.50'}
        self.requests_ = requests.session()
        self.RedisTool = RedisTool()
        self.log = Log()

    def Identify_code(self):
        import ddddocr
        OCR = ddddocr.DdddOcr(show_ad=False)
        with open('code.jpg', 'rb') as f:
            text = OCR.classification(f.read())
        return text

    def _login(self):
        for _ in range(5):
            self.requests_.get(self._url, headers=self.headers)
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
                headers=self.headers)
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

            resp3 = self.requests_.post(login_url, data=data)
            if '验证码填写错误' in resp3.text:
                self.log.error('验证码错误,返回结果:{}'.format(resp3.text))
            else:
                self.log.success('自助登录成功')
                self.save_cookie()
                break


    def save_cookie(self):
        cookies = self.requests_.cookies.get_dict()
        cookie = ''
        for key, value in cookies.items():
            cookie += key + '=' + value + ';'
        self.RedisTool.redis_set('Cookie_cunhua', cookie)
        self.log.success('Cookie保存到redis成功')

    def login_with_cookie(self):
        cookie = '_ga=GA1.2.556904626.1649494043; n4XN_2132_saltkey=JGzCzc08; n4XN_2132_lastvisit=1650803729; _gid=GA1.2.337403476.1650980551; n4XN_2132_sendmail=1; _gat_gtag_UA_144688693_3=1; n4XN_2132_sid=KhGFss; n4XN_2132_seccode=13573.82dd9bbd147d4d05de; n4XN_2132_ulastactivity=326eaxrI7pXxRVXAxJL16tZGypxjJZjwfD25wUeew9qeqceDfJe5; n4XN_2132_auth=638a%2F33CMRA%2ByaZjRZTRYQKnWSjFX3Btv5wPu7F1Fr3g8Zh0vWG3Z7pLjnLvPA1wO3dg99AAVl%2B7bPeTFELvkYKq3Yo; n4XN_2132_lastcheckfeed=198866%7C1650980838; n4XN_2132_checkfollow=1; n4XN_2132_lip=210.21.226.100%2C1650963287; n4XN_2132_member_login_status=1; n4XN_2132_nofavfid=1; n4XN_2132_checkpm=1; n4XN_2132_lastact=1650980842%09misc.php%09patch'
        self.headers.update({'Cookie': cookie})
        resp = self.requests_.get(self._url, headers=self.headers)
        if '登录' not in resp.text:
            self.log.success('cookie缓存登录成功')
            # send_msg.send_dingding('cookie缓存登录成功')
            self.sign_today()
        else:
            self.log.error('cookie缓存登录失败')
            self._login()
            self.login_with_cookie()

    def sign_today(self):
        massage = ''
        resp_ = self.requests_.get(self._url, headers=self.headers)
        if '今日已签' in resp_.text:
            self.log.info('今日已签到')
            massage = f'账号{os.getenv("CUNHUA_USER")}今日已签,时间{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))}'
        else:
            formhash = re.findall(r'name="formhash" value="(\S{8})"', resp_.text)[0]
            resp = self.requests_.get(f'{self._url}/k_misign-sign.html?operation=qiandao&format=global_usernav_extra&formhash={formhash}b&inajax=1&ajaxtarget=k_misign_topb', headers=self.headers)
            if '今日已签' in resp_.text:
                self.log.info('今日已签到')
                massage = f'账号{os.getenv("CUNHUA_USER")}今日已签,时间{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))}'
        self.log.success(massage)
        send_msg.send_dingding(massage)


if __name__ == '__main__':
    sign = Sign()
    sign.login_with_cookie()

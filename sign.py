# -*- coding: utf-8 -*-
# @Time    : 2022/4/23 17:03
# @Author  : huni
# @Email   : zcshiyonghao@163.com
# @File    : sign.py
# @Software: PyCharm
import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()
from chaojiying import Chaojiying_Client


class Sign(object):
    def __init__(self):
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br', 'accept-language': 'zh-CN,zh;q=0.9',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36 Edg/100.0.1185.50'}
        self.requests_ = requests.Session()

    def get_code(self):
        self.requests.get('https://www.cunhua.shop/', headers = self.headers)
        time.sleep(1)
        self.requests.get('https://www.cunhua.shop/home.php?mod=misc&ac=sendmail&rand=1650798602',
                          headers = self.headers)
        time.sleep(0.3)
        self.requests.get(
            'https://www.cunhua.shop/member.php?mod=logging&action=login&infloat=yes&handlekey=login&inajax=1&ajaxtarget=fwin_content_login',
            headers = self.headers)
        time.sleep(0.3)
        self.requests.get(
            'https://www.cunhua.shop/misc.php?mod=seccode&action=update&idhash=cSAhMQeqy&0.539828999054315&modid=member::logging ',
            headers = self.headers)
        time.sleep(0.3)

        resp = self.requests.get('https://www.cunhua.shop/misc.php?mod=seccode&update=40430&idhash=cSAhMQeqy',
                                 headers = self.headers)
        time.sleep(1)
        with open('code.jpg', 'wb') as f:
            f.write(resp.content)

    def Identify_code(self):
        Chaojiying_Client()
        im = open('code.jpg', 'rb').read()
        pic_str = Chaojiying_Client().PostPic(im, 1902)['pic_str']
        print(pic_str)

    def _login(self):
        # 首页
        self.requests_.get('https://www.cunhua.shop/', headers = self.headers)
        time.sleep(0.5)
        # 登录
        self.requests_.get(
            'https://www.cunhua.shop/member.php?mod=logging&action=login&infloat=yes&handlekey=login&inajax=1&ajaxtarget=fwin_content_login',)
        # 验证码模板
        time.sleep(0.5)
        self.requests_.get(
            'https://www.cunhua.shop/misc.php?mod=seccode&action=update&idhash=cSAxPFNTa&0.5634774256588155&modid=member::logging',)

        for i in range(3):
            self.requests_.get('https://www.cunhua.shop/misc.php?mod=seccode&action=update&idhash=cSACemlsZ&0.07077478295800965&modid=undefined')
            time.sleep(0.5)
            # 验证码图片
            resp = self.requests_.get('https://www.cunhua.shop/misc.php?mod=seccode&update=21249&idhash=cSAxPFNTa',)
            time.sleep(0.5)
            with open('code.jpg', 'wb') as f:
                f.write(resp.content)
            pic_str = input('请输入验证码：')
            varify_code = self.requests_.get(
                f'https://www.cunhua.shop/misc.php?mod=seccode&action=check&inajax=1&modid=member::logging&idhash=cSAl1s9ug&secverify={pic_str}',
                headers = self.headers)
            if 'succeed' in varify_code.text:
                print('验证码正确')
            else:
                print('验证码错误')
            time.sleep(0.3)
            login_url = 'https://www.cunhua.shop/member.php?mod=logging&action=login&loginsubmit=yes&handlekey=login&loginhash=LA4Ff&inajax=1'
            data = {'formhash': '0368eb0f', 'referer': 'https://www.cunhua.shop', 'loginfield': 'username', 'username': '用手机某人咯', 'password': '81995071c1bb547c9ec11f27f70b449f', 'questionid': '0', 'answer': '', 'seccodehash': 'cSAl1s9ug', 'seccodemodid': 'member::logging', 'seccodeverify': pic_str}

            # self.headers['Cookie'] = 'n4XN_2132_sendmail=1;'
            # for key, value in self.requests_.cookies.get_dict().items():
            #     if key == 'n4XN_2132_sendmail':
            #         continue
            #     self.headers['Cookie'] += f'{key}={value};'

            resp = self.requests_.post(login_url, data = json.dumps(data))
            if '验证码填写错误' in resp.text:
                print(resp.text)
                continue
            else:
                print('登录成功')


if __name__ == '__main__':
    sign = Sign()
    sign._login()

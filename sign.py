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



class Sign(object):
    def __init__(self):
        self._url = os.environ.get('CUNHUA_WEBSITE')
        self.username = os.environ.get('CUNHUA_USERNAME')
        self.password = os.environ.get('CUNHUA_PASSWORD')
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br', 'accept-language': 'zh-CN,zh;q=0.9',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36 Edg/100.0.1185.50'}
        self.requests_ = requests.session()
        self.log = Log()

    def Identify_code(self,img):
        import ddddocr
        OCR = ddddocr.DdddOcr(show_ad=False)
        return OCR.classification(img)

    def _login(self):
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
        pic_str = self.Identify_code(f.read())
        varify_code = self.requests_.get(
            f'{self._url}/misc.php?mod=seccode&action=check&inajax=1&modid=member::logging&idhash={seccodehash}&secverify={pic_str}',
            headers=self.headers)
        if 'succeed' in varify_code.text:
            self.log.success(f'验证码识别成功,验证码识别结果:{pic_str}')
        else:
            print('验证码错误')

        login_url = f'{self._url}/member.php?mod=logging&action=login&loginsubmit=yes&handlekey=login&loginhash={loginhash}&inajax=1'
        data = {'formhash': formhash, 'referer': self._url, 'loginfield': 'username',
                'username': self.username, 'password': self.password, 'questionid': '0',
                'answer': '', 'seccodehash': seccodehash, 'seccodemodid': 'member::logging',
                'seccodeverify': pic_str}

        resp3 = self.requests_.post(login_url, data=data)
        if '验证码填写错误' in resp3.text:
            print(resp3.text)
        else:
            print(resp3.text)
            print('登录成功')


if __name__ == '__main__':
    sign = Sign()
    sign._login()

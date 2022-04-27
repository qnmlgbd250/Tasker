# -*- coding: utf-8 -*-
# @Time    : 2022/4/18 19:32
# @Author  : huni
# @Email   : zcshiyonghao@163.com
# @File    : yun.py
# @Software: PyCharm
import requests
import time
import hashlib
import base64
import random
import os
from schedule import every, repeat, run_pending
from tools import Log

import send_msg
from dotenv import load_dotenv

load_dotenv()
log = Log()

headers = {
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'referer': 'https://yd.shuabu.net/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36 Edg/100.0.1185.44'
}

phone_list_str = os.environ.get('PHONE_NUMBER')
password_list_str = os.environ.get('PASSWORD')

phone_list = phone_list_str.split(',')
password_list = password_list_str.split(',')

ppdict = dict(zip(phone_list, password_list))

a = random.randint(0, 1000)
b = random.randint(1500, 2000)
c = random.randint(2001, 2500)
d = random.randint(2501, 3000)
e = random.randint(3001, 3600)
f = random.randint(4000, 5000)
g = random.randint(5001, 5200)
h = random.randint(5500, 6000)
i = random.randint(10000, 11000)
j = random.randint(13000, 15000)
k = random.randint(17761, 21000)


@repeat(every().day.at("08:30"), a, ppdict)
@repeat(every().day.at("09:30"), b, ppdict)
@repeat(every().day.at("10:30"), c, ppdict)
@repeat(every().day.at("11:30"), d, ppdict)
@repeat(every().day.at("14:46"), e, ppdict)
@repeat(every().day.at("15:30"), f, ppdict)
@repeat(every().day.at("16:30"), g, ppdict)
@repeat(every().day.at("17:30"), h, ppdict)
@repeat(every().day.at("18:30"), i, ppdict)
@repeat(every().day.at("19:30"), j, ppdict)
@repeat(every().day.at("20:30"), k, ppdict)
def yundong(step_, ppdict: dict):
    tim = str(int(time.time()))
    for phone, password in ppdict.items():
        step = str(step_ + random.randint(1, 200))
        data = f'{phone}1{password}2{step}xjdsb{tim}'
        bt = base64.b64encode(data.encode('utf-8')).decode("utf-8")
        md5_val = hashlib.md5(bt.encode('utf8')).hexdigest()
        data = f'time={tim}&phone={phone}&password={password}&step={step}&key={md5_val}'
        rep = requests.post('https://api.shuabu.net/apix/xm.php', headers = headers, data = data).json()
        log.success(f"返回信息>> {rep['msg']} ")
        massage = f'账号{phone}刷步数{step},返回信息:{rep["msg"]},时间{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))}'
        log.info(massage)
        if any(rep['msg'] in i for i in ['同步失败', '登录失败，账户或密码错误']):
            rep2 = requests.post('https://api.shuabu.net/apix/xm.php', headers = headers, data = data).json()
            massage = f'账号{phone}刷步数{step},返回信息:第一次{rep["msg"]},第二次{rep2["msg"]},时间{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))}'
            log.info(massage)
        send_msg.send_dingding(massage)


def run():
    while True:
        run_pending()

        time.sleep(1)

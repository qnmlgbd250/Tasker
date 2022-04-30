# -*- coding: utf-8 -*-
# @Time    : 2022/4/30 10:22
# @Author  : huni
# @Email   : zcshiyonghao@163.com
# @File    : test.py
# @Software: PyCharm
import requests
import json

res = requests.post('http://127.0.0.1:8000/items', data=json.dumps({'price':'100'}))
print(res.text)
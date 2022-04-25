# -*- coding: utf-8 -*-
# @Time    : 2022/4/23 17:08
# @Author  : huni
# @Email   : zcshiyonghao@163.com
# @File    : 格式化.py
# @Software: PyCharm
s ='''
formhash: 0368eb0f
referer: https://www.cunhua.shop
loginfield: username
username: 用手机某人咯
password: 81995071c1bb547c9ec11f27f70b449f
questionid: 0
answer: 
seccodehash: cSAl1s9ug
seccodemodid: member::logging
seccodeverify: cgg2
'''



ls = s.split('\n')
lsl = []
ls = ls[1:-1]
headers = {}
for l in ls:
    l = l.split(': ')
    lsl.append(l)
for x in lsl:
    headers[str(x[0]).strip('    ')] = x[1]
print(headers)
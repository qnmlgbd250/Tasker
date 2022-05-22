# -*- coding: utf-8 -*-
# @Time    : 2022/4/30 10:22
# @Author  : huni
# @Email   : zcshiyonghao@163.com
# @File    : test.py
# @Software: PyCharm
import requests
import json
import time
import random
import ddddocr
import os
import cv2
import numpy as np

requests_ = requests.session()
def save_webp():
    headers = {
    	'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.53',
    	'accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    	'referer': 'https://laowangebe387.us/member.php?mod=logging&action=login',

    }
    res = requests_.get(f'https://laowangebe387.us/captcha/tncode.php?t={random.random()}',headers=headers)
    # 下载完整图片
    with open('test.webp','wb') as f:
        f.write(res.content)
        print('下载完成')

def cut_webp_to_png():
    # 裁剪图片
    img = cv2.imread('test.webp')
    bg_img = img[0:150,0:240]
    sk_img = img[300:450,0:240]
    path = os.path.abspath('.')
    cv2.imwrite(path + '/bg_1.png',bg_img)
    cv2.imwrite(path + '/bg_2.png',sk_img)
    print('裁剪完成')

def ocr_():
    det = ddddocr.DdddOcr(det = False, ocr = False,show_ad=False)
    with open('bg_1.png', 'rb') as f:
        target_bytes = f.read()

    with open('bg_2.png', 'rb') as f:
        background_bytes = f.read()

    res = det.slide_comparison(target_bytes, background_bytes)

    print(res)


save_webp()
cut_webp_to_png()
# transPNG('sk.png','sk2.png')
ocr_()
# ocr_2()
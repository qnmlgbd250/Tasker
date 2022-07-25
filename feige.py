# -*- coding: utf-8 -*-
# @Time    : 2022/7/25 19:55
# @Author  : huni
# @Email   : zcshiyonghao@163.com
# @File    : feige.py
# @Software: PyCharm
import requests
import re
import time
import base64
import cv2
import numpy as np
import encrypt_tools

class Feige(object):
    def __init__(self):
        self.requests_ = requests.Session()

        self.requests_.get('https://www.fgnwct.com/register.html')
    def get_yzm(self):
        json_data = {
            "captchaType": "blockPuzzle",
            "clientUid": "slider-477ad1f5-c470-45e8-ba3a-f997bef1b55c",
            "ts": str(int(time.time() * 1000))
        }
        res_captcha = self.requests_.post("https://www.fgnwct.com/captcha/get", json=json_data, verify=False)
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
        res_check_captcha = self.requests_.post("https://www.fgnwct.com/captcha/check", json=json_check_captcha)
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

    def sign_email(self):
        """注册"""
        json_data = {"captchaVerification":self.get_yzm()}
        print(json_data)
        headers = {
            'content-type': 'application/json;charset=UTF-8',
        }
        res_sign = self.requests_.post("https://www.fgnwct.com/sendMailVerifyCode/1096005725@qq.com", json=json_data,headers=headers)
        return res_sign.json()
fig = True
while fig:
    st = Feige().sign_email()
    print(st)
    if '请不要频繁发送验证码' in str(st):
        continue
    else:
        fig = False
        print(st)
        print('注册成功')
        break
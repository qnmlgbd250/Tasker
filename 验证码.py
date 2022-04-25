# -*- coding: utf-8 -*-
# @Time    : 2022/4/25 19:28
# @Author  : huni
# @Email   : zcshiyonghao@163.com
# @File    : 验证码.py
# @Software: PyCharm
import requests
import base64
requests.packages.urllib3.disable_warnings()
# import config
# if config.Env == "product":
#     PATH = 'https://www.kdzwy.com/captchaplatform/decodeCaptcha/'
# else:
PATH = 'https://mock.kdzwy.com/captchaplatform/decodeCaptcha/'
def decode(img, captcha_type=1001, captcha_desc=''):
    data = {
        'image': base64.b64encode(img),
        'captcha_type': 2006,
        'captcha_desc': captcha_desc
    }
    r = requests.post(PATH, data=data, verify=False)
    if r.status_code != 200: return 600, '链接打码平台失败'
    return r.text

def get_img(img_url):
    r = requests.get(img_url, verify=False,headers={
                    'Accept': 'image/webp,image/*,*/*;q=0.8'
                })
    if r.status_code != 200:
        return 600, '链接图片失败'
    with open('test.jpg', 'wb') as f:
        f.write(r.content)
    return r.content

print(decode(get_img('https://etax.xizang.chinatax.gov.cn:8443/download.sword?ctrl=CheckcodeCtrl_getCheckcode&id=sswszmcy_picimg&0.05987326043600061')))
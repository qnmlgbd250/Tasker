# -*- coding: utf-8 -*-
# @Time    : 2022/4/24 21:26
# @Author  : huni
# @Email   : zcshiyonghao@163.com
# @File    : sign_sele.py
# @Software: PyCharm

import os
from dotenv import load_dotenv
load_dotenv()
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
import time
from Redis import RedisTool
from tools import Log
import send_msg
from schedule import every, repeat, run_pending



class Sign(object):
    def __init__(self, **kwargs):
        super(Sign, self).__init__()
        self._url = os.getenv('CUNHUA_WEBSITE')
        self.RedisTool = RedisTool()
        self.log = Log()

    def _login(self):
        browser, wait = self.browser_initial()
        browser.get(self._url)
        # 点击登录
        login_btn = wait.until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="lsform"]/div/div/table/tbody/tr/td[1]/a')))
        login_btn.click()
        time.sleep(2)

        # 输入用户名
        username = wait.until(EC.presence_of_element_located((By.XPATH,
                                                              '/html/body/header/div[1]/div[1]/table/tbody/tr[2]/td[2]/div[1]/div[1]/form/div/div[1]/table/tbody/tr/td[1]/input')))
        username.send_keys(os.getenv('CUNHUA_USER'))

        # 输入密码
        password = wait.until(EC.presence_of_element_located((By.XPATH,
                                                              '/html/body/header/div[1]/div[1]/table/tbody/tr[2]/td[2]/div[1]/div[1]/form/div/div[2]/table/tbody/tr/td[1]/input')))
        password.send_keys(os.getenv('CUNHUA_PASSWORD'))

        # 输入验证码
        code_hand = input('请输入验证码:')
        code = wait.until(EC.presence_of_element_located((By.XPATH,
                                                          '/html/body/header/div[1]/div[1]/table/tbody/tr[2]/td[2]/div[1]/div[1]/form/div/span/div/table/tbody/tr/td/input')))
        code.send_keys(code_hand)

        # 点击登录
        login_btn = wait.until(EC.presence_of_element_located((By.XPATH,
                                                               '/html/body/header/div[1]/div[1]/table/tbody/tr[2]/td[2]/div[1]/div[1]/form/div/div[6]/table/tbody/tr/td[1]/button/strong')))
        login_btn.click()

        time.sleep(2)
        browser.refresh()
        if '登录' not in browser.page_source:
            self.log.success('自助登录成功')
            get_cookies_list = browser.get_cookies()
            self.RedisTool.redis_set('Cookies', get_cookies_list)
            return browser,wait
        else:
            self.log.error('自助登录失败')

    def login_with_cookie(self):
        browser, wait = self.browser_initial()
        browser.get(self._url)
        cookies = self.RedisTool.redis_str_to_list('Cookies')
        browser.delete_all_cookies()
        for item in cookies:
            browser.add_cookie(item)
        browser.refresh()
        time.sleep(2)
        if '登录' not in browser.page_source:
            self.log.success('携带cookie登录成功')
            return browser,wait
        else:
            self.log.error('携带cookie登录失败')
            self._login()

    def browser_initial(self):
        """
        初始化浏览器
        Returns:

        """
        options = webdriver.ChromeOptions()
        options.add_experimental_option("detach", True)  # 解决闪退
        options.add_experimental_option('excludeSwitches', ['enable-automation'])  # 规避检测
        # options.add_argument('blink-settings=imagesEnabled=false')  # 不加载图片, 提升速度
        browser = webdriver.Chrome(service = Service("chromedriver.exe"), options = options)

        browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                  get: () => undefined
                })
              """
        })
        browser.maximize_window()
        wait = WebDriverWait(browser, 100)
        return browser, wait

    def sign(self):
        browser, wait = self.login_with_cookie()
        if '今日已签' in browser.page_source:
            self.log.info('今日已签')
            massage = f'账号{os.getenv("CUNHUA_USER")}今日已签,时间{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))}'
        else:
            sign_btn = wait.until(EC.presence_of_element_located((By.ID,'fx_checkin_b')))
            sign_btn.click()
            massage = f'账号{os.getenv("CUNHUA_USER")}签到成功,时间{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))}'
        self.log.success(massage)
        send_msg.send_dingding(massage)
        browser.quit()


sign_ = Sign()


@repeat(every().day.at("21:36"))
def run():
    sign_.sign()

while True:
    run_pending()
    time.sleep(1)

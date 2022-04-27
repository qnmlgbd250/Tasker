# -*- coding: utf-8 -*-
# @Time    : 2022/4/27 17:11
# @Author  : huni
# @Email   : zcshiyonghao@163.com
# @File    : apitest.py
# @Software: PyCharm
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}
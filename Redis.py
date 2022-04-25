# -*- coding: utf-8 -*-
# @Time    : 2022/4/25 20:07
# @Author  : huni
# @Email   : zcshiyonghao@163.com
# @File    : Redis.py
# @Software: PyCharm
import os
from dotenv import load_dotenv

load_dotenv()
import redis


class RedisTool(object):
    def __init__(self):
        redis_host = os.getenv('REDIS_HOST')
        redis_port = os.getenv('REDIS_PORT')
        redis_password = os.getenv('REDIS_PASSWORD')
        redis_db = os.getenv('REDIS_DB')
        redis_pool = redis.ConnectionPool(host = redis_host, port = redis_port, password = redis_password,
                                          db = redis_db, decode_responses = True)
        self.redis_conn = redis.Redis(connection_pool = redis_pool)

    def redis_get(self, key: str):
        return self.redis_conn.get(key)

    def redis_set(self, key: str, value):
        return self.redis_conn.set(key, str(value))

    def redis_delete(self, key: str):
        return self.redis_conn.delete(key)

    def redis_exists(self, key: str):
        return self.redis_conn.exists(key)

    def redis_lpush(self, list_: str, value: str):
        return self.redis_conn.lpush(list_, value)

    def redis_rpush(self, list_: str, value: str):
        return self.redis_conn.rpush(list_, value)

    def redis_lpop(self, list_: list):
        return self.redis_conn.lpop(list_)

    def redis_rpop(self, list_: list):
        return self.redis_conn.rpop(list_)

    def redis_llen(self, list_: str):
        return self.redis_conn.llen(list_)

    def redis_str_to_list(self, key):
        return eval(self.redis_conn.get(key))


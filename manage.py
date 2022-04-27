# -*- coding: utf-8 -*-
# @Time    : 2022/4/26 22:36
# @Author  : huni
# @Email   : zcshiyonghao@163.com
# @File    : manage.py
# @Software: PyCharm

import click
import sign
import yun

@click.group()
def cli():
    pass

@click.command()
def autosign():
    """论坛自动签到"""
    sign.run()

@click.command()
def yundong():
    """自动刷步数"""
    yun.run()


cli.add_command(autosign, name = 'autosign')
cli.add_command(yundong, name = 'yundong')


if __name__ == '__main__':
    cli()
# -*- coding: utf-8 -*-
# @Time    : 2022/4/26 22:36
# @Author  : huni
# @Email   : zcshiyonghao@163.com
# @File    : manage.py
# @Software: PyCharm

import click
import task

@click.group()
def cli():
    pass

@click.command()
def taskstart():
    task.run()


cli.add_command(taskstart, name = 'taskstart')


if __name__ == '__main__':
    cli()
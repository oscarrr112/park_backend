# -*- coding: utf-8 -*-
# @Time    : 2019-12-30 03:24
# @Author  : 彭奥
# @Cooperation: LvMeng
# @Site    : 
# @File    : url.py
# @Software: PyCharm

from park_backend.settings import server_url, version, default_icon


def image_url(url):
    if url != '/media/media/icon/timg.jpeg':
        return server_url + url
    else:
        return server_url + '/' + default_icon


def sex_to_int(sex):
    return 1 if sex == '男' else 0


def int_to_sex(sex):
    return '男' if sex == 1 else '女'


def test_url(url):
    return version + url

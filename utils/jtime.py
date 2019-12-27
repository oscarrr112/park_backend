# -*- coding: utf-8 -*-
# @Time    : 2019-12-13 20:34
# @Author  : 彭奥
# @Cooperation: LvMeng
# @Site    : 
# @File    : utils_json.py
# @Software: PyCharm

import json
from datetime import date, datetime


class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, obj)

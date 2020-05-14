# -*- coding: utf-8 -*-
# @Time    : 2020-05-08 22:31
# @Author  : 彭奥
# @Site    :
# @File    : const.py
# @Software: PyCharm


class UserState:
    available = 0
    booked = 1
    not_payed = 2


class ParkLotState:
    hang_up = -1
    available = 0
    booked = 1
    used = 2


class OrderState:
    canceled = -1
    booked = 0
    not_payed = 1
    payed = 2

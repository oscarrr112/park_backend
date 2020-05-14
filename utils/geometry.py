# -*- coding: utf-8 -*-
# @Time    : 2019-12-14 00:36
# @Author  : 彭奥
# @Cooperation: LvMeng
# @Site    : 
# @File    : geometry.py
# @Software: PyCharm


from math import sin, asin, cos, radians, fabs, sqrt, degrees
import logging

logger = logging.getLogger(__file__)


EARTH_RADIUS = 6371  # 地球平均半径，6371km



def hav(theta):
    s = sin(theta / 2)
    return s * s


def get_distance_hav(lat0, lng0, lat1, lng1):
    # 用haversine公式计算球面两点间的距离。
    # 经纬度转换成弧度
    lat0 = radians(lat0)
    lat1 = radians(lat1)
    lng0 = radians(lng0)
    lng1 = radians(lng1)

    dlng = fabs(lng0 - lng1)
    dlat = fabs(lat0 - lat1)
    h = hav(dlat) + cos(lat0) * cos(lat1) * hav(dlng)
    distance = 2 * EARTH_RADIUS * asin(sqrt(h))

    return distance


def delta(lat, lng, distance):
    a = (sin(distance / (2 * EARTH_RADIUS)) / cos(lat))
    if a > 1.0:
        a = 0.99
    elif a < -1.0:
        a = -0.99
    dlng = 2 * asin(a)
    dlng = degrees(dlng)  # 弧度转换成角度

    dlat = distance / EARTH_RADIUS
    dlat = degrees(dlat)  # 弧度转换成角度

    return [lat + dlat, lat - dlat, lng - dlng, lng + dlng]


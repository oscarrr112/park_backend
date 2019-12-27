# -*- coding: utf-8 -*-
# @Time    : 2019-12-11 19:30
# @Author  : 彭奥
# @Cooperation: LvMeng
# @Site    : 
# @File    : version_1_0.py
# @Software: PyCharm

from django.urls import path, include

urlpatterns = [
    path('auth/', include('user.urls')),
    path('park-lot/', include('parking_lot.urls')),
    path('order/', include('order.urls'))
]

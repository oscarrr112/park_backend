# -*- coding: utf-8 -*-
# @Time    : 2019-12-13 20:28
# @Author  : 彭奥
# @Cooperation: LvMeng
# @Site    : 
# @File    : urls.py
# @Software: PyCharm

from django.urls import path
from parking_lot import views

urlpatterns = [
    path('new', views.NewView.as_view()),
    path('list', views.ListView.as_view()),
    path('userlist', views.UserList.as_view()),
    path('del', views.DelList.as_view()),
    path('odify', views.ModifyList.as_view()),
    path('getinfo', views.GetInfoView.as_view()),
    path('newpic', views.NewPicView.as_view()),
]

# -*- coding: utf-8 -*-
# @Time    : 2019-12-11 19:31
# @Author  : 彭奥
# @Cooperation: LvMeng
# @Site    : 
# @File    : urls.py
# @Software: PyCharm

from django.urls import path
from user import views

urlpatterns = [
    path('register', views.RegisterView.as_view()),
    path('login', views.AuthorizeView.as_view()),
    path('idcert', views.IDCertificationView.as_view()),
    path('usermanagement', views.UserManageView.as_view()),
    path('icon', views.IconView.as_view()),
    path('newicon', views.NewIconView.as_view()),
]

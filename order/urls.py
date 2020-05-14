# -*- coding: utf-8 -*-
# @Time    : 2019-12-16 23:05
# @Author  : 彭奥
# @Cooperation: LvMeng
# @Site    : 
# @File    : urls.py
# @Software: PyCharm


from django.urls import path

from order import views

urlpatterns = [
    path('new', views.NewList.as_view()),
    path('begin', views.BeginView.as_view()),
    path('end', views.EndView.as_view()),
    path('pay', views.PayView.as_view()),
    path('cancel', views.CancelView.as_view()),
    path('lessor', views.LessorListView.as_view()),
    path('tenant', views.TenantListView.as_view()),
    path('park-lot', views.ParkLotListView.as_view())
]

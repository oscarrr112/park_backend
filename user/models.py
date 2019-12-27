from django.db import models
from park_backend import settings

# Create your models here.


class User(models.Model):
    """
    用户表


    `petname` varchar(50) COLLATE greek_bin NOT NULL, 昵称
    `phonenum` varchar(11) COLLATE greek_bin NOT NULL, 电话号码
    `icon` binary(50) DEFAULT NULL, 头像
    `password` varchar(50) COLLATE greek_bin NOT NULL, 密码
    `name` varchar(50) COLLATE greek_bin NOT NULL, 姓名
    `ID` varchar(50) COLLATE greek_bin NOT NULL, 身份证号
    `sex` varchar(50) COLLATE greek_bin NOT NULL, 性别
    `bankcard` varchar(50) COLLATE greek_bin NOT NULL, 银行卡号
    state 用户交易状态 0 可自由交易 1 有订单正在进行 2 有订单尚未付款
    """
    nickname = models.CharField(max_length=50, default="")
    phone_number = models.CharField(max_length=11, primary_key=True)
    icon = models.ImageField(upload_to='icon', default=settings.default_icon)
    name = models.CharField(max_length=50, default="")
    password = models.CharField(max_length=50, default="")
    sex = models.IntegerField(default=0)
    bankcard = models.CharField(max_length=30, default="")
    ID = models.CharField(max_length=20, default="")
    state = models.IntegerField(default=0)

# -*- coding: utf-8 -*-
# @Time    : 2019-12-11 16:53
# @Author  : 彭奥
# @Cooperation: LvMeng
# @Site    : 
# @File    : auth.py
# @Software: PyCharm

from django.http import JsonResponse

from functools import wraps

from utils.respones import wrap_json_response, ReturnCode
from user.models import User


def id_cert_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        request = args[1]
        phone_number = request.session.get('phone_number')
        user = User.objects.get(phone_number=phone_number)
        id_number = user.ID
        if id_number is None:
            response = wrap_json_response(code=ReturnCode.NOT_ID_CERT)
            return JsonResponse(data=response, safe=False)
        return func(*args, **kwargs)

    return inner


def login_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        request = args[1]
        is_authorized = request.session.get('is_authorized')

        if not is_authorized:
            response = wrap_json_response(code=ReturnCode.UNAUTHORIZED)
            return JsonResponse(data=response, safe=False)
        return func(*args, **kwargs)

    return inner


def id_cert(name, id_number):
    return {
        'respCode': '0'
    }


def phone_cert(phone_number, captcha):
    data = {
        'result': '0',
    }

    return data


def bank_account_cert(credit_card_number, id_number, phone_number, name):
    return {
        'result': '0'
    }

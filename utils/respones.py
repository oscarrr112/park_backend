# -*- coding: utf-8 -*-
# @Time    : 2019-12-10 22:31
# @Author  : 彭奥
# @Cooperation: LvMeng
# @Site    : 
# @File    : respones.py
# @Software: PyCharm


class ReturnCode:

    # 公用状态码
    SUCCESS = 0
    FAILED = 100
    UNAUTHORIZED = 101
    BROKEN_PARAMS = 102
    NOT_ID_CERT = 103

    # 登陆状态码
    WRONG_PASSWORD = 201
    UNREGISTERED = 202

    # 实名验证状态码
    WRONG_NAME_FORM = 203
    WRONG_ID_FORM = 204
    MATCH_FAIL = 205
    NO_ID = 206

    # 手机绑定状态码
    WRONG_PHONE_NUMBER = 207
    WRONG_CAPTCHA = 208
    CAPTCHA_DUE = 209
    FREQUENTLY = 214

    # 银行卡绑定状态码
    WRONG_NAME = 210
    WRONG_ID_NUMBER = 211
    WRONG_CARD_NUMBER = 212
    NO_BANK_ACCOUNT = 213

    # 注册账号状态码
    PHONE_NUMBER_NOT_EXISTED = 215

    # 获取车位列表状态码
    BAD_INDEX = 301

    # 新建订单状态码
    BAD_TIME = 401
    PARK_LOT_OCCUPIED = 402
    ORDER_NOT_PAID = 403
    INVALID_PARK_LOT = 404

    # 取消订单状态码
    INVALID_ORDER_ID = 405
    CANCEL_FAILED = 406


messages = dict()

# 公用状态信息
messages[ReturnCode.SUCCESS] = "请求成功"
messages[ReturnCode.FAILED] = "请求失败"
messages[ReturnCode.UNAUTHORIZED] = "尚未登陆"
messages[ReturnCode.BROKEN_PARAMS] = "参数不全"
messages[ReturnCode.NOT_ID_CERT] = '尚未验证身份证'

# 登陆状态码
messages[ReturnCode.UNREGISTERED] = "手机号未注册"
messages[ReturnCode.WRONG_PASSWORD] = "密码错误"

# 实名验证状态信息
messages[ReturnCode.WRONG_NAME_FORM] = '开户名不能包含特殊字符'
messages[ReturnCode.WRONG_ID_FORM] = '身份证号格式错误'
messages[ReturnCode.MATCH_FAIL] = '身份证信息不匹配'
messages[ReturnCode.NO_ID] = '该身份证号码不存在'

# 手机绑定状态信息
messages[ReturnCode.WRONG_PHONE_NUMBER] = '手机号不正确'
messages[ReturnCode.WRONG_CAPTCHA] = '验证码错误'
messages[ReturnCode.CAPTCHA_DUE] = '验证码过期'
messages[ReturnCode.FREQUENTLY] = '频率过快'

# 银行卡认证状态信息
messages[ReturnCode.WRONG_NAME] = '姓名错误'
messages[ReturnCode.WRONG_ID_NUMBER] = '身份证号错误'
messages[ReturnCode.WRONG_CARD_NUMBER] = '银行卡号错误'
messages[ReturnCode.NO_BANK_ACCOUNT] = '无银行卡账号绑定'

# 注册状态信息
messages[ReturnCode.PHONE_NUMBER_NOT_EXISTED] = '手机号已存在'

# 获取车位列表状态信息
messages[ReturnCode.BAD_INDEX] = '索引越界'

# 新建订单状态信息
messages[ReturnCode.BAD_TIME] = '时间越界'
messages[ReturnCode.ORDER_NOT_PAID] = '尚有订单未支付'
messages[ReturnCode.PARK_LOT_OCCUPIED] = '车位已被预定或正在使用'
messages[ReturnCode.INVALID_PARK_LOT] = '车位号不正确'

# 取消订单状态信息
messages[ReturnCode.INVALID_ORDER_ID] = '订单号不正确'
messages[ReturnCode.CANCEL_FAILED] = '订单已被取消或完成'


class CommonResponseMixin(object):
    @classmethod
    def wrap_json_response(cls, data=None, code=None, message=None):
        response = wrap_json_response(data, code, message)
        return response


def wrap_json_response(data=None, code=None, message=None):
    response = {}
    if not code:
        code = ReturnCode.SUCCESS
    if not message:
        message = messages[code]

    response['data'] = data
    response['code'] = code
    response['message'] = message
    return response

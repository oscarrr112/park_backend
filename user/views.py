# Create your views here.

from django.views import View
from django.http import JsonResponse, FileResponse

import hashlib

from user.models import User
from park_backend import settings
import numpy as np

from utils.respones import CommonResponseMixin, ReturnCode
from utils import auth

import random
from django_redis import get_redis_connection

DUE = 900
INTERNAL = 60


class AuthorizeView(View, CommonResponseMixin):
    """
    用户认证相关视图
    """

    def post(self, request):
        """
        授权登陆表单，方法为POST
        :param request:
        :return:
        """

        request.session.delete()

        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')

        if not all([phone_number, password]):
            response = self.wrap_json_response(code=ReturnCode.BROKEN_PARAMS)
            return JsonResponse(data=response, safe=False)

        user = User.objects.get(phone_number=phone_number)

        if user is None:
            response = AuthorizeView.wrap_json_response(code=ReturnCode.UNREGISTERED)
            return JsonResponse(data=response, safe=False)
        elif user.password != password:
            response = AuthorizeView.wrap_json_response(code=ReturnCode.WRONG_PASSWORD)
            return JsonResponse(data=response, safe=False)
        else:
            request.session['phone_number'] = phone_number
            request.session['is_authorized'] = True
            response = {
                'phone_number': user.password,
                'petname': user.nickname,
                'name': user.name,
                'ID': user.ID,
                'sex': '男' if user.sex == 1 else '女',
                'bankcard': user.bankcard,
                'icon_url': user.icon.url if user.icon.url != '/media/' + settings.default_icon else settings.default_icon,
                'state': user.state,
            }

            print('/media/' + settings.default_icon)

            response = AuthorizeView.wrap_json_response(data=response)
            return JsonResponse(data=response, safe=False)


class PhoneCertificationView(View, CommonResponseMixin):

    def get(self, request):
        """
        获取短信验证码
        :param request: web请求，phone_number 用户手机号
        :return: JsonResponse data储存状态码，短信是否发送成功
        """
        # post_data = request.body.decode('utf-8')
        # post_data = json.loads(post_data)
        phone_number = request.GET.get('phone_number')
        sms_code = get_redis_connection('sms_code')
        redis_p = sms_code.pipeline()

        if phone_number is None:
            response = PhoneCertificationView.wrap_json_response(code=ReturnCode.BROKEN_PARAMS)
            return JsonResponse(data=response, safe=False)

        if sms_code.get(phone_number + '_flag') is not None:
            response = PhoneCertificationView.wrap_json_response(code=ReturnCode.FREQUENTLY)
            return JsonResponse(data=response, safe=False)

        captcha = str(random.randint(10000, 100000 - 1))

        redis_p.setex(phone_number, DUE, captcha)
        redis_p.setex(phone_number + '_flag', INTERNAL, 1)
        request.session['phone_number'] = phone_number
        redis_p.execute()

        data = auth.phone_cert(phone_number, captcha)
        if data['result'] == -119:
            response = PhoneCertificationView.wrap_json_response(code=ReturnCode.WRONG_PHONE_NUMBER)
            return JsonResponse(data=response, safe=False)

        response = PhoneCertificationView.wrap_json_response(data=captcha,
                                                             code=ReturnCode.SUCCESS)
        return JsonResponse(data=response, safe=False)

    def post(self, request):
        """
        验证码的验证
        :param request: web请求，captcha 用户填写的验证码
        :return:
        """
        # post_data = request.body.decode('utf-8')
        # post_data = json.loads(post_data)
        #
        # captcha_user = post_data.get('captcha')
        captcha_user = request.POST.get('captcha')
        sms_code = get_redis_connection('sms_code')

        if captcha_user is None:
            response = PhoneCertificationView.wrap_json_response(code=ReturnCode.BROKEN_PARAMS)
            return JsonResponse(data=response, safe=False)

        try:
            phone_number = request.session['phone_number']
        except KeyError:
            response = PhoneCertificationView.wrap_json_response(code=ReturnCode.CAPTCHA_DUE)
            return JsonResponse(data=response, safe=False)

        captcha_correct = sms_code.get(phone_number)

        if captcha_correct is None:
            response = PhoneCertificationView.wrap_json_response(code=ReturnCode.CAPTCHA_DUE)
            return JsonResponse(data=response, safe=False)

        captcha_correct = captcha_correct.decode()
        print("correct", captcha_correct)
        print("user", captcha_user)

        if captcha_correct == captcha_user:
            user = User(phone_number=phone_number)
            user.save()
            response = PhoneCertificationView.wrap_json_response(code=ReturnCode.SUCCESS)
            del request.session['phone_number']
            return JsonResponse(data=response, safe=False)
        else:
            response = PhoneCertificationView.wrap_json_response(code=ReturnCode.WRONG_CAPTCHA)
            return JsonResponse(data=response, safe=False)


class IDCertificationView(View, CommonResponseMixin):
    def post(self, request):

        """
        实名认证方法
        :param request: 传入的web请求，需传入两个参数，身份证号 id_number 和姓名 name
        :return: JsonResponse data储存状态码，表示是否认证成功
        """

        # post_data = request.body.decode('utf-8')
        # post_data = json.loads(post_data)
        phone_number = request.POST.get('phone_number')
        name = request.POST.get('name')
        id_num = request.POST.get('ID')

        if not all([phone_number, name, id_num]):
            response = IDCertificationView.wrap_json_response(code=ReturnCode.BROKEN_PARAMS)
            return JsonResponse(data=response, safe=False)

        data = auth.id_cert(name, id_num)
        errcode = data['respCode']

        if errcode == '0002':
            response = IDCertificationView.wrap_json_response(code=ReturnCode.WRONG_NAME_FORM)
            return JsonResponse(data=response, safe=False)
        elif errcode == '0004':
            response = IDCertificationView.wrap_json_response(code=ReturnCode.WRONG_ID_FORM)
            return JsonResponse(data=response, safe=False)
        elif errcode == '0007':
            response = IDCertificationView.wrap_json_response(code=ReturnCode.NO_ID)
            return JsonResponse(data=response, safe=False)
        elif errcode == '0008':
            response = IDCertificationView.wrap_json_response(code=ReturnCode.MATCH_FAIL)
            return JsonResponse(data=response, safe=False)
        elif errcode == '0010':
            response = IDCertificationView.wrap_json_response(code=ReturnCode.FAILED)
            return JsonResponse(data=response, safe=False)

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            response = self.wrap_json_response(code=ReturnCode.PHONE_NUMBER_NOT_EXISTED)
            return JsonResponse(data=response, safe=False)

        user.name = name
        user.ID = id_num
        user.save()

        response = IDCertificationView.wrap_json_response(code=ReturnCode.SUCCESS)
        return JsonResponse(data=response, safe=False)


class BankAccountView(View, CommonResponseMixin):

    @auth.login_required
    @auth.id_cert_required
    def post(self, request):
        """
        验证用户银行卡
        :param request:
        :return:
        """

        name = request.POST.get('name')
        id_num = request.POST.get('id')
        bankcard = request.POST.get('bankcard')
        phone_number = request.POST.get('phone_number')

        data = auth.bank_account_cert(bankcard, id_num, phone_number, name)
        code = data['status']
        if code == '202' or code == '203':
            response = BankAccountView.wrap_json_response(code=ReturnCode.FAILED)
            return JsonResponse(response, safe=False)
        elif code == '204':
            response = BankAccountView.wrap_json_response(code=ReturnCode.WRONG_NAME)
            return JsonResponse(response, safe=False)
        elif code == '205':
            response = BankAccountView.wrap_json_response(code=ReturnCode.WRONG_ID_NUMBER)
            return JsonResponse(response, safe=False)
        elif code == '206':
            response = BankAccountView.wrap_json_response(code=ReturnCode.WRONG_CARD_NUMBER)
            return JsonResponse(response, safe=False)
        elif code == '207':
            response = BankAccountView.wrap_json_response(code=ReturnCode.WRONG_PHONE_NUMBER)
            return JsonResponse(response, safe=False)
        else:
            phone_number = request.session.get('phone_number')
            user = User.objects.filter(phone_number=phone_number).first()
            user.bankcard = bankcard
            user.save()
            response = BankAccountView.wrap_json_response(code=ReturnCode.SUCCESS)
            return JsonResponse(data=response, safe=False)


class RegisterView(View, CommonResponseMixin):
    def post(self, request):

        nickname = request.POST.get('petname')
        phone_number = request.POST.get('phone_number')
        icon = request.FILES.get('icon')
        password = request.POST.get('password')
        sex = request.POST.get('sex')

        # if nickname is None or phone_number is None or password is None or sex is None:
        if not all([nickname, phone_number, password, sex]):
            response = RegisterView.wrap_json_response(code=ReturnCode.BROKEN_PARAMS)
            return JsonResponse(data=response, safe=False)

        user = User.objects.filter(phone_number=phone_number)
        if user.count() != 0:
            response = self.wrap_json_response(code=ReturnCode.PHONE_NUMBER_NOT_EXISTED)
            return JsonResponse(data=response, safe=False)

        user = User(phone_number=phone_number, password=password, nickname=nickname, sex=1 if sex == "男" else 0)
        if icon is not None:
            user.icon = icon

        user.save()

        response = RegisterView.wrap_json_response(code=ReturnCode.SUCCESS)
        return JsonResponse(data=response, safe=False)


class UserManageView(View, CommonResponseMixin):

    @auth.login_required
    def post(self, request):

        phone_number = request.session['phone_number']
        new_phone_number = request.POST.get('phone_number')
        nickname = request.POST.get('petname')
        icon = request.FILES.get('icon')
        password = request.POST.get('password')
        sex = request.POST.get('sex')

        if nickname is None and password is None and sex is None and phone_number is None:
            response = RegisterView.wrap_json_response(code=ReturnCode.BROKEN_PARAMS)
            return JsonResponse(data=response, safe=False)

        sex = 1 if sex == "男" else 0

        user = User.objects.filter(phone_number=phone_number).first()

        icon_md5 = hashlib.md5(np.array(icon))
        user_icon_md5 = hashlib.md5(np.array(user.icon))
        if user_icon_md5 != icon_md5 and user_icon_md5 != settings.default_md5:
            user.icon.storage.delete(user.icon.path)
            user.icon = icon
        elif user_icon_md5 == settings.default_md5:
            user.icon = icon

        user.password = password if password is not None else user.password
        user.sex = sex if sex is not None else user.sex
        user.nickname = nickname if nickname is not None else user.nickname
        user.phone_number = new_phone_number if phone_number is not None else user.phone_number
        user.save()

        response = RegisterView.wrap_json_response(code=ReturnCode.SUCCESS)
        return JsonResponse(data=response, safe=False)


class IconView(View):

    @auth.login_required
    def get(self, request):
        phone_number = request.session['phone_number']
        user = User.objects.filter(phone_number=phone_number).first()

        return FileResponse(user.icon)


class GetInfoView(View, CommonResponseMixin):

    @auth.login_required
    def get(self, request):
        phone_number = request.session.get('phone_number')

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            response = self.wrap_json_response(code=ReturnCode.PHONE_NUMBER_NOT_EXISTED)
            return JsonResponse(data=response, safe=False)

        response = {
            'phone_number': user.password,
            'petname': user.nickname,
            'name': user.name,
            'ID': user.ID,
            'sex': '男' if user.sex == 1 else '女',
            'bankcard': user.bankcard,
            'icon_url': user.icon.url if user.icon.url != '/media/' + settings.default_icon else settings.default_icon,
            'state': user.state,
        }

        response = AuthorizeView.wrap_json_response(data=response)
        return JsonResponse(data=response, safe=False)

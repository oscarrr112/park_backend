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

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            response = AuthorizeView.wrap_json_response(code=ReturnCode.UNREGISTERED)
            return JsonResponse(data=response, safe=False)

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

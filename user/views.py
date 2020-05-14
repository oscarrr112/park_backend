# Create your views here.

from django.views import View
from django.http import JsonResponse, FileResponse
import logging

import hashlib
import os

from user.models import User
from park_backend import settings
import numpy as np

from utils.respones import CommonResponseMixin, ReturnCode
from utils import auth
from utils.parse import image_url, sex_to_int, int_to_sex

DUE = 900
INTERNAL = 60

logger = logging.getLogger(os.path.abspath(__file__))


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

        # request.session.delete()

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
            # request.session['phone_number'] = phone_number
            response = {
                'phone_number': user.phone_number,
                'petname': user.nickname,
                'name': user.name,
                'ID': user.ID,
                'sex': int_to_sex(user.sex),
                'bankcard': user.bankcard,
                'icon_url': image_url(user.icon.url),
                'state': user.state,
            }

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
        password = request.POST.get('password')
        sex = request.POST.get('sex')
        icon = request.FILES.get('icon')

        # if nickname is None or phone_number is None or password is None or sex is None:
        if not all([nickname, phone_number, password, sex]):
            response = RegisterView.wrap_json_response(code=ReturnCode.BROKEN_PARAMS)
            return JsonResponse(data=response, safe=False)

        user = User.objects.filter(phone_number=phone_number).first()
        if user is not None:
            response = self.wrap_json_response(code=ReturnCode.PHONE_NUMBER_EXISTED)
            return JsonResponse(data=response, safe=False)

        user = User.objects.create(phone_number=phone_number, password=password, nickname=nickname, sex=sex_to_int(sex))
        if icon is not None:
            user.icon = icon
            user.save()
        user.save()

        data = {
            'image_url': image_url(user.icon.url)
        }

        response = RegisterView.wrap_json_response(code=ReturnCode.SUCCESS, data=data)
        return JsonResponse(data=response, safe=False)


class UserManageView(View, CommonResponseMixin):

    @auth.login_required
    def post(self, request):
        phone_number = request.POST.get('phone_number')
        nickname = request.POST.get('petname')
        password = request.POST.get('password')
        sex = request.POST.get('sex')
        icon = request.FILES.get('icon')
        if nickname is None and password is None and sex is None and phone_number is None:
            response = self.wrap_json_response(code=ReturnCode.BROKEN_PARAMS)
            return JsonResponse(data=response, safe=False)

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            response = self.wrap_json_response(code=ReturnCode.PHONE_NUMBER_NOT_EXISTED)
            return JsonResponse(data=response, safe=False)

        if icon is not None:
            icon_md5 = hashlib.md5(np.array(icon))
            user_icon_md5 = hashlib.md5(np.array(user.icon))
            if user_icon_md5 != icon_md5 and user_icon_md5 != settings.default_md5:
                user.icon.storage.delete(user.icon.path)
                user.icon = icon
            elif user_icon_md5 == settings.default_md5:
                user.icon = icon

            user.save()

        data = {
            'image_url': image_url(user.icon.url)
        }

        user.password = password if password is not None else user.password
        user.sex = sex_to_int(sex) if sex is not None else user.sex
        user.nickname = nickname if nickname is not None else user.nickname
        user.save()
        response = self.wrap_json_response(code=ReturnCode.SUCCESS, data=data)
        return JsonResponse(data=response, safe=False)


class IconView(View):

    @auth.login_required
    def get(self, request):
        phone_number = request.GET.get['phone_number']
        user = User.objects.filter(phone_number=phone_number).first()

        return FileResponse(user.icon)


class NewIconView(View, CommonResponseMixin):

    def post(self, request):
        icon = request.FILES.get('icon')
        phone_number = request.POST.get('phone_number')

        if not all([icon, phone_number]):
            response = self.wrap_json_response(code=ReturnCode.BROKEN_PARAMS)
            return JsonResponse(data=response, safe=False)
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            response = self.wrap_json_response(code=ReturnCode.PHONE_NUMBER_NOT_EXISTED)
            return JsonResponse(data=response, safe=False)

        if icon is not None:
            icon_md5 = hashlib.md5(np.array(icon))
            user_icon_md5 = hashlib.md5(np.array(user.icon))
            if user_icon_md5 != icon_md5 and user_icon_md5 != settings.default_md5:
                user.icon.storage.delete(user.icon.path)
                user.icon = icon
                user.save()
            elif user_icon_md5 == settings.default_md5:
                user.icon = icon
                user.save()
        data = {
            'image_url': image_url(user.icon.url)
        }

        response = self.wrap_json_response(code=ReturnCode.SUCCESS, data=data)
        return JsonResponse(data=response, safe=False)

# class LogoutView(View, CommonResponseMixin):
#
#     @auth.login_required
#     def post(self, request):
#         phone_number = request.POST.get('phone_number')
#
#         if phone_number is None:
#             response = self.wrap_json_response(code=ReturnCode.BROKEN_PARAMS)
#             return JsonResponse(data=response, safe=False)
#
#         # if phone_number != request.session.get('phone_number'):
#         #     response = self.wrap_json_response(code=ReturnCode.PHONE_NUMBER_NOT_THE_SAME)
#         #     return JsonResponse(data=response)
#
#         # del request.session['phone_number']
#         # del request.session['is_authorized']
#
#         response = self.wrap_json_response(code=ReturnCode.SUCCESS)
#         return JsonResponse(data=response, safe=False)

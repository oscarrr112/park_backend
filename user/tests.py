from django.test import TestCase

from rest_framework.test import APIRequestFactory
from user import views, models

from utils.respones import ReturnCode
from utils.parse import test_url, sex_to_int, int_to_sex, image_url

from PIL import Image
import json


# Create your tests here.


class RegisterTest(TestCase):

    def setUp(self) -> None:
        models.User.objects.create(phone_number='13975860352', nickname='oscar', password='011016', sex='1')
        self.url = test_url('/auth/register')

    def test_base_register(self):
        data = {
            'petname': 'Test',
            'phone_number': '13907486770',
            'password': '1',
            'sex': '男',
        }

        response = self.client.post(self.url, data=data)
        content = json.loads(response.content)
        self.assertEqual(content.get('code'), 0, '用户基础注册: 测试失败')

    def test_repeat_register(self):
        data = {
            'phone_number': '13975860352',
            'petname': 'oscar',
            'password': '011016',
            'sex': '1'
        }

        response = self.client.post(self.url, data=data)
        content = json.loads(response.content)
        self.assertEqual(content.get('code'), 217, '用户重复注册: 测试失败')


class LoginTest(TestCase):

    def setUp(self) -> None:
        self.user = models.User.objects.create(phone_number='13975860352', nickname='oscar', password='011016', sex=1)
        self.url = test_url('/auth/login')

    def test_base_login(self):
        data = {
            'phone_number': '13975860352',
            'password': '011016',
        }

        response = self.client.post(self.url, data=data)
        content = json.loads(response.content)
        self.assertEqual(content.get('code'), ReturnCode.SUCCESS, '用户基础登陆: 测试失败')
        data = content.get('data')
        self.assertEqual(data.get('phone_number'), self.user.phone_number, '用户基础登陆: 获取手机账号打败')
        self.assertEqual(data.get('petname'), self.user.nickname, '用户基础登陆: 获取昵称失败')
        self.assertEqual(data.get('name'), self.user.name, '用户基础登陆: 获取真实姓名失败')
        self.assertEqual(data.get('ID'), self.user.ID, '用户基础: 获取身份证号失败')
        self.assertEqual(sex_to_int(data.get('sex')), self.user.sex, '用户基础登陆: 获取性别失败')
        self.assertEqual(data.get('state'), self.user.state, '用户基础登陆: 获取当前状态失败')
        self.assertEqual(data.get('icon_url'), image_url(self.user.icon.url), '用户基础登陆: 当前头像获取失败')

    def test_invalid_password_login(self):
        data = {
            'phone_number': '13975860352',
            'password': '12',
        }

        response = self.client.post(self.url, data=data)
        content = json.loads(response.content)
        self.assertEqual(content.get('code'), ReturnCode.WRONG_PASSWORD, '用户密码错误登陆: 测试失败')

    def test_invalid_phone_number_login(self):
        data = {
            'phone_number': '17763638641',
            'password': '12',
        }

        response = self.client.post(self.url, data=data)
        content = json.loads(response.content)
        self.assertEqual(content.get('code'), ReturnCode.UNREGISTERED, '用户账号错误登陆: 测试失败')


class UserManageTest(TestCase):

    def setUp(self) -> None:
        self.user = models.User.objects.create(phone_number='13975860352', nickname='oscar', password='011016', sex='1')
        self.url = test_url('/auth/usermanagement')

    def test_base_user_manage(self):
        data = {
            'phone_number': '13975860352',
            'petname': 'oscarr112',
            'password': '1',
            'sex': '女',
        }

        response = self.client.post(self.url, data=data)
        content = json.loads(response.content)
        self.user = models.User.objects.get(phone_number=data['phone_number'])
        self.assertEqual(content.get('code'), ReturnCode.SUCCESS, '用户信息修改基础: 测试失败')
        self.assertEqual(data.get('phone_number'), self.user.phone_number, '用户信息修改基础: 修改手机账号打败')
        self.assertEqual(data.get('petname'), self.user.nickname, '用户信息修改基础: 修改昵称失败')
        self.assertEqual(sex_to_int(data.get('sex')), self.user.sex, '用户基础登陆: 获取性别失败')

    def test_broken_params_user_manage(self):
        data = {}

        response = self.client.post(self.url, data=data)
        content = json.loads(response.content)
        self.assertEqual(content.get('code'), ReturnCode.BROKEN_PARAMS, '用户信息修改空参数: 测试失败')

    def test_invalid_phone_number_user_manage(self):
        data = {
            'phone_number': '1',
            'petname': 'oscarr112',
            'password': '1',
            'sex': '女',
        }

        response = self.client.post(self.url, data=data)
        content = json.loads(response.content)
        self.assertEqual(content.get('code'), ReturnCode.PHONE_NUMBER_NOT_EXISTED, '用户账号错误信息修改: 测试失败')

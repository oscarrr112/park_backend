# UserListView 并没有进行单元测试

from django.test import TestCase

from user.models import User
from parking_lot.models import ParkLot, DescriptionPic

from utils.parse import image_url, test_url
from utils.respones import ReturnCode

from PIL import Image
import json
import random


# Create your tests here.


class NewParkLotTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(phone_number='13975860352', nickname='oscar', password='011016', sex='1')
        self.url = test_url('/park-lot/new')

    def test_new_park_lot_base(self):
        image1 = open('media/park_pic/prior.png', 'rb')
        image2 = open('media/park_pic/123468.png', 'rb')

        data = {
            'phone_number': self.user.phone_number,
            'longitude': 0,
            'latitude': 0,
            'detail_address': '无',
            'rent_date': '[{"datetime_start": "19:00", "datetime_end": "20:00", "frequency": [1, 2, 3]},' +
                         ' {"datetime_start": "10:00", "datetime_end": "20:00", "frequency": [5, 6, 7]}]',
            'price': 1,
            'rent_state': 0,
            'image1': image1,
            'image2': image2,
            'detail_word': '无',
        }
        response = self.client.post(self.url, data=data)
        content = json.loads(response.content)
        self.assertEqual(content.get('code'), ReturnCode.SUCCESS, '新建车位基础失败')

    def test_park_lot_broke_param(self):
        data = {
            'phone_number': self.user.phone_number,
            'longitude': 0,
            'latitude': 0,
            'detail_address': '无',
            'rent_date': '[{"datetime_start": "19:00", "datetime_end": "20:00", "frequency": [1, 2, 3]},' +
                         ' {"datetime_start": "10:00", "datetime_end": "20:00", "frequency": [5, 6, 7]}]',
            'price': 1,
            'rent_state': 0,
            'detail_word': '无',
        }

        response = self.client.post(self.url, data=data)
        response = json.loads(response.content)
        self.assertEqual(response.get('code'), ReturnCode.BROKEN_PARAMS, '新建车位参数不完整失败')


class ListTest(TestCase):

    def setUp(self) -> None:
        image1 = open('media/park_pic/prior.png', 'rb')
        image2 = open('media/park_pic/123468.png', 'rb')
        renter = User.objects.create(phone_number='17763638641', password='1', sex='1', nickname='oscar')

        for i in range(0, 20):
            longitude = random.uniform(0, 90)
            latitude = random.uniform(0, 180)
            price = random.uniform(0, 20)
            data = {
                'phone_number': renter.phone_number,
                'longitude': longitude,
                'latitude': latitude,
                'detail_address': '无',
                'rent_date': '[{"datetime_start": "19:00", "datetime_end": "20:00", "frequency": [1, 2, 3]},' +
                             ' {"datetime_start": "10:00", "datetime_end": "20:00", "frequency": [5, 6, 7]}]',
                'price': price,
                'rent_state': 0,
                'image1': image1,
                'image2': image2,
                'detail_word': '无',
            }
            self.client.post(test_url('/park-lot/new'), data=data)

        image1.close()
        image2.close()
        self.url = test_url('/park-lot/list')

    def test_list_base_mode_0_order_mode_1(self):
        longitude = random.uniform(0, 90)
        latitude = random.uniform(0, 180)

        data = {
            'latitude': latitude,
            'longitude': longitude,
            'mode': 0,
            'bindex': 0,
            'eindex': 9,
            'order_mode': 1
        }

        response = self.client.get(self.url, data=data)
        response = json.loads(response.content)
        self.assertEqual(response.get('code'), ReturnCode.SUCCESS, '获取列表距离优先降序: 状态码错误')
        print(data)
        self.assertEqual(sorted(response.get('data'), key=lambda x: x['distance']), response.get('data'),
                         '获取列表距离优先降序: 错误')

    def test_list_base_mode_0_order_mode_2(self):
        longitude = random.uniform(0, 90)
        latitude = random.uniform(0, 180)

        data = {
            'latitude': latitude,
            'longitude': longitude,
            'mode': 0,
            'bindex': 0,
            'eindex': 9,
            'order_mode': 2
        }

        response = self.client.get(self.url, data=data)
        response = json.loads(response.content)
        self.assertEqual(response.get('code'), ReturnCode.SUCCESS, '获取列表距离优先升序: 状态码错误')
        self.assertEqual(sorted(response.get('data'), key=lambda x: x['distance']), response.get('data'),
                         '获取列表距离优先升序: 错误')

    def test_list_base_mode_1_order_mode_1(self):
        longitude = random.uniform(0, 90)
        latitude = random.uniform(0, 180)

        data = {
            'latitude': latitude,
            'longitude': longitude,
            'mode': 1,
            'bindex': 0,
            'eindex': 9,
            'order_mode': 1
        }

        response = self.client.get(self.url, data=data)
        response = json.loads(response.content)
        self.assertEqual(response.get('code'), ReturnCode.SUCCESS, '获取列表距离优先降序: 状态码错误')
        self.assertEqual(sorted(response.get('data'), key=lambda x: x['price']), response.get('data'),
                         '获取列表距离优先降序: 错误')

    def test_list_base_mode_1_order_mode_2(self):
        longitude = random.uniform(0, 90)
        latitude = random.uniform(0, 180)

        data = {
            'latitude': latitude,
            'longitude': longitude,
            'mode': 1,
            'bindex': 0,
            'eindex': 9,
            'order_mode': 2
        }

        response = self.client.get(self.url, data=data)
        response = json.loads(response.content)
        self.assertEqual(response.get('code'), ReturnCode.SUCCESS, '获取列表距离优先升序: 状态码错误')
        self.assertEqual(sorted(response.get('data'), key=lambda x: x['price']), response.get('data'),
                         '获取列表距离优先升序: 错误')


class DelTest(TestCase):
    def setUp(self) -> None:
        renter = User.objects.create(phone_number='17763638641', password='1', sex='1', nickname='oscar')
        longitude = random.uniform(0, 90)
        latitude = random.uniform(0, 180)
        price = random.uniform(0, 20)
        image1 = open('media/park_pic/prior.png', 'rb')
        image2 = open('media/park_pic/123468.png', 'rb')
        data = {
            'phone_number': renter.phone_number,
            'longitude': longitude,
            'latitude': latitude,
            'detail_address': '无',
            'rent_date': '[{"datetime_start": "19:00", "datetime_end": "20:00", "frequency": [1, 2, 3]},' +
                         ' {"datetime_start": "10:00", "datetime_end": "20:00", "frequency": [5, 6, 7]}]',
            'price': price,
            'rent_state': 0,
            'image1': image1,
            'image2': image2,
            'detail_word': '无',
        }
        response = self.client.post(test_url('/park-lot/new'), data=data)
        self.test_data = json.loads(response.content).get('data')
        self.url = test_url('/park-lot/del')

    def test_del_base(self):
        data = self.test_data
        response = self.client.post(self.url, data=data)
        response = json.loads(response.content)
        self.assertEqual(response.get('code'), 0, '删除车位错误：状态码返回错误')
        self.assertEqual(ParkLot.objects.filter(park_lot_id=data.get('parking_lot_id')).count(), 0, '删除车位错误：车位未成功删除')

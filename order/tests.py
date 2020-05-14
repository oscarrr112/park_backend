from django.test import TestCase
import logging

from user.models import User
from order.models import Order
from parking_lot.models import ParkLot, DescriptionPic

from utils.parse import test_url
from utils.respones import ReturnCode
from utils.const import ParkLotState, UserState, OrderState

import json
from datetime import datetime

logger = logging.getLogger(__file__)


# Create your tests here.


class NewTest(TestCase):

    def setUp(self) -> None:
        self.url = test_url('/order/new')

        image1 = open('media/park_pic/prior.png', 'rb')

        # 测试样例中的租客
        self.tenant = User.objects.create(phone_number='17763638641', nickname='tenant', sex=1, password='011016')
        # 测试样例中的出租者
        self.lessor = User.objects.create(phone_number='13907486770', nickname='lessor', sex=1, password='011016')
        response = self.client.post(test_url('/park-lot/new'), data={
            'phone_number': self.tenant.phone_number,
            'longitude': 0,
            'latitude': 0,
            'detail_address': '无',
            'rent_date': '[{"datetime_start": "19:00", "datetime_end": "20:00", "frequency": [1, 2, 3]},' +
                         ' {"datetime_start": "10:00", "datetime_end": "20:00", "frequency": [5, 6, 7]}]',
            'price': 1,
            'rent_state': 0,
            'image1': image1,
            'detail_word': '无',
        })
        response = json.loads(response.content)
        # logger.info(response)
        self.park_lot = ParkLot.objects.get(park_lot_id=response.get('data').get('parking_lot_id'))

    def test_new_order_base(self):
        data = {
            'phone_number': self.tenant.phone_number,
            'time_start': '2019-12-30 19:01',
            'time_end': '2019-12-30 19:50',
            'park_lot': self.park_lot.park_lot_id
        }

        response = self.client.post(self.url, data=data)
        response = json.loads(response.content)
        self.assertEqual(response.get('code'), ReturnCode.SUCCESS, '新建订单基础测试: 测试失败')

    def test_new_order_broke_params(self):
        data = {
            'phone_number': self.tenant.phone_number,
            'time_start': '2019-12-30 19:01',
            'park_lot': self.park_lot.park_lot_id
        }

        response = self.client.post(self.url, data=data)
        response = json.loads(response.content)
        self.assertEqual(response.get('code'), ReturnCode.BROKEN_PARAMS, '新建订单参数不全测试: 测试失败')

    def test_new_order_time_out_params(self):
        data = {
            'phone_number': self.tenant.phone_number,
            'time_start': '2019-12-30 19:01',
            'time_end': '2019-12-30 20:20',
            'park_lot': self.park_lot.park_lot_id
        }

        response = self.client.post(self.url, data=data)
        response = json.loads(response.content)
        self.assertEqual(response.get('code'), ReturnCode.BAD_TIME, '新建订单时间越界测试: 测试失败')

    def test_new_order_park_lot_occupied(self):
        data = {
            'phone_number': self.tenant.phone_number,
            'time_start': '2019-12-30 19:01',
            'time_end': '2019-12-30 19:20',
            'park_lot': self.park_lot.park_lot_id
        }

        self.park_lot.rent_state = 2
        self.park_lot.save()
        response = self.client.post(self.url, data=data)
        response = json.loads(response.content)
        self.assertEqual(response.get('code'), ReturnCode.PARK_LOT_OCCUPIED, '新建订单车位被占用测试: 测试失败')

    def test_new_order_order_not_paid(self):
        data = {
            'phone_number': self.tenant.phone_number,
            'time_start': '2019-12-30 19:01',
            'time_end': '2019-12-30 19:50',
            'park_lot': self.park_lot.park_lot_id
        }

        Order.objects.create(lessor=self.lessor, tenant=self.tenant, state=1, park_lot=self.park_lot,
                             book_time_start=datetime.now(), book_time_end=datetime.now(), price=10)
        self.tenant.state = 3
        self.tenant.save()
        response = self.client.post(self.url, data=data)
        response = json.loads(response.content)
        self.assertEqual(response.get('code'), ReturnCode.ORDER_NOT_PAID, '新建订单订单尚未支付测试: 测试失败')

    def test_new_order_wrong_parklot(self):
        data = {
            'phone_number': self.tenant.phone_number,
            'time_start': '2019-12-30 19:01',
            'time_end': '2019-12-30 19:20',
            'park_lot': -1
        }

        self.park_lot.rent_state = 2
        self.park_lot.save()
        response = self.client.post(self.url, data=data)
        response = json.loads(response.content)
        self.assertEqual(response.get('code'), ReturnCode.INVALID_PARK_LOT, '新建订单车位被占用测试: 测试失败')


class CancelTest(TestCase):

    def setUp(self) -> None:
        image1 = open('media/park_pic/prior.png', 'rb')

        # 测试样例中的租客
        self.tenant = User.objects.create(phone_number='17763638641', nickname='tenant', sex=1, password='011016',
                                          state=1)
        # 测试样例中的出租者
        self.lessor = User.objects.create(phone_number='13907486770', nickname='lessor', sex=1, password='011016')
        response = self.client.post(test_url('/park-lot/new'), data={
            'phone_number': self.tenant.phone_number,
            'longitude': 0,
            'latitude': 0,
            'detail_address': '无',
            'rent_date': '[{"datetime_start": "19:00", "datetime_end": "20:00", "frequency": [1, 2, 3]},' +
                         ' {"datetime_start": "10:00", "datetime_end": "20:00", "frequency": [5, 6, 7]}]',
            'price': 1,
            'rent_state': 1,
            'image1': image1,
            'detail_word': '无',
        })
        response = json.loads(response.content)
        self.test_data = response
        # logger.info(response)
        self.test_data = response
        self.park_lot = ParkLot.objects.get(park_lot_id=response.get('data').get('parking_lot_id'))
        self.order = Order.objects.create(lessor=self.lessor, tenant=self.tenant, state=0, park_lot=self.park_lot,
                                          book_time_start=datetime.now(), book_time_end=datetime.now(), price=10)
        self.url = test_url('/order/cancel')

    def test_cancel_base(self):
        data = {
            'order_id': self.order.order_id
        }

        logger.info(self.tenant.state)
        response = self.client.get(self.url, data=data)
        response = json.loads(response.content)
        self.assertEqual(response.get('code'), ReturnCode.SUCCESS, '订单取消接口基础测试: 测试失败')

        park_lot = ParkLot.objects.get(park_lot_id=self.test_data.get('data').get('parking_lot_id'))
        order = Order.objects.get(order_id=data.get('order_id'))
        tenant = User.objects.get(phone_number='17763638641')
        self.assertEqual(order.state, OrderState.canceled, '订单取消接口基础测试: order.state 异常')
        self.assertEqual(tenant.state, UserState.available, '订单取消接口基础测试: tenant.state 异常')
        self.assertEqual(park_lot.rent_state, ParkLotState.available, '订单取消接口基础测试: park_lot.rent_state 异常')


class BeginTest(TestCase):

    def setUp(self) -> None:
        image1 = open('media/park_pic/prior.png', 'rb')

        # 测试样例中的租客
        self.tenant = User.objects.create(phone_number='17763638641', nickname='tenant', sex=1, password='011016',
                                          state=1)
        # 测试样例中的出租者
        self.lessor = User.objects.create(phone_number='13907486770', nickname='lessor', sex=1, password='011016',
                                          state=1)
        response = self.client.post(test_url('/park-lot/new'), data={
            'phone_number': self.tenant.phone_number,
            'longitude': 0,
            'latitude': 0,
            'detail_address': '无',
            'rent_date': '[{"datetime_start": "19:00", "datetime_end": "20:00", "frequency": [1, 2, 3]},' +
                         ' {"datetime_start": "10:00", "datetime_end": "20:00", "frequency": [5, 6, 7]}]',
            'price': 1,
            'rent_state': 0,
            'image1': image1,
            'detail_word': '无',
        })
        response = json.loads(response.content)
        self.test_data = response
        # logger.info(response)
        self.park_lot = ParkLot.objects.get(park_lot_id=response.get('data').get('parking_lot_id'))
        self.order = Order.objects.create(lessor=self.lessor, tenant=self.tenant, state=0, park_lot=self.park_lot,
                                          book_time_start=datetime.now(), book_time_end=datetime.now(), price=10)
        self.url = test_url('/order/cancel')

    def test_begin_base(self):
        data = {
            'order_id': self.order.order_id
        }

        logger.info(self.tenant.state)
        response = self.client.get(self.url, data=data)
        response = json.loads(response.content)
        self.assertEqual(response.get('code'), ReturnCode.SUCCESS, '订单取消接口基础测试: 测试失败')
        logger.info(self.order.state)
        tenant = User.objects.get(phone_number='17763638641')
        order = Order.objects.get(order_id=data.get('order_id'))
        park_lot = ParkLot.objects.get(park_lot_id=self.test_data.get('data').get('parking_lot_id'))
        self.assertEqual(order.state, OrderState.canceled, '订单开始接口基础测试: order.state 异常')
        self.assertEqual(tenant.state, UserState.available, '订单开始接口基础测试: tenant.state 异常')
        self.assertEqual(park_lot.rent_state, ParkLotState.available, '订单开始接口基础测试: park_lot.rent_state 异常')

from django.views import View
from django.http import JsonResponse
import logging

from utils.respones import ReturnCode, CommonResponseMixin
from utils import auth, uorder
from utils.parse import image_url
from utils.const import OrderState, ParkLotState, UserState

from order.models import Order
from parking_lot.models import ParkLot, DescriptionPic
from user.models import User

from datetime import datetime, timedelta
import json
from math import ceil

logger = logging.getLogger(__file__)


# Create your views here.


class NewList(View, CommonResponseMixin):

    @auth.login_required
    @auth.id_cert_required
    def post(self, request):
        time_start = request.POST.get('time_start')
        time_end = request.POST.get('time_end')
        park_lot = request.POST.get('park_lot')
        tenant = request.POST.get('phone_number')

        if not all([time_start, time_end, park_lot, tenant]):
            print('BROKEN_PARAMS')
            response = self.wrap_json_response(code=ReturnCode.BROKEN_PARAMS)
            return JsonResponse(data=response, safe=False)

        time_start = datetime.strptime(time_start, '%Y-%m-%d %H:%M')
        time_end = datetime.strptime(time_end, '%Y-%m-%d %H:%M')
        try:
            park_lot = ParkLot.objects.get(park_lot_id=park_lot)
        except ParkLot.DoesNotExist:
            print('INVALID_PARK_LOT')
            response = self.wrap_json_response(code=ReturnCode.INVALID_PARK_LOT)
            return JsonResponse(data=response, safe=False)

        lessor = park_lot.renter
        tenant = User.objects.get(phone_number=tenant)

        if tenant.state:
            data = {
                'order_id': Order.objects.get(tenant=tenant, state__in=[0, 1, 2]).order_id
            }
            print('ORDER_NOT_PAID')
            response = self.wrap_json_response(code=ReturnCode.ORDER_NOT_PAID, data=data)
            return JsonResponse(data=response, safe=False)

        if park_lot.rent_state:
            print('PARK_LOT_OCCUPIED')
            response = self.wrap_json_response(code=ReturnCode.PARK_LOT_OCCUPIED)
            return JsonResponse(data=response, safe=False)

        # 判断预定时间是否合法
        available_times = park_lot.rent_date
        available_times = json.loads(available_times)
        if isinstance(available_times, str):
            available_times = json.loads(available_times)

        available = False
        for available_time in available_times:
            # 可用的开始时间、结束时间、频率
            datetime_start = available_time['datetime_start'].split(':')
            datetime_start = datetime(time_start.year, time_start.month, time_start.day,
                                      int(datetime_start[0]), int(datetime_start[1]))
            datetime_end = available_time['datetime_end'].split(':')
            datetime_end = datetime(time_end.year, time_end.month, time_end.day,
                                    int(datetime_end[0]), int(datetime_end[1]))
            frequency = available_time['frequent']
            print(datetime_start, time_start)
            print(datetime_end, time_end)
            print(time_start.weekday(), frequency)

            if time_start.weekday() + 1 in frequency and datetime_start <= time_start and time_end <= datetime_end:
                available = True
                break

        if not available:
            print('BAD_TIME')
            response = self.wrap_json_response(code=ReturnCode.BAD_TIME)
            return JsonResponse(data=response, safe=False)

        # 新建Order记录
        Order.objects.create(book_time_start=time_start, book_time_end=time_end, price=park_lot.price,
                             park_lot=park_lot, tenant=tenant, lessor=lessor)
        park_lot.rent_state = ParkLotState.booked
        tenant.state = UserState.booked
        print(tenant.phone_number, tenant.state)
        response = self.wrap_json_response(code=ReturnCode.SUCCESS)
        print('SUCCESS')
        park_lot.save()
        tenant.save()

        return JsonResponse(data=response, safe=False)


class BeginView(View, CommonResponseMixin):

    @auth.login_required
    @auth.id_cert_required
    def get(self, request):
        order_id = request.GET.get('order_id')
        uorder.unlock()

        order = Order.objects.get(order_id=order_id)

        if order is None or order.state != 0:
            response = self.wrap_json_response(code=ReturnCode.INVALID_ORDER_ID)
            return JsonResponse(data=response, safe=False)

        order.state = OrderState.going

        park_lot = ParkLot.objects.get(park_lot_id=order.park_lot.park_lot_id)
        park_lot.rent_state = ParkLotState.used
        order.time_start = datetime.now()
        response = self.wrap_json_response(data={
            'time_start': order.time_start.strftime('%Y-%m-%d %H:%M')
        }, code=ReturnCode.SUCCESS)
        order.save()
        park_lot.save()

        return JsonResponse(data=response, safe=False)


class EndView(View, CommonResponseMixin):
    @auth.login_required
    @auth.id_cert_required
    def get(self, request):
        order_id = request.GET.get('order_id')
        uorder.lock()

        order = Order.objects.get(order_id=order_id)

        if order is None or order.state != OrderState.going:
            response = self.wrap_json_response(code=ReturnCode.INVALID_ORDER_ID)
            return JsonResponse(data=response, safe=False)

        order.state = OrderState.not_payed
        order.time_end = datetime.now()
        time_start = order.time_start
        time_end = order.time_end
        delta_time = time_end - time_start
        order.tot_price = order.price * delta_time.seconds / (60 * 60)

        tenant = User.objects.get(phone_number=order.tenant.phone_number)
        tenant.state = UserState.not_payed

        park_lot = ParkLot.objects.get(park_lot_id=order.park_lot.park_lot_id)
        park_lot.rent_state = 0
        data = {
            'time_start': order.time_start.strftime('%Y-%m-%d %H:%M'),
            'time_end': order.time_end.strftime('%Y-%m-%d %H:%M'),
            'tot_price': order.tot_price
        }
        response = self.wrap_json_response(data=data,
                                           code=ReturnCode.SUCCESS)
        order.save()
        tenant.save()
        park_lot.save()

        return JsonResponse(data=response, safe=False)


class PayView(View, CommonResponseMixin):
    @auth.login_required
    @auth.id_cert_required
    def get(self, request):
        order_id = request.GET.get('order_id')
        uorder.pay()

        order = Order.objects.get(order_id=order_id)

        if order is None or abs(order.state) != 2:
            response = self.wrap_json_response(code=ReturnCode.INVALID_ORDER_ID)
            return JsonResponse(data=response, safe=False)

        order.state = OrderState.canceled if order.state == OrderState.canceled_not_pay else OrderState.payed

        tenant = order.tenant
        tenant.state = UserState.available
        data = {
            'tot_price': order.tot_price,
            'time_start': order.time_start,
            'time_end': order.time_end
        }
        response = self.wrap_json_response(code=ReturnCode.SUCCESS, data=data)
        tenant.save()
        order.save()
        return JsonResponse(data=response, safe=False)


class CancelView(View, CommonResponseMixin):

    @auth.login_required
    @auth.id_cert_required
    def get(self, request):
        order = request.GET.get('order_id')

        if order is None:
            response = self.wrap_json_response(code=ReturnCode.BROKEN_PARAMS)
            return JsonResponse(data=response, safe=False)

        try:
            order = Order.objects.get(order_id=order)
        except Order.DoesNotExist:
            response = self.wrap_json_response(code=ReturnCode.INVALID_ORDER_ID)
            return JsonResponse(data=response, safe=False)

        if order.state != 0:
            response = self.wrap_json_response(code=ReturnCode.CANCEL_FAILED)
            return JsonResponse(data=response, safe=False)

        tenant = User.objects.get(phone_number=order.tenant.phone_number)

        time_end = datetime.now()
        time_start = order.book_time_start - timedelta(hours=1)
        if time_end <= time_start:
            tenant.state = UserState.available
            order.state = OrderState.canceled
            park_lot = ParkLot.objects.get(park_lot_id=order.park_lot.park_lot_id)
            park_lot.rent_state = ParkLotState.available
            order.tot_price = 0
            order.time_end = time_end

            tenant.save()
            order.save()
            park_lot.save()
        else:
            order.state = OrderState.canceled_not_pay
            park_lot = ParkLot.objects.get(park_lot_id=order.park_lot.park_lot_id)
            park_lot.rent_state = ParkLotState.available
            tenant.state = UserState.not_payed
            order.time_end = time_end

            time_start = order.book_time_start
            time_end = order.book_time_end
            delta_time = time_end - time_start
            order.tot_price = order.price * delta_time.seconds / (60 * 60)

            tenant.save()
            order.save()
            park_lot.save()

        response = self.wrap_json_response(code=ReturnCode.SUCCESS)
        return JsonResponse(data=response, safe=False)


class LessorListView(View, CommonResponseMixin):
    @auth.login_required
    @auth.id_cert_required
    def get(self, request):
        try:
            phone_number = request.GET.get('phone_number')
            mode = int(request.GET.get('mode'))
        except TypeError:
            response = self.wrap_json_response(code=ReturnCode.BROKEN_PARAMS)
            return JsonResponse(data=response, safe=False)

        if phone_number is None or mode is None:
            response = self.wrap_json_response(code=ReturnCode.BROKEN_PARAMS)
            return JsonResponse(data=response, safe=False)

        try:
            tenant = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            response = self.wrap_json_response(code=ReturnCode.WRONG_PHONE_NUMBER)
            return JsonResponse(data=response, safe=False)

        if mode == 4:
            orders = Order.objects.filter(tenant=tenant)
        elif mode != 2:
            orders = Order.objects.filter(tenant=tenant, state=mode)
        else:
            orders = Order.objects.filter(tenant=tenant, state=mode) | Order.objects.filter(tenant=tenant, state=-mode)

        response = []
        for order in orders:
            pics = DescriptionPic.objects.filter(park_lot=order.park_lot)
            data = {
                'order_id': order.order_id,
                'time_start': order.time_start.strftime('%Y-%m-%d %H:%M') if order.time_start is not None else None,
                'time_end': order.time_end.strftime('%Y-%m-%d %H:%M') if order.time_end is not None else None,
                'book_time_start': order.book_time_start.strftime('%Y-%m-%d %H:%M'),
                'book_time_end': order.book_time_end.strftime('%Y-%m-%d %H:%M'),
                'price': order.price,
                'lessor': order.lessor_id,
                'lessor_nickname': order.lessor.nickname,
                'tenant': order.tenant_id,
                'tenant_nickname': order.tenant.nickname,
                'park_lot': order.park_lot_id,
                'state': abs(order.state) if order.state == OrderState.canceled_not_pay else order.state,
                'tot_price': order.tot_price,
                'photo_urls': [image_url(pic.pic.url) for pic in pics],
                'detail_address': order.park_lot.detail_address
            }
            response.append(data)

        response = self.wrap_json_response(data=response, code=ReturnCode.SUCCESS)
        return JsonResponse(data=response, safe=False)


class TenantListView(View, CommonResponseMixin):
    @auth.login_required
    @auth.id_cert_required
    def get(self, request):
        order_id = request.GET.get('order_id')

        if order_id is None:
            response = self.wrap_json_response(code=ReturnCode.INVALID_ORDER_ID)
            return JsonResponse(data=response, safe=False)

        try:
            order = Order.objects.get(order_id=order_id)
        except Order.DoesNotExist:
            response = self.wrap_json_response(code=ReturnCode.INVALID_ORDER_ID)
            return JsonResponse(data=response, safe=False)

        pics = DescriptionPic.objects.filter(park_lot=order.park_lot)
        data = {
            'order_id': order.order_id,
            'time_start': order.time_start.strftime('%Y-%m-%d %H:%M') if order.time_start is not None else None,
            'time_end': order.time_end.strftime('%Y-%m-%d %H:%M') if order.time_end is not None else None,
            'book_time_start': order.book_time_start.strftime('%Y-%m-%d %H:%M'),
            'book_time_end': order.book_time_end.strftime('%Y-%m-%d %H:%M'),
            'price': order.price,
            'lessor': order.lessor_id,
            'lessor_nickname': order.lessor.nickname,
            'tenant': order.tenant_id,
            'tenant_nickname': order.tenant.nickname,
            'park_lot': order.park_lot_id,
            'state': abs(order.state) if order.state == OrderState.canceled_not_pay else order.state,
            'photo_urls': [image_url(pic.pic.url) for pic in pics],
            'tot_price': order.tot_price
        }

        response = self.wrap_json_response(data=data, code=ReturnCode.SUCCESS)
        return JsonResponse(data=response, safe=False)


class ParkLotListView(View, CommonResponseMixin):
    @auth.login_required
    @auth.id_cert_required
    def get(self, request):
        park_lot = request.GET.get('park_lot_id')
        orders = Order.objects.filter(park_lot_id=park_lot)
        pics = DescriptionPic.objects.filter(park_lot_id=park_lot)

        response = []
        for order in orders:
            data = {
                'order_id': order.order_id,
                'time_start': order.time_start.strftime('%Y-%m-%d %H:%M') if order.time_start is not None else None,
                'time_end': order.time_end.strftime('%Y-%m-%d %H:%M') if order.time_end is not None else None,
                'book_time_start': order.book_time_start.strftime('%Y-%m-%d %H:%M'),
                'book_time_end': order.book_time_end.strftime('%Y-%m-%d %H:%M'),
                'price': order.price,
                'lessor': order.lessor_id,
                'lessor_nickname': order.lessor.nickname,
                'tenant': order.tenant_id,
                'tenant_nickname': order.tenant.nickname,
                'park_lot': order.park_lot_id,
                'state': abs(order.state) if order.state == OrderState.canceled_not_pay else order.state,
                'image_url': [image_url(pic.pic.url) for pic in pics],
                'tot_price': order.tot_price
            }
            response.append(data)

        response = self.wrap_json_response(data=response, code=ReturnCode.SUCCESS)
        return JsonResponse(data=response, safe=False)

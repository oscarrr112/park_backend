from django.views import View
from django.http import JsonResponse

from utils.respones import ReturnCode, CommonResponseMixin
from utils import auth, uorder

from order.models import Order
from parking_lot.models import ParkLot, DescriptionPic
from user.models import User

from datetime import datetime, timedelta
import json


# Create your views here.


class NewList(View, CommonResponseMixin):

    @auth.login_required
    @auth.id_cert_required
    def post(self, request):
        time_start = request.POST.get('time_start')
        time_end = request.POST.get('time_end')
        park_lot = request.POST.get('park_lot_id')
        lessor = request.session['phone_number']

        if not all([time_start, time_end, park_lot]):
            response = self.wrap_json_response(code=ReturnCode.BROKEN_PARAMS)
            return JsonResponse(data=response, safe=False)

        time_start = datetime.strptime(time_start, '%Y-%m-%d %H:%M')
        time_end = datetime.strptime(time_end, '%Y-%m-%d %H:%M')
        park_lot = ParkLot.objects.get(park_lot_id=park_lot)
        tenant = park_lot.renter
        lessor = User.objects.get(phone_number=lessor)

        if park_lot is None:
            response = self.wrap_json_response(code=ReturnCode.INVALID_PARK_LOT)
            return JsonResponse(data=response, safe=False)

        if tenant.state:
            data = {
                'order_id': Order.objects.get(tenant=tenant, state__in=[0, 1, 2]).order_id
            }
            response = self.wrap_json_response(code=ReturnCode.ORDER_NOT_PAID, data=data)
            return JsonResponse(data=response, safe=False)

        if park_lot.rent_state:
            response = self.wrap_json_response(code=ReturnCode.PARK_LOT_OCCUPIED)
            return JsonResponse(data=response, safe=False)

        # 判断预定时间是否合法
        available_times = park_lot.rent_date
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
            frequency = available_time['frequency']
            if time_start.weekday() + 1 in frequency and datetime_start <= time_start and time_end <= datetime_end:
                print(available_time)
                available = True
                break

        if not available:
            response = self.wrap_json_response(code=ReturnCode.BAD_TIME)
            return JsonResponse(data=response, safe=False)

        # 新建Order记录
        order = Order(book_time_start=time_start, book_time_end=time_end, price=park_lot.price,
                      park_lot=park_lot, tenant=tenant, lessor=lessor)
        order.save()
        park_lot.rent_state = 1
        park_lot.save()
        tenant.state = 1
        tenant.save()
        response = self.wrap_json_response(code=ReturnCode.SUCCESS)
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

        order.state = 1
        order.time_start = datetime.now()
        order.save()
        park_lot = order.park_lot
        park_lot.state = 2
        park_lot.save()
        response = self.wrap_json_response(data=order.time_start.strftime('%Y-%m-%d %H:%M'),
                                           code=ReturnCode.SUCCESS)
        return JsonResponse(data=response, safe=False)


class EndView(View, CommonResponseMixin):
    @auth.login_required
    @auth.id_cert_required
    def get(self, request):
        order_id = request.GET.get('order_id')
        uorder.lock()

        order = Order.objects.get(order_id=order_id)

        if order is None or order.state != 1:
            response = self.wrap_json_response(code=ReturnCode.INVALID_ORDER_ID)
            return JsonResponse(data=response, safe=False)

        order.state = 2
        order.time_end = datetime.now()
        order.save()
        tenant = order.tenant
        tenant.state = 2
        tenant.save()
        park_lot = order.park_lot
        park_lot.state = 0
        park_lot.save()
        response = self.wrap_json_response(data=order.time_end.strftime('%Y-%m-%d %H:%M'),
                                           code=ReturnCode.SUCCESS)
        return JsonResponse(data=response, safe=False)


class PayView(View, CommonResponseMixin):
    @auth.login_required
    @auth.id_cert_required
    def get(self, request):
        order_id = request.GET.get('order_id')
        uorder.pay()

        order = Order.objects.get(order_id=order_id)

        if order is None or order.state != 2:
            response = self.wrap_json_response(code=ReturnCode.INVALID_ORDER_ID)
            return JsonResponse(data=response, safe=False)

        order.state = 3
        order.time_end = datetime.now()
        time_start = order.time_start
        time_end = order.time_end
        delta_time = time_end - time_start

        order.tot_price = order.price * delta_time.seconds / (60 * 60)
        order.save()
        tenant = order.tenant
        tenant.state = 0
        tenant.save()
        response = self.wrap_json_response(ReturnCode.SUCCESS)
        return JsonResponse(data=response, safe=False)


class CancelView(View, CommonResponseMixin):

    @auth.login_required
    @auth.id_cert_required
    def get(self, request):
        phone_number = request.session.get('phone_number')
        order = request.GET.get('order_id')

        if order is None:
            response = self.wrap_json_response(code=ReturnCode.BROKEN_PARAMS)
            return JsonResponse(data=response, safe=False)

        order = Order.objects.get(order_id=order)

        if order is None:
            response = self.wrap_json_response(code=ReturnCode.INVALID_ORDER_ID)
            return JsonResponse(data=response, safe=False)

        if order.state != 0:
            response = self.wrap_json_response(code=ReturnCode.CANCEL_FAILED)
            return JsonResponse(data=response, safe=False)
        tenant = User.objects.get(phone_number=phone_number)
        tenant.state = 0
        tenant.save()
        order.state = -1
        order.save()
        park_lot = order.park_lot
        park_lot.state = 0
        park_lot.save()

        response = self.wrap_json_response(code=ReturnCode.SUCCESS)
        return JsonResponse(data=response, safe=False)


class LessorListView(View, CommonResponseMixin):
    @auth.login_required
    @auth.id_cert_required
    def get(self, request):
        phone_number = request.GET.get('phone_number')
        mode = request.GET.get('mode')

        if not all([phone_number, mode]):
            response = self.wrap_json_response(code=ReturnCode.BROKEN_PARAMS)
            return JsonResponse(data=response, safe=False)

        if mode == 4:
            orders = Order.objects.filter(lessor_id=phone_number)
        else:
            orders = Order.objects.filter(lessor_id=phone_number, state=mode)

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
                'state': order.state,
                'tot_price': order.tot_price
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
            'state': order.state,
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
                'state': order.state,
                'image_url': [pic.pic.url for pic in pics],
                'tot_price': order.tot_price
            }
            response.append(data)

        response = self.wrap_json_response(data=response, code=ReturnCode.SUCCESS)
        return JsonResponse(data=response, safe=False)

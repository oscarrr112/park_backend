from django.http import JsonResponse, FileResponse
from django.views import View

from parking_lot.models import ParkLot, DescriptionPic
from user.models import User

from utils.respones import CommonResponseMixin, ReturnCode
from utils import auth, geometry

import json


# Create your views here.


class NewView(View, CommonResponseMixin):

    @auth.login_required
    @auth.id_cert_required
    def post(self, request):
        longitude = request.POST.get('longitude')
        latitude = request.POST.get('latitude')
        detail_address = request.POST.get('detail_address')
        rent_date = request.POST.get('rent_date')
        rent_state = request.POST.get('rent_state')
        remark = request.POST.get('remark')
        price = request.POST.get('price')

        renter_id = request.session.get('phone_number')

        rent_date = json.dumps(rent_date)
        if not all([longitude, latitude, detail_address, rent_date, price, rent_state]):
            response = NewView.wrap_json_response(code=ReturnCode.BROKEN_PARAMS)
            return JsonResponse(data=response, safe=False)

        park_lot = ParkLot(renter=User.objects.filter(phone_number=renter_id).first(), longitude=longitude,
                           latitude=latitude, detail_address=detail_address,
                           rent_date=rent_date, rent_state=rent_state,
                           remark=remark, price=price)
        park_lot.save()

        response = NewView.wrap_json_response(code=ReturnCode.SUCCESS, data={
            'parking_lot_id': park_lot.park_lot_id
        })
        return JsonResponse(data=response, safe=False)


class NewPicView(View, CommonResponseMixin):

    @auth.login_required
    @auth.id_cert_required
    def post(self, request):
        park_lot_id = request.POST.get('parking_lot_id')
        pics = request.FILES

        if not all([park_lot_id, pics]):
            response = self.wrap_json_response(code=ReturnCode.BROKEN_PARAMS)
            return JsonResponse(data=response, safe=False)

        try:
            park_lot = ParkLot.objects.get(park_lot_id=park_lot_id)
        except ParkLot.DoesNotExist:
            response = self.wrap_json_response(code=ReturnCode.INVALID_PARK_LOT)
            return JsonResponse(data=response, safe=False)

        des_pics = DescriptionPic.objects.filter(park_lot=park_lot)
        for pic in des_pics:
            pic.delete()

        for key, value in pics.items():
            pic = DescriptionPic(pic=value, park_lot=park_lot)
            pic.save()

        response = self.wrap_json_response(code=ReturnCode.SUCCESS)
        return JsonResponse(data=response, safe=False)


class ListView(View, CommonResponseMixin):

    def get(self, request):

        distance = 5000

        try:
            latitude = float(request.GET.get('latitude'))
            longitude = float(request.GET.get('longitude'))
            mode = int(request.GET.get('mode'))
            order_mode = int(request.GET.get('order_mode'))
            bindex = int(request.GET.get('bindex'))
            eindex = int(request.GET.get('eindex'))
        except TypeError:
            response = self.wrap_json_response(code=ReturnCode.BROKEN_PARAMS)
            return JsonResponse(data=response, safe=False)

        max_latitude, min_latitude, min_longitude, max_longitude = geometry.delta(latitude, longitude, distance)
        park_lots = ParkLot.objects.filter(latitude__gte=min_latitude, latitude__lte=max_latitude,
                                           longitude__gte=min_longitude, longitude__lte=max_longitude)

        if mode == 1:
            park_lots = park_lots.order_by('price')
            response = []
            for park_lot in park_lots:
                description_pics = DescriptionPic.objects.filter(park_lot=park_lot)
                response.append({
                    'park_lot_id': park_lot.park_lot_id,
                    'renter': park_lot.renter.phone_number,
                    'renter_nickname': park_lot.renter.nickname,
                    'longitude': park_lot.longitude,
                    'latitude': park_lot.latitude,
                    'detail_address': park_lot.detail_address,
                    'rent_date': json.loads(park_lot.rent_date),
                    'price': park_lot.price,
                    'detail_word': park_lot.detail_word,
                    'rent_state': park_lot.rent_state,
                    'remark': park_lot.remark,
                    'distance': geometry.get_distance_hav(park_lot.latitude, park_lot.longitude, latitude, longitude),
                    'photo_url': ['http://114.55.255.62:8000' + pic.pic.url for pic in description_pics],
                })

            if order_mode == 2:
                response.reverse()
            response = ListView.wrap_json_response(data=response, code=ReturnCode.SUCCESS)
            return JsonResponse(data=response, safe=False)
        else:

            if bindex < 0 or bindex >= ParkLot.objects.count() or bindex > eindex:
                response = ListView.wrap_json_response(code=ReturnCode.BAD_INDEX)
                return JsonResponse(data=response, safe=False)

            eindex = eindex if eindex < ParkLot.objects.count() else ParkLot.objects.count() - 1

            tmp = 1
            while park_lots.count() < eindex:
                max_latitude, min_latitude, min_longitude, max_longitude \
                    = geometry.delta(latitude, longitude, distance * tmp)
                park_lots = ParkLot.objects.filter(latitude__gte=min_latitude, latitude__lte=max_latitude,
                                                   longitude__gte=min_longitude, longitude__lte=max_longitude)

            response = []
            for park_lot in park_lots:
                description_pics = DescriptionPic.objects.filter(park_lot=park_lot)
                data = {
                    'park_lot_id': park_lot.park_lot_id,
                    'renter': park_lot.renter.phone_number,
                    'renter_nickname': park_lot.renter.nickname,
                    'longitude': park_lot.longitude,
                    'latitude': park_lot.latitude,
                    'detail_address': park_lot.detail_address,
                    'rent_date': json.loads(park_lot.rent_date),
                    'price': park_lot.price,
                    'detail_word': park_lot.detail_word,
                    'rent_state': park_lot.rent_state,
                    'remark': park_lot.remark,
                    'distance': geometry.get_distance_hav(park_lot.latitude, park_lot.longitude, latitude, longitude),
                    'photo_url': ['http://114.55.255.62:8000' + pic.pic.url for pic in description_pics],
                    'nickname': park_lot.renter.nickname,
                }
                response.append(data)

            sorted(response, key=lambda x: x['distance'])
            response = response[bindex: eindex + 1]
            if order_mode == 2:
                response.reverse()
            response = ListView.wrap_json_response(data=response, code=ReturnCode.SUCCESS)
            return JsonResponse(data=response, safe=False)


class UserList(View, CommonResponseMixin):

    @auth.login_required
    @auth.id_cert_required
    def get(self, request):
        phone_number = request.GET.get('phone_number')

        if phone_number is None:
            response = UserList.wrap_json_response(code=ReturnCode.BROKEN_PARAMS)
            return JsonResponse(data=response, safe=False)

        user = User.objects.get(phone_number=phone_number)
        park_lots = ParkLot.objects.filter(renter=user)

        response = []
        for park_lot in park_lots:
            description_pics = DescriptionPic.objects.filter(park_lot=park_lot)
            data = {
                'park_lot_id': park_lot.park_lot_id,
                'detail_address': park_lot.detail_address,
                'rent_state': park_lot.rent_state,
                'photo_url': ['http://114.55.255.62:8000' + pic.pic.url for pic in description_pics],
            }
            response.append(data)

        response = UserList.wrap_json_response(data=response, code=ReturnCode.SUCCESS)
        return JsonResponse(data=response, safe=False)


class DelList(View, CommonResponseMixin):

    @auth.login_required
    @auth.id_cert_required
    def get(self, request):
        parking_lot_id = request.GET.get('parking_lot_id')

        if parking_lot_id is None:
            response = self.wrap_json_response(code=ReturnCode.BROKEN_PARAMS)
            return JsonResponse(data=response, safe=False)

        parking_lot = ParkLot.objects.get(park_lot_id=parking_lot_id)

        if parking_lot is None:
            response = self.wrap_json_response(code=ReturnCode.INVALID_PARK_LOT)
            return JsonResponse(data=response, safe=False)
        parking_lot.delete()

        response = self.wrap_json_response(code=ReturnCode.SUCCESS)
        return JsonResponse(data=response)


class ModifyList(View, CommonResponseMixin):
    @auth.login_required
    @auth.id_cert_required
    def post(self, request):
        parking_lot_id = request.POST.get('parking_lot_id')
        rent_date = request.POST.get('rent_date')
        description_tag = request.POST.get('description_tag')
        rent_state = request.POST.get('rent_state')
        remark = request.POST.get('remark')
        price = request.POST.get('price')

        if parking_lot_id is None:
            response = self.wrap_json_response(code=ReturnCode.BROKEN_PARAMS)
            return JsonResponse(data=response, safe=False)
        elif rent_date is None and description_tag is None and rent_state is None and remark is None and price is None:
            response = self.wrap_json_response(code=ReturnCode.BROKEN_PARAMS)
            return JsonResponse(data=response, safe=False)

        try:
            park_lot = ParkLot.objects.get(park_lot_id=parking_lot_id)
        except ParkLot.DoesNotExist:
            response = self.wrap_json_response(code=ReturnCode.INVALID_PARK_LOT)
            return JsonResponse(data=response, safe=False)

        if park_lot is None:
            response = self.wrap_json_response(code=ReturnCode.INVALID_PARK_LOT)
            return JsonResponse(data=response, safe=False)

        park_lot.rent_date = rent_date if rent_date is not None else park_lot.rent_date
        park_lot.description_tag = description_tag if description_tag is not None else park_lot.description_tag
        park_lot.rent_state = rent_state if park_lot.rent_state is not None else park_lot.rent_state
        park_lot.remark = remark if park_lot.remark is not None else park_lot.remark
        park_lot.price = price if park_lot.price is not None else park_lot.pricey

        response = NewView.wrap_json_response(code=ReturnCode.SUCCESS)
        return JsonResponse(data=response, safe=False)


class GetInfoView(View, CommonResponseMixin):

    def get(self, request):
        parking_lot_id = request.GET.get('parking_lot_id')

        if parking_lot_id is None:
            response = self.wrap_json_response(code=ReturnCode.BROKEN_PARAMS)
            return JsonResponse(data=response, safe=False)

        try:
            park_lot = ParkLot.objects.get(park_lot_id=parking_lot_id)
        except ParkLot.DoesNotExist:
            response = self.wrap_json_response(code=ReturnCode.INVALID_PARK_LOT)
            return JsonResponse(data=response)

        """
        park_lot_id         车位唯一id 主键
        renter_id           出租人手机号码
        longitude           车库经度
        latitude            车库纬度
        detail_address      详细地址
        rent_date           出租日期
        price               出租价格
        detail_word         详细描述
        rent_state          出租状态            -1:暂停出租，0:空闲中，1:预约中，2:出租中
        remark              备注
        """

        description_pics = DescriptionPic.objects.filter(park_lot=park_lot)
        data = {
            'parking_lot_id': park_lot.park_lot_id,
            'renter_id': park_lot.renter_id,
            'renter_name': park_lot.renter.nickname,
            'longitude': park_lot.longitude,
            'latitude': park_lot.latitude,
            'detail_address': park_lot.detail_address,
            'rent_date': json.loads(park_lot.rent_date),
            'price': park_lot.price,
            'remark': park_lot.remark,
            'detail_word': park_lot.detail_word,
            'photo_url': ['http://114.55.255.62:8000' + pic.pic.url for pic in description_pics],
            'rent_state': park_lot.rent_state
        }

        response = self.wrap_json_response(code=ReturnCode.SUCCESS, data=data)
        return JsonResponse(data=response, safe=False)

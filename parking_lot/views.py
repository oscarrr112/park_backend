from django.http import JsonResponse, FileResponse
from django.views import View

from parking_lot.models import ParkLot, DescriptionPic
from user.models import User

from utils.respones import CommonResponseMixin, ReturnCode
from utils import auth, geometry


# Create your views here.


class NewView(View, CommonResponseMixin):

    @auth.login_required
    @auth.id_cert_required
    def post(self, request):
        longitude = request.POST.get('longitude')
        latitude = request.POST.get('latitude')
        detail_address = request.POST.get('detail_address')
        rent_date = request.POST.get('rent_date')
        photos = request.FILES
        rent_state = request.POST.get('rent_state')
        remark = request.POST.get('remark')
        price = request.POST.get('price')

        renter_id = request.session.get('phone_number')

        if not all([longitude, latitude, detail_address, rent_date, price, photos, rent_state]):
            response = NewView.wrap_json_response(code=ReturnCode.BROKEN_PARAMS)
            return JsonResponse(data=response, safe=False)

        park_lot = ParkLot(renter=User.objects.filter(phone_number=renter_id).first(), longitude=longitude,
                           latitude=latitude, detail_address=detail_address,
                           rent_date=rent_date, description_tag=description_tag, rent_state=rent_state,
                           remark=remark, price=price)
        park_lot.save()

        for photo_name in photos:
            photo_db = DescriptionPic(pic=request.FILES.get(photo_name), park_lot=park_lot)
            photo_db.save()

        response = NewView.wrap_json_response(code=ReturnCode.SUCCESS)
        return JsonResponse(data=response, safe=False)


class ListView(View, CommonResponseMixin):

    @auth.login_required
    @auth.id_cert_required
    def get(self, request):

        distance = 5000

        latitude = float(request.GET.get('latitude'))
        longitude = float(request.GET.get('longitude'))
        mode = request.GET.get('mode')
        order_mode = request.GET.get('order_mode')
        bindex = int(request.GET.get('bindex'))
        eindex = int(request.GET.get('eindex'))

        if not all([latitude, longitude, mode]) and (
                mode == 0 and not all([bindex, eindex])) or mode == 1 or order_mode is None:
            response = ListView.wrap_json_response(code=ReturnCode.BROKEN_PARAMS)
            return JsonResponse(data=response, safe=False)

        if bindex < 0 or eindex >= ParkLot.objects.count():
            response = ListView.wrap_json_response(code=ReturnCode.BAD_INDEX)
            return JsonResponse(data=response, safe=False)

        max_latitude, min_latitude, min_longitude, max_longitude = geometry.delta(latitude, longitude, distance)
        park_lots = ParkLot.objects.filter(latitude__gte=min_latitude, latitude__lte=max_latitude,
                                           longitude__gte=min_longitude, longitude__lte=max_longitude)

        if mode == 1:
            park_lots.order_by('price')

            response = []
            for park_lot in park_lots:
                response += {
                    'park_lot_id': park_lot.park_lot_id,
                    'renter': park_lot.renter.phone_number,
                    'renter_nickname': park_lot.renter.nickname,
                    'longitude': park_lot.longitude,
                    'latitude': park_lot.latitude,
                    'detail_address': park_lot.detail_address,
                    'rent_date': park_lot.rent_date,
                    'price': park_lot.price,
                    'detail_word': park_lot.detail_word,
                    'rent_state': park_lot.rent_state,
                    'remark': park_lot.remark,
                    'distance': geometry.get_distance_hav(park_lot.latitude, park_lot.longitude, latitude, longitude)
                }
                if order_mode == 2:
                    response = reversed(response)
            response = ListView.wrap_json_response(data=response, code=ReturnCode.SUCCESS)
            return JsonResponse(data=response, safe=False)
        else:
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
                    'rent_date': park_lot.rent_date,
                    'price': park_lot.price,
                    'detail_word': park_lot.detail_word,
                    'rent_state': park_lot.rent_state,
                    'remark': park_lot.remark,
                    'distance': geometry.get_distance_hav(park_lot.latitude, park_lot.longitude, latitude, longitude),
                    'photo_url': [pic.pic.url for pic in description_pics],
                    'nickname': park_lot.renter.nickname,
                    'icon': park_lot.renter.icon
                }
                response.append(data)

            sorted(response, key=lambda x: x['distance'])
            response = response[bindex: eindex + 1]
            if order_mode == 2:
                reversed(response)
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
                'photo_url': [pic.pic.url for pic in description_pics]
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
        photos = request.FILES
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

        if photos is not None:
            photo_descriptions = DescriptionPic.objects.filter(park_lot_id=parking_lot_id)
            for photo in photo_descriptions:
                photo.delete()

            for photo_name in photos:
                photo_db = DescriptionPic(pic=request.FILES.get(photo_name), park_lot=park_lot)
                photo_db.save()

        park_lot.rent_date = rent_date if rent_date is not None else park_lot.rent_date
        park_lot.description_tag = description_tag if description_tag is not None else park_lot.description_tag
        park_lot.rent_state = rent_state if park_lot.rent_state is not None else park_lot.rent_state
        park_lot.remark = remark if park_lot.remark is not None else park_lot.remark
        park_lot.price = price if park_lot.price is not None else park_lot.pricey

        response = NewView.wrap_json_response(code=ReturnCode.SUCCESS)
        return JsonResponse(data=response, safe=False)

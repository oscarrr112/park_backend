from django.db import models

from user.models import User
from parking_lot.models import ParkLot
# Create your models here.


class Order(models.Model):
    """
    state: 订单状态 -1:已取消 0:预约中 1:进行中 2:未支付 3:已支付
    """
    order_id = models.AutoField(primary_key=True)
    time_start = models.DateTimeField(blank=True, null=True)
    time_end = models.DateTimeField(blank=True, null=True)
    book_time_start = models.DateTimeField()
    book_time_end = models.DateTimeField()
    price = models.FloatField()
    state = models.IntegerField(default=0)
    lessor = models.ForeignKey(User,  on_delete=models.CASCADE, related_name='lessor')
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenant')
    park_lot = models.ForeignKey(ParkLot, on_delete=models.CASCADE)
    tot_price = models.FloatField(blank=True, null=True)

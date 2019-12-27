from django.db import models

from user.models import User
# Create your models here.


class ParkLot(models.Model):
    """
    park_lot_id         车位唯一id 主键
    renter_id           出租人手机号码
    longitude           车库经度
    latitude            车库纬度
    detail_address      详细地址
    rent_date           出租日期
    price               出租价格
    description_tag     描述标签
    detail_word         详细描述
    rent_state          出租状态            -1:暂停出租，0:空闲中，1:预约中，2:出租中
    remark              备注
    """
    park_lot_id = models.AutoField(primary_key=True)
    renter = models.ForeignKey(User, on_delete=models.CASCADE, default='')
    detail_address = models.TextField(default='')
    rent_date = models.TextField(default='')
    price = models.FloatField(default=0)
    description_tag = models.TextField(default='')
    detail_word = models.TextField(default='')
    rent_state = models.IntegerField(default=0)
    remark = models.TextField(default='')
    longitude = models.FloatField(default=0, db_index=True)
    latitude = models.FloatField(default=0, db_index=True)


class DescriptionPic(models.Model):
    """
    pic_id 图片id
    pic 图片
    park_lot 对应的车位
    """
    pic_id = models.IntegerField(primary_key=True)
    pic = models.ImageField(upload_to='park_pic')
    park_lot = models.ForeignKey(ParkLot, on_delete=models.CASCADE)

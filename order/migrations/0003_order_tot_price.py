# Generated by Django 3.0 on 2019-12-28 06:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0002_auto_20191217_1631'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='tot_price',
            field=models.FloatField(blank=True, null=True),
        ),
    ]

# Generated by Django 3.2 on 2022-02-07 07:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0054_orderitem_available_restaurants'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='restaurant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to='foodcartapp.restaurant', verbose_name='Ресторан, который готовит заказ'),
        ),
    ]

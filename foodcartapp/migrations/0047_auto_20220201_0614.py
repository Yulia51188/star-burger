# Generated by Django 3.2 on 2022-02-01 06:14

from django.db import migrations, models
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0046_alter_orderitem_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='phonenumber',
            field=phonenumber_field.modelfields.PhoneNumberField(db_index=True, max_length=128, region=None, verbose_name='Номер телефона'),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('not_processed', 'Не обработан'), ('processed', 'Обработан'), ('done', 'Завершен')], db_index=True, default='not_processed', max_length=14, verbose_name='Статус заказа'),
        ),
    ]

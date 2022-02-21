from collections import defaultdict

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Sum
from phonenumber_field.modelfields import PhoneNumberField


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        'Order',
        verbose_name='Заказ',
        related_name='order_items',
        on_delete=models.CASCADE,
        db_index=True,
    )
    product = models.ForeignKey(
        'Product',
        verbose_name='Товар',
        on_delete=models.CASCADE,
        related_name='order_items'
    )
    quantity = models.PositiveIntegerField(
        'Количество',
        validators=[MinValueValidator(1)],
    )

    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=True,
    )

    class Meta:
        verbose_name = 'товар в заказе'
        verbose_name_plural = 'товары в заказах'

    def __str__(self):
        return f'{self.product.name} х {self.quantity} в заказе {self.order.id} по цене  {self.price}'


class OrderQuerySet(models.QuerySet):
    def calculate_total_cost(self):
        return self.annotate(
            total_cost=Sum(F('order_items__price') * F('order_items__quantity')))

    def join_restaurants(self):
        """WARNING: evaluate queryset."""
        for order in self:
            order_items = order.order_items.all()
            product_amount = len(order_items)
            restaurants = defaultdict(int)
            for order_item in order_items:
                for menu_item in order_item.product.menu_items.all():
                    restaurants[menu_item.restaurant] += 1
            order.available_restaurants = [
                restaurant
                for restaurant, count in restaurants.items()
                if count == product_amount
            ]
        return self


class Order(models.Model):

    class OrderStatus(models.TextChoices):
        NOT_PROCESSED = 'not_processed', 'Не обработан'
        PROCESSED = 'processed', 'Обработан'
        DONE = 'done', 'Завершен'

    class PaymentMethod(models.TextChoices):
        CASH = 'cash', 'Наличными при получении'
        CARD_ONLINE = 'card_online', 'Банковской картой на сайте'

    firstname = models.CharField('Имя', max_length=100)
    lastname = models.CharField('Фамилия', max_length=100)
    address = models.CharField('Адрес', max_length=200)
    phonenumber = PhoneNumberField('Номер телефона', db_index=True)
    status = models.CharField(
        'Статус заказа',
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.NOT_PROCESSED,
        db_index=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Время создания заказа',
        db_index=True
    )
    called_at = models.DateTimeField(
        verbose_name='Звонок менеджера',
        db_index=True,
        blank=True,
        null=True,
    )
    delivered_at = models.DateTimeField(
        verbose_name='Доставлено',
        db_index=True,
        blank=True,
        null=True,
    )
    payment_method = models.CharField(
        'Способ оплаты',
        max_length=50,
        choices=PaymentMethod.choices,
        db_index=True,
    )
    comment = models.TextField('Комментарий к заказу', blank=True)

    restaurant = models.ForeignKey(
        Restaurant,
        verbose_name='Ресторан, который готовит заказ',
        related_name='orders',
        db_index=True,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def __str__(self):
        return f'Заказ №{self.id}'

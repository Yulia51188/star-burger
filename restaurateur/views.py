from operator import itemgetter

from django import forms
from django.db.models import Prefetch
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from foodcartapp.models import (Order, OrderItem, Product, Restaurant,
                                RestaurantMenuItem)
from geocoder.geocoder_functions import (calculate_distance,
                                         fetch_coordinates_by_addresses)


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    default_availability = {restaurant.id: False for restaurant in restaurants}
    products_with_restaurants = []
    for product in products:

        availability = {
            **default_availability,
            **{item.restaurant_id: item.availability for item in product.menu_items.all()},
        }
        orderer_availability = [availability[restaurant.id] for restaurant in restaurants]

        products_with_restaurants.append(
            (product, orderer_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurants': products_with_restaurants,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


class OrderItemsSerializer(ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price']


class RestaurantSerializer(ModelSerializer):

    class Meta:
        model = Restaurant
        fields = [
            'name',
            'contact_phone',
            'address',
        ]


def get_distance(obj):
    return obj.get('distance') or float('inf')


class OrderSerializer(ModelSerializer):
    order_items = OrderItemsSerializer(many=True, allow_empty=False)
    total_cost = serializers.DecimalField(max_digits=8, decimal_places=2)
    status = serializers.CharField(source='get_status_display')
    payment_type = serializers.CharField(source='get_payment_method_display')
    available_restaurants = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id',
            'firstname',
            'lastname',
            'phonenumber',
            'address',
            'order_items',
            'total_cost',
            'status',
            'payment_type',
            'available_restaurants'
        ]
        read_only_fields = ('id', 'total_cost')

    def get_available_restaurants(self, obj):
        restaurants = [
            RestaurantSerializer(restaurant).data
            for restaurant in obj.available_restaurants
        ]
        return restaurants


def get_coordinates(orders):
    orders_address = [order['address'] for order in orders]
    restaurants_address = [
        restaurant.address for restaurant in Restaurant.objects.all()
    ]
    coordinates = fetch_coordinates_by_addresses(
        [*restaurants_address, *orders_address],
        settings.GEOCODER_TOKEN
    )
    return coordinates


def join_distances(orders):
    coordinates = get_coordinates(orders)
    for order in orders:
        for restaurant in order['available_restaurants']:
            restaurant['distance'] = calculate_distance(
                coordinates.get(order['address']),
                coordinates.get(restaurant['address']),
            )

        sorted_restaurants = sorted(
            order['available_restaurants'],
            key=get_distance
        )
        order['available_restaurants'] = sorted_restaurants
    return orders


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    menu_item_qs = (
        RestaurantMenuItem.objects
        .filter(availability=True)
        .select_related('restaurant')
    )
    orders = (
        Order.objects
        .exclude(status=Order.OrderStatus.DONE)
        .prefetch_related(
            Prefetch('order_items__product__menu_items', queryset=menu_item_qs)
        )
        .calculate_total_cost()
        .join_restaurants()
    )

    serialized_orders = OrderSerializer(orders, many=True)
    orders_with_distances = join_distances(serialized_orders.data)

    return render(request, template_name='order_items.html', context={
        'orders': sorted(orders_with_distances, key=itemgetter('id'))
    })

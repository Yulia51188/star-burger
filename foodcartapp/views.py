import json

from django.http import JsonResponse
from django.templatetags.static import static
from django.db import transaction
from django.shortcuts import get_object_or_404
from phonenumber_field.phonenumber import PhoneNumber


from .models import Product
from .models import Order
from .models import OrderItem


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            },
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@transaction.atomic
def register_order(request):
    try:
        order_details = json.loads(request.body.decode())
        print(order_details)
        order = Order.objects.create(
            first_name=order_details['firstname'],
            last_name=order_details['lastname'],
            address=order_details['address'],
            phone=PhoneNumber.from_string(
                phone_number=order_details['phonenumber'],
                region='RU'
            ).as_e164,
        )

        for product in order_details['products']:
            product_entry = get_object_or_404(Product, id=product['product'])
            OrderItem.objects.create(
                order=order,
                product=product_entry,
                quantity=product['quantity'],
                price=product_entry.price,
            )

        order.total_cost = order.items.calc_total_cost()
        order.save()

        return JsonResponse(order_details, safe=False, json_dumps_params={
            'ensure_ascii': False,
            'indent': 4,
        })
    except ValueError:
        return JsonResponse({
            'error': 'bla bla bla',
        })

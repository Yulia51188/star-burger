from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.templatetags.static import static
from phonenumber_field.phonenumber import PhoneNumber
import phonenumbers
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Order, OrderItem, Product


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
@api_view(['POST'])
def register_order(request):
    order_details = request.data

    is_valid_post_data, error_details = validate_post_data(order_details)
    if not is_valid_post_data:
        return Response(error_details, status=status.HTTP_400_BAD_REQUEST)

    order = Order.objects.create(
        first_name=order_details['firstname'],
        last_name=order_details['lastname'],
        address=order_details['address'],
        phone=PhoneNumber.from_string(
            phone_number=order_details['phonenumber'], region='RU').as_e164,
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

    return Response(order_details)


def validate_post_data(order_details):
    firstname = order_details.get('firstname')
    if not firstname:
        return False, {
            "type": "ValueError",
            "data_filed": "firstname",
            "message": "firstname field value is empty or skipped",
        }
    if not isinstance(firstname, str):
        return False, {
            "type": "TypeError",
            "data_filed": "firstname",
            "message": "firstname field value is not a string",
        }

    lastname = order_details.get('lastname')
    if not lastname:
        return False, {
            "type": "ValueError",
            "data_filed": "lastname",
            "message": "lastname field value is empty or skipped",
        }
    if not isinstance(lastname, str):
        return False, {
            "type": "TypeError",
            "data_filed": "lastname",
            "message": "lastname field value is not a string",
        }

    address = order_details.get('lastname')
    if not address:
        return False, {
            "type": "ValueError",
            "data_filed": "address",
            "message": "address field value is empty or skipped",
        }
    if not isinstance(address, str):
        return False, {
            "type": "TypeError",
            "data_filed": "address",
            "message": "address field value is not a string",
        }

    phonenumber = order_details.get('phonenumber')
    if not phonenumber:
        return False, {
            "type": "ValueError",
            "data_filed": "phonenumber",
            "message": "phonenumber field value is empty or skipped",
        }
    if not isinstance(phonenumber, str):
        return False, {
            "type": "TypeError",
            "data_filed": "phonenumber",
            "message": "phonenumber field value is not a string",
        }
    try:
        parsed_phone = phonenumbers.parse(phonenumber, "RU")
        is_valid = phonenumbers.is_valid_number(parsed_phone)
        is_possible = phonenumbers.is_possible_number(parsed_phone)
        if not is_valid or not is_possible:
            return False, {
                "type": "ValueError",
                "data_filed": "phonenumber",
                "message": "phonenumber field value is invalid for RU region",
            }
    except phonenumbers.phonenumberutil.NumberParseException as error:
        return False, {
            "type": "ValueError",
            "data_filed": "phonenumber",
            "message": f"phonenumber field value is invalid: {error}",
        }

    products = order_details.get('products')
    if not products:
        return False, {
            "type": "ValueError",
            "data_filed": "products",
            "message": "products field value is null or skipped",
        }
    if not isinstance(products, list):
        return False, {
            "type": "TypeError",
            "data_filed": "products",
            "message": "products field value is not a list",
        }
    if not any(products):
        return False, {
            "type": "ValueError",
            "data_filed": "products",
            "message": "products list is empty",
        }
    return True, None

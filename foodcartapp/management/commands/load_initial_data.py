import json
import os

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from foodcartapp.models import (Product, ProductCategory, Restaurant,
                                RestaurantMenuItem)


def upload_photo(photo_path, product):
    with open(photo_path, 'rb') as photo_obj:
        photo = photo_obj.read()

    product.image.save(
        os.path.basename(photo_path),
        ContentFile(photo),
        save=True
    )


def load_products(file_path, images_folder):
    with open(file_path, 'r') as file_obj:
        products = json.load(file_obj)
    for product in products:
        category, _ = ProductCategory.objects.get_or_create(name=product['type'])
        new_product, _ = Product.objects.get_or_create(
            name=product['title'],
            defaults={
                'category': category,
                'price': product['price'],
                'description': product['description']
            }
        )
        upload_photo(os.path.join(images_folder, product['img']), new_product)


def load_restaurants(file_path, set_all_available):
    with open(file_path, 'r') as file_obj:
        restaurants = json.load(file_obj)
    for restaurant in restaurants:
        Restaurant.objects.get_or_create(
            name=restaurant['title'],
            address=restaurant['address'],
            contact_phone=restaurant['contact_phone']

        )

    if set_all_available:
        products = Product.objects.all()
        for restaurant in Restaurant.objects.all():
            for product in products:
                RestaurantMenuItem.objects.get_or_create(
                    product=product,
                    restaurant=restaurant,
                    defaults={
                        'availability': True,
                    }
                )


class Command(BaseCommand):
    help = 'Load initial menu and restaurants to database'

    def add_arguments(self, parser):
        parser.add_argument('--products_path', type=str,
            default='test_data/products.json')
        parser.add_argument('--restaurants_path', type=str,
            default='test_data/restaurants.json')
        parser.add_argument('--images_folder', type=str,
            default='test_data/')
        parser.add_argument('-set', '--set_products_available', action='store_true')

    def handle(self, *args, **options):
        load_products(options['products_path'], options['images_folder'])
        load_restaurants(options['restaurants_path'], options['set_products_available'])

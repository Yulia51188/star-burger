
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import reverse
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Order, OrderItem, Product, Restaurant, RestaurantMenuItem


class RestaurantMenuItemInline(admin.TabularInline):
    model = RestaurantMenuItem
    extra = 0


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    search_fields = [
        'name',
        'address',
        'contact_phone',
    ]
    list_display = [
        'name',
        'address',
        'contact_phone',
    ]
    inlines = [
        RestaurantMenuItemInline
    ]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'get_image_list_preview',
        'name',
        'category',
        'price',
    ]
    list_display_links = [
        'name',
    ]
    list_filter = [
        'category',
    ]
    search_fields = [
        # FIXME SQLite can not convert letter case for cyrillic words properly, so search will be buggy.
        # Migration to PostgreSQL is necessary
        'name',
        'category__name',
    ]

    inlines = [
        RestaurantMenuItemInline
    ]
    fieldsets = (
        ('Общее', {
            'fields': [
                'name',
                'category',
                'image',
                'get_image_preview',
                'price',
            ]
        }),
        ('Подробно', {
            'fields': [
                'special_status',
                'description',
            ],
            'classes': [
                'wide'
            ],
        }),
    )

    readonly_fields = [
        'get_image_preview',
    ]

    class Media:
        css = {
            "all": (
                static("admin/foodcartapp.css")
            )
        }

    def get_image_preview(self, obj):
        if not obj.image:
            return 'выберите картинку'
        return format_html('<img src="{url}" style="max-height: 200px;"/>', url=obj.image.url)
    get_image_preview.short_description = 'превью'

    def get_image_list_preview(self, obj):
        if not obj.image or not obj.id:
            return 'нет картинки'
        edit_url = reverse('admin:foodcartapp_product_change', args=(obj.id,))
        return format_html('<a href="{edit_url}"><img src="{src}" style="max-height: 50px;"/></a>', edit_url=edit_url, src=obj.image.url)
    get_image_list_preview.short_description = 'превью'


class OrderItemInline(admin.TabularInline):
    model = OrderItem


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_cost', 'firstname', 'lastname', 'status',
                    'called_at', 'delivered_at', 'payment_method')
    readonly_fields = ('created_at',)
    list_filter = ('status', 'called_at', 'delivered_at')
    inlines = [
        OrderItemInline,
    ]

    def response_change(self, request, obj):
        if 'next' in request.GET:
            next_url = request.GET['next']
            if url_has_allowed_host_and_scheme(next_url, None):
                return HttpResponseRedirect(next_url)
        return super().response_change(request, obj)

    def order_cost(self, obj):
        return f"{obj.total_cost} руб."

    def get_queryset(self, request):
        orders = super().get_queryset(request)
        return orders.calculate_total_cost()

    def save_formset(self, request, form, formset, change):
        order_items = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()

        for order_item in order_items:
            if not order_item.price:
                product = Product.objects.get(id=order_item.product.id)
                order_item.price = product.price
            order_item.save()


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    pass

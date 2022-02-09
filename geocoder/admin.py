from django.contrib import admin

from .models import Place


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ('address', 'latitude', 'longitude', 'fetch_coordinates_at')
    readonly_fields = ('fetch_coordinates_at',)

# Register your models here.

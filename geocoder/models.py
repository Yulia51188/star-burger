from django.db import models


class Place(models.Model):
    address = models.CharField(
        'Адрес места',
        max_length=100,
        unique=True,
        db_index=True,
    )
    latitude = models.FloatField('Широта')
    longitude = models.FloatField('Долгота')
    fetch_coordinates_at = models.DateTimeField(
        'Дата запроса координат',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'Место'
        verbose_name_plural = 'Места'

    def __str__(self):
        return self.address

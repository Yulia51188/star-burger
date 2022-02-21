import requests
from django.conf import settings
from geopy import distance

from geocoder.models import Place


def fetch_coordinates(apikey, address):
    if not apikey:
        return None

    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


def calculate_distance(lonlat_coords_from, lonlat_coords_to):
    if not lonlat_coords_from or not lonlat_coords_to:
        return None
    lon_from, lat_from = lonlat_coords_from
    lon_to, lat_to = lonlat_coords_to
    dist = distance.distance((lat_from, lon_from), (lat_to, lon_to)).km
    return dist


def define_coordinates(address):
    try:
        place = Place.objects.get(address=address)
        return place.longitude, place.latitude
    except Place.DoesNotExist:
        coordinates = fetch_coordinates(settings.GEOCODER_TOKEN, address)
        if coordinates:
            lon, lat = coordinates
            Place.objects.create(
                address=address,
                longitude=lon,
                latitude=lat,
            )
        return coordinates


def get_existed_places(addresses):
    existed_places = Place.objects.filter(address__in=addresses)
    return {
        place.address: (place.longitude, place.latitude)
        for place in existed_places
    }


def fetch_coordinates_by_addresses(addresses, apikey):
    unique_addresses = list(set(addresses))
    known_coordinates = get_existed_places(unique_addresses)
    if len(unique_addresses) > len(known_coordinates):
        new_places = []
        for address in addresses:
            if not known_coordinates.get(address, None):
                known_coordinates[address] = fetch_coordinates(apikey, address)
                if known_coordinates[address]:
                    lon, lat = known_coordinates[address]
                    new_places.append(Place(
                        address=address,
                        longitude=lon,
                        latitude=lat
                    ))
        if any(new_places):
            Place.objects.bulk_create(new_places)
    return known_coordinates

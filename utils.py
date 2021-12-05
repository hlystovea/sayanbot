from os import environ

import requests
from dotenv import load_dotenv

from schema.weather import Gismeteo, OpenWeather, Yandex

load_dotenv()


def gis_weather(coordinates):
    token = environ.get('GIS_TOKEN')
    url = 'https://api.gismeteo.net/v2/weather/current/'
    headers = {
        'X-Gismeteo-Token': token,
        'Accept-Encoding': 'gzip',
    }
    params = {
        'lang': 'ru',
        'latitude': coordinates[0],
        'longitude': coordinates[1],
    }
    text = 'По данным ["Gismeteo"](https://www.gismeteo.ru/) сейчас:\n'
    r = requests.get(url, headers=headers, params=params)
    if r.status_code == 200:
        weather = Gismeteo(**r.json()['response'])
        return f'{text}{weather.current_weather()}.\n'
    else:
        return ya_weather(coordinates)


def ya_weather(coordinates):
    token = environ.get('YA_TOKEN')
    url = 'https://api.weather.yandex.ru/v2/informers/'
    headers = {
        'X-Yandex-API-Key': token,
    }
    params = {
        'lang': 'ru-RU',
        'lat': coordinates[0],
        'lon': coordinates[1],
    }
    text = 'По данным ["Яндекс.Погода"](https://yandex.ru/pogoda/) сейчас:\n'
    r = requests.get(url, headers=headers, params=params)
    if r.status_code == 200:
        weather = Yandex(**r.json())
        return f'{text}{weather.current_weather()}.\n'
    else:
        return op_weather(coordinates)


def op_weather(coordinates):
    token = environ.get('OP_TOKEN')
    url = 'https://api.openweathermap.org/data/2.5/weather/'
    params = {
        'lat': coordinates[0],
        'lon': coordinates[1],
        'appid': token,
        'units': 'metric',
        'lang': 'ru',
    }
    text = 'По данным ["OpenWeather"](https://openweathermap.org/) сейчас:\n'
    r = requests.get(url, params=params)
    if r.status_code == 200:
        weather = OpenWeather(**r.json())
        return f'{text}{weather.current_weather()}.\n'
    else:
        return 'Сервис с погодой сейчас недоступен. Попробуйте немного позже.'


def weather(coordinates):
    return gis_weather(coordinates)


if __name__ == '__main__':
    print(weather((52.927255, 91.361045)))

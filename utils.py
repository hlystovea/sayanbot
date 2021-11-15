import json
from os import environ

import requests
from dotenv import load_dotenv

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
        weather = json.loads(r.text)

        temp = weather['response']['temperature']['air']['C']
        cond = weather['response']['description']['full'].lower()
        wind = weather['response']['wind']['speed']['m_s']

        text += f'{temp:+.1f} \xb0С, {wind} м/с, {cond}.\n'
        return text
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
    condition = {
        'clear': 'ясно',
        'partly-cloudy': 'малооблачно',
        'cloudy': 'облачно с прояснениями',
        'overcast': 'пасмурно',
        'drizzle': 'морось',
        'light-rain': 'небольшой дождь',
        'rain': 'дождь',
        'moderate-rain': 'умеренно сильный дождь',
        'heavy-rain': 'сильный дождь',
        'continuous-heavy-rain': 'длительный сильный дождь',
        'showers': 'ливень',
        'wet-snow': 'дождь со снегом',
        'light-snow': 'небольшой снег',
        'snow': 'снег',
        'snow-showers': 'снегопад',
        'hail': 'град',
        'thunderstorm': 'гроза',
        'thunderstorm-with-rain': 'дождь с грозой',
        'thunderstorm-with-hail': 'гроза с градом',
    }
    text = 'По данным ["Яндекс.Погода"](https://yandex.ru/pogoda/) сейчас:\n'
    r = requests.get(url, headers=headers, params=params)
    if r.status_code == 200:
        weather = json.loads(r.text)
        temp = weather['fact']['temp']
        cond = weather['fact']['condition']
        wind = weather['fact']['wind_speed']

        text += f'{temp:+.1f} \xb0С, {wind} м/с, {condition[cond]}.\n'
        return text
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
        weather = json.loads(r.text)
        temp = weather['main']['temp']
        cond = weather['weather'][0]['description']
        wind = weather['wind']['speed']

        text += f'{temp:+.1f} \xb0С, {wind} м/с, {cond}.\n'
        return text
    else:
        return 'Проблемы со связью. Попробуйте немного позже.'


def weather(coordinates):
    return gis_weather(coordinates)


if __name__ == '__main__':
    print(weather((52.927255, 91.361045)))

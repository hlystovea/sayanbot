import asyncio
from os import environ
import time

import aiohttp
from dotenv import load_dotenv
from schema.weather import Gismeteo, OpenWeather, Yandex

load_dotenv()


async def gismeteo_current(coordinates: tuple[float]) -> str:
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
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url=url, params=params, ssl=False) as r:
            if r.status == 200:
                text = 'По данным ["Gismeteo"](https://www.gismeteo.ru/) сейчас:\n' # noqa (E501)
                data = await r.json()
                weather = Gismeteo(**data['response'])
                return f'{text}{weather.current_weather()}.\n'
            return None


async def yandex_current(coordinates: tuple[float]) -> str:
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
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url=url, params=params, ssl=False) as r:
            if r.status == 200:
                text = 'По данным ["Яндекс.Погода"](https://yandex.ru/pogoda/) сейчас:\n' # noqa (E501)
                data = await r.json()
                weather = Yandex(**data)
                return f'{text}{weather.current_weather()}.\n'
            return None


async def openweather_current(coordinates: tuple[float]) -> str:
    token = environ.get('OP_TOKEN')
    url = 'https://api.openweathermap.org/data/2.5/weather/'
    params = {
        'lat': coordinates[0],
        'lon': coordinates[1],
        'appid': token,
        'units': 'metric',
        'lang': 'ru',
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, params=params, ssl=False) as r:
            if r.status == 200:
                text = 'По данным ["OpenWeather"](https://openweathermap.org/) сейчас:\n' # noqa (E501)
                data = await r.json()
                weather = OpenWeather(**data)
                return f'{text}{weather.current_weather()}.\n'
            return 'Сервис погоды сейчас недоступен. Попробуйте немного позже.'


async def get_current_weather(coordinates: tuple[float]) -> str:
    results = await asyncio.gather(
        gismeteo_current(coordinates),
        yandex_current(coordinates),
        openweather_current(coordinates),
    )
    return results[0] or results[1] or results[2]


if __name__ == '__main__':
    start = time.time()
    print(asyncio.run(get_current_weather((52.927255, 91.361045))))
    print(time.time() - start)

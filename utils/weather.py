import asyncio
import logging
from os import environ
from typing import List, Optional, Union

from aiohttp import ClientSession, ContentTypeError
from pydantic import parse_obj_as, ValidationError

from schema.weather import Gismeteo, OpenWeather, Yandex


async def gismeteo_current(coordinates: tuple[float]) -> Optional[Gismeteo]:
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
    async with ClientSession(headers=headers) as session:
        async with session.get(url=url, params=params, ssl=False) as r:
            if r.status == 200:
                try:
                    data = await r.json()
                    return Gismeteo(**data['response'])
                except (ContentTypeError, ValidationError, KeyError) as error:
                    logging.error(repr(error))
            return None


async def yandex_current(coordinates: tuple[float]) -> Optional[Yandex]:
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
    async with ClientSession(headers=headers) as session:
        async with session.get(url=url, params=params, ssl=False) as r:
            if r.status == 200:
                try:
                    data = await r.json()
                    return Yandex(**data)
                except (ContentTypeError, ValidationError, KeyError) as error:
                    logging.error(repr(error))
            return None


async def openweather_current(coordinates: tuple[float]) -> Optional[OpenWeather]:  # noqa (E501)
    token = environ.get('OP_TOKEN')
    url = 'https://api.openweathermap.org/data/2.5/weather/'
    params = {
        'lat': coordinates[0],
        'lon': coordinates[1],
        'appid': token,
        'units': 'metric',
        'lang': 'ru',
    }
    async with ClientSession() as session:
        async with session.get(url=url, params=params, ssl=False) as r:
            if r.status == 200:
                try:
                    data = await r.json()
                    return OpenWeather(**data)
                except (ContentTypeError, ValidationError, KeyError) as error:
                    logging.error(repr(error))
            return 'Сервис погоды сейчас недоступен. Попробуйте немного позже.'


async def gismeteo_forecast(coordinates: tuple[float], days: int) -> List[Gismeteo]:  # noqa (E501)
    token = environ.get('GIS_TOKEN')
    url = 'https://api.gismeteo.net/v2/weather/forecast/'
    headers = {
        'X-Gismeteo-Token': token,
        'Accept-Encoding': 'gzip',
    }
    params = {
        'lang': 'ru',
        'latitude': coordinates[0],
        'longitude': coordinates[1],
        'days': days,
    }
    async with ClientSession(headers=headers) as session:
        async with session.get(url=url, params=params, ssl=False) as r:
            if r.status == 200:
                try:
                    data = await r.json()
                    return parse_obj_as(List[Gismeteo], data['response'])
                except (ContentTypeError, ValidationError, KeyError) as error:
                    logging.error(repr(error))
            return []


async def get_current_weather(
    coordinates: tuple[float]
) -> Union[Gismeteo, Yandex, OpenWeather]:
    results = await asyncio.gather(
        gismeteo_current(coordinates),
        yandex_current(coordinates),
        openweather_current(coordinates),
    )
    return results[0] or results[1] or results[2]


async def get_forecast_24h(coordinates: tuple[float]) -> List[Gismeteo]:
    return await gismeteo_forecast(coordinates, 2)

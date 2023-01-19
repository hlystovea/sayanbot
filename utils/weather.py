import asyncio
from os import environ

from aiohttp import ClientSession, ContentTypeError
from pydantic import parse_obj_as, ValidationError

from logger import logger
from schemes.weather import Gismeteo, OpenWeather, Weather, Yandex


HOSTS = {
    'gismeteo': {
        'url': 'https://api.gismeteo.net/v2/weather/current/',
        'headers': {
            'X-Gismeteo-Token': environ['GIS_TOKEN'],
            'Accept-Encoding': 'gzip',
        },
        'params': {
            'lang': 'ru',
        },
    },
    'yandex': {
        'url': 'https://api.weather.yandex.ru/v2/informers/',
        'headers': {
            'X-Yandex-API-Key': environ['YA_TOKEN'],
        },
        'params': {
            'lang': 'ru-RU',
        },
    },
    'openweather': {
        'url': 'https://api.openweathermap.org/data/2.5/weather/',
        'headers': {},
        'params': {
            'units': 'metric',
            'lang': 'ru',
            'appid': environ['OP_TOKEN'],
        }
    },
}


_sessions: dict[str, ClientSession] = {}


async def get_session(host: str) -> ClientSession:
    session = _sessions.get(host)

    if session is not None and not session.closed:
        return session

    session = ClientSession(headers=HOSTS[host]['headers'])
    _sessions[host] = session

    return session


async def gismeteo_current(coordinates: tuple[float, float]) -> Gismeteo | None:  # noqa(E501)
    url = HOSTS['gismeteo']['url']
    params = {
        'latitude': coordinates[0],
        'longitude': coordinates[1],
    }
    params |= HOSTS['gismeteo']['params']

    session = await get_session('gismeteo')

    async with session.get(url=url, params=params, ssl=False) as r:
        if r.status == 200:
            try:
                data = await r.json()
                return Gismeteo(**data['response'])
            except (ContentTypeError, ValidationError, KeyError) as error:
                logger.error(repr(error))


async def yandex_current(coordinates: tuple[float, float]) -> Yandex | None:
    url = HOSTS['yandex']['url']
    params = {
        'lat': coordinates[0],
        'lon': coordinates[1],
    }
    params |= HOSTS['yandex']['params']

    session = await get_session('yandex')

    async with session.get(url=url, params=params, ssl=False) as r:
        if r.status == 200:
            try:
                data = await r.json()
                return Yandex(**data)
            except (ContentTypeError, ValidationError, KeyError) as error:
                logger.error(repr(error))


async def openweather_current(coordinates: tuple[float, float]) -> OpenWeather | None:  # noqa(E501)
    url = HOSTS['openweather']['url']
    params = {
        'lat': coordinates[0],
        'lon': coordinates[1],
    }
    params |= HOSTS['openweather']['params']

    session = await get_session('openweather')

    async with session.get(url=url, params=params, ssl=False) as r:
        if r.status == 200:
            try:
                data = await r.json()
                return OpenWeather(**data)
            except (ContentTypeError, ValidationError, KeyError) as error:
                logger.error(repr(error))


async def gismeteo_forecast(coordinates: tuple[float, float], days: int) -> list[Gismeteo]:  # noqa(E501)
    url = 'https://api.gismeteo.net/v2/weather/forecast/'
    params = {
        'latitude': coordinates[0],
        'longitude': coordinates[1],
        'days': days,
    }
    params |= HOSTS['gismeteo']['params']

    session = await get_session('gismeteo')

    async with session.get(url=url, params=params, ssl=False) as r:
        if r.status == 200:
            try:
                data = await r.json()
                return parse_obj_as(list[Gismeteo], data['response'])
            except (ContentTypeError, ValidationError, KeyError) as error:
                logger.error(repr(error))
        return []


async def get_current_weather(coordinates: tuple[float, float]) -> Weather | None:  # noqa(E501)
    results = await asyncio.gather(
        gismeteo_current(coordinates),
        yandex_current(coordinates),
        openweather_current(coordinates),
    )
    return results[0] or results[1] or results[2]


async def get_forecast_24h(coordinates: tuple[float, float]) -> list[Gismeteo]:
    return await gismeteo_forecast(coordinates, 2)

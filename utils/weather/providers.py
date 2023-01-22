from abc import ABC, abstractmethod

from aiohttp import ClientError, ClientSession
from pydantic import parse_obj_as

from schemes.weather import Gismeteo, OpenWeather, Yandex
from logger import logger

GISMETEO_API_URL = 'https://api.gismeteo.net/v2/weather/'
YANDEX_API_URL = 'https://api.weather.yandex.ru/v2/informers/'
OPENWEATHER_API_URL = 'https://api.openweathermap.org/data/2.5/weather/'

_pool: dict['AbstractWeatherProvider', ClientSession] = {}


class AbstractWeatherProvider(ABC):
    @property
    @abstractmethod
    def headers(self) -> dict:
        pass

    @abstractmethod
    def params(self, *args, **kwargs) -> dict:
        pass

    @abstractmethod
    def get_data(self, *args, **kwargs) -> dict:
        pass


class WeatherProviderMixin(AbstractWeatherProvider):
    def __init__(self, token: str = ''):
        self.token = token

    def _get_session(self) -> ClientSession:
        session = _pool.get(self)

        if session is not None and not session.closed:
            return session

        session = ClientSession(headers=self.headers)
        _pool[self] = session

        return session

    @property
    def headers(self) -> dict:
        return {}

    def params(self, *args, **kwargs) -> dict:
        return kwargs

    async def get_data(self, url: str, *args, **kwargs) -> dict | None:
        params = self.params(*args, **kwargs)
        session = self._get_session()

        try:
            async with session.get(url=url, params=params, ssl=False) as r:
                if r.status == 200:
                    return await r.json()
                logger.error(f'Response error: {r.status}, {await r.text()}')
        except ClientError as error:
            logger.error(repr(error))


class GismeteoWeatherProvider(WeatherProviderMixin):
    @property
    def headers(self) -> dict:
        return {
            'X-Gismeteo-Token': self.token,
            'Accept-Encoding': 'gzip',
        }

    def params(self, latitude: float, longitude: float, **kwargs) -> dict:
        params = {
            'lang': 'ru',
            'latitude': latitude,
            'longitude': longitude,
        }
        return params | super().params(**kwargs)

    async def current_weather(self, latitude: float, longitude: float) -> Gismeteo | None:  # noqa(E501)
        url = GISMETEO_API_URL + 'current/'
        data = await self.get_data(url, latitude, longitude)
        return Gismeteo(**data['response']) if data else None

    async def forecast(self, latitude: float, longitude: float, days: int = 3) -> list[Gismeteo] | None:  # noqa(E501)
        url = GISMETEO_API_URL + 'forecast/'
        data = await self.get_data(url, latitude, longitude, days=days)
        return parse_obj_as(list[Gismeteo], data['response']) if data else None


class YandexWeatherProvider(WeatherProviderMixin):
    @property
    def headers(self) -> dict:
        return {
            'X-Yandex-API-Key': self.token,
        }

    def params(self, latitude: float, longitude: float) -> dict:
        return {
            'lang': 'ru-RU',
            'lat': latitude,
            'lon': longitude,
        }

    async def current_weather(self, latitude: float, longitude: float) -> Yandex | None:  # noqa(E501)
        data = await self.get_data(YANDEX_API_URL, latitude, longitude)
        return Yandex(**data['fact']) if data else None


class OpenWeatherProvider(WeatherProviderMixin):
    def params(self, latitude: float, longitude: float) -> dict:
        return {
            'units': 'metric',
            'lang': 'ru',
            'appid': self.token,
            'lat': latitude,
            'lon': longitude,
        }

    async def current_weather(self, latitude: float, longitude: float) -> OpenWeather | None:  # noqa(E501)
        data = await self.get_data(OPENWEATHER_API_URL, latitude, longitude)
        return OpenWeather(**data) if data else None

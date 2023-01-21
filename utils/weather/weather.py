import asyncio
from os import environ

from schemes.weather import Gismeteo, Weather
from utils.weather.providers import (GismeteoWeatherProvider,
                                     OpenWeatherProvider,
                                     YandexWeatherProvider)


gismeteo = GismeteoWeatherProvider(token=environ['GIS_TOKEN'])
yandex = YandexWeatherProvider(token=environ['YA_TOKEN'])
openweather = OpenWeatherProvider(token=environ['OP_TOKEN'])


async def get_current_weather(coordinates: tuple[float, float]) -> Weather | None:
    results = await asyncio.gather(
        gismeteo.current_weather(*coordinates),
        yandex.current_weather(*coordinates),
        openweather.current_weather(*coordinates),
    )
    return results[0] or results[1] or results[2]


async def get_forecast(coordinates: tuple[float, float], days: int = 2) -> list[Gismeteo] | None:
    return await gismeteo.forecast(*coordinates, days)


async def main():
    print(await get_current_weather((0, 0)))


if __name__ == '__main__':
    asyncio.run(main())

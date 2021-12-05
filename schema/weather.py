from pydantic import BaseModel


CONDITION = {
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


class Weather(BaseModel):
    cond: str
    icon: str
    temp: int
    pressure: int
    humidity: int
    wind_speed: int
    feels_like: int

    def current_weather(self):
        temp = self.temp
        wind = self.wind_speed
        cond = self.cond
        return f'{temp:+.1f} \xb0С, {wind} м/с, {cond}'


class Gismeteo(Weather):
    def __init__(self, **kwargs):
        kwargs['cond'] = kwargs['description']['full'].lower()
        kwargs['temp'] = kwargs['temperature']['air']['C']
        kwargs['pressure'] = kwargs['pressure']['mm_hg_atm']
        kwargs['humidity'] = kwargs['humidity']['percent']
        kwargs['wind_speed'] = kwargs['wind']['speed']['m_s']
        kwargs['feels_like'] = kwargs['temperature']['comfort']['C']
        super().__init__(**kwargs)


class Yandex(Weather):
    def __init__(self, **kwargs):
        kwargs['cond'] = CONDITION[kwargs['fact']['condition']]
        kwargs['icon'] = kwargs['fact']['icon']
        kwargs['temp'] = kwargs['fact']['temp']
        kwargs['pressure'] = kwargs['fact']['pressure_mm']
        kwargs['humidity'] = kwargs['fact']['humidity']
        kwargs['wind_speed'] = kwargs['fact']['wind_speed']
        kwargs['feels_like'] = kwargs['fact']['feels_like']
        super().__init__(**kwargs)


class OpenWeather(Weather):
    def __init__(self, **kwargs):
        kwargs['cond'] = kwargs['weather'][0]['description']
        kwargs['icon'] = kwargs['weather'][0]['icon']
        kwargs['temp'] = kwargs['main']['temp']
        kwargs['pressure'] = 0.75006376*kwargs['main']['pressure']
        kwargs['humidity'] = kwargs['main']['humidity']
        kwargs['wind_speed'] = kwargs['wind']['speed']
        kwargs['feels_like'] = kwargs['main']['feels_like']
        super().__init__(**kwargs)

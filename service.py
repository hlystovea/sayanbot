import requests
import json
import os

def weather():
	yandex_token = os.environ.get('YA_TOKEN')
	open_token = os.environ.get('OP_TOKEN')
	url_ya = 'https://api.weather.yandex.ru/v2/forecast/'
	url_op = 'https://api.openweathermap.org/data/2.5/weather/'

	header_ya = {
    	'X-Yandex-API-Key': yandex_token,
		}

	param_op = {
		'lat': '52.916296', 
		'lon': '91.351843',
		'appid': open_token,
		'units': 'metric',
		'lang': 'ru',
    }

	# координаты мест для вывода погоды
	places = {
    	'name': ['Гладенькая', 'Ергаки', 'Черемушки'],
	'lat': ['52.917383', '52.837717', '52.853902'],
    	'lon': ['91.352284', '93.255870', '91.408986'],
    }

	quan = len(places['name']) # определяет количество запросов о погоде

	# расшифровка осадков для яндекс погоды
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

	list_weather_ya = f'По данным ["Яндекс.Погода"](https://yandex.ru/pogoda/cheryomushki) сейчас:\n'
	list_weather_op = f'По данным ["OpenWeather"](https://openweathermap.org/city/1492893) сейчас:\n'

	response_ya = requests.get(url_ya, headers=header_ya)
	response_op = requests.get(url_op, params=param_op)
	if response_ya.status_code == 200: # проверяет доступность сервера погоды
		for i in range(0, quan): # перебирает места и формирует список погоды
			param_ya = {
				'lat': places['lat'][i], 
				'lon': places['lon'][i],
				'lang': 'ru_RU',
				'limit': '1',
				'extra': 'true',
				'hours': 'false',
			}
			response = requests.get(url_ya, headers=header_ya, params=param_ya)
			weather = json.loads(response.text)
			fact_temp = weather['fact']['temp']
			fact_cond = weather['fact']['condition']
			fact_wind = weather['fact']['wind_speed']
			
			sn = '+'
			if fact_temp <= 0: # знак перед значением температуры
				sn = ''
			
			place = places['name'][i]
			fact_weather = f'{place}: {sn}{fact_temp} \xb0С, {fact_wind} м/с, {condition[fact_cond]}.\n'
			list_weather_ya = list_weather_ya + fact_weather
		return list_weather_ya
	elif response_op.status_code == 200: # проверяет доступность сервера погоды
		for i in range(0, quan): # перебирает места и формирует список погоды
			param_op = {
				'lat': places['lat'][i], 
				'lon': places['lon'][i],
				'appid': open_token,
				'units': 'metric',
				'lang': 'ru',
			}
			response = requests.get(url_op, params=param_op)
			weather = json.loads(response.text)
			fact_temp = weather['main']['temp']
			fact_cond = weather['weather'][0]['description']
			fact_wind = weather['wind']['speed']
			
			sn = '+'
			if fact_temp <= 0: # знак перед значением температуры
				sn = ''
			
			place = places['name'][i]
			fact_weather = f'{place}: {sn}{fact_temp} \xb0С, {fact_wind} м/с, {fact_cond}.\n'
			list_weather_op = list_weather_op + fact_weather
		return list_weather_op
	else:
		return f'Проблемы со связью. Попробуйте немного позже.'


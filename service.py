import requests
import json
import os
from text_db import text_db, phone_msg

def text_message(message): #ответ на текстовое сообщение
    keys = text_db.keys()
    n = 0
    for key in keys: #поиск совпадений в словаре
        if key in message.text.lower():
            n+=1
            return text_db[key] #ответ
    if n == 0:
        return 'Извини. Я в ответах ограничен. Правильно задавай вопросы.'


def weather_yandex():
	yandex_token = os.environ.get('YA_TOKEN')
	url = 'https://api.weather.yandex.ru/v2/forecast/'

	header = {
    	'X-Yandex-API-Key': yandex_token,
		}
	
	# координаты мест для вывода погоды
	coord_1 = {
    	'lat': '52.917383', 
    	'lon': '91.352284',
    	'lang': 'ru_RU',
    	'limit': '1',
    	'extra': 'true',
    	'hours': 'false',
    }

	coord_2 = {
    	'lat': '52.837717', 
    	'lon': '93.255870',
    	'lang': 'ru_RU',
    	'limit': '1',
    	'extra': 'true',
    	'hours': 'false',
    }

	coord_3 = {
		'lat': '52.853902', 
    	'lon': '91.408986',
    	'lang': 'ru_RU',
    	'limit': '1',
    	'extra': 'true',
    	'hours': 'false',
	}

	places = ['Гладенькая', 'Ергаки', 'Черемушки'] # названия мест
	coordinates = [coord_1, coord_2, coord_3] # последовательность координат
	
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

	if len(places) <= len(coordinates): # защита от короткого списка
		quan = len(places)
	else:
		quan = len(coordinates)

	list_weather = f'Текущая погода по версии Яндекса:\n'

	response = requests.get(url, headers=header)
	if response.status_code == 200: # проверяет доступность сервера погоды
		for i in range(0, quan): # перебирает места и формирует список погоды
			response = requests.get(url, headers=header, params=coordinates[i])
			weather = json.loads(response.text)
			fact_temp = weather['fact']['temp']
			fact_cond = weather['fact']['condition']
			fact_wind = weather['fact']['wind_speed']
			
			sn = '+'
			if fact_temp <= 0: # знак перед значением температуры
				sn = ''

			fact_weather = f'{places[i]}: {sn}{fact_temp} \xb0С, {fact_wind} м/с, {condition[fact_cond]}.\n'
			list_weather = list_weather + fact_weather
		
		return list_weather
	else:
		return f'Проблемы со связью. Попробуйте немного позже.'

def phone():
    return phone_msg

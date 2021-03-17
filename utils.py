import json
import os

import requests

places = {
	'ГК "Гладенькая"': {
		'coordinates': (52.927255, 91.361045),
		'phone': '+79233933300',
		'url': 'http://ski-gladenkaya.ru',
		'info': {
			'trails': 3,
			'max_length': 4.2,
			'total_length': 8,
			'vertical_drop': 920,
			'max_elevation': 1747,
			'lifts': 3,
			'type_lift': 'кресельный, бугельный',
			},
	},
	'ГК "Черёмуховый лог"': {
		'coordinates': (52.853902, 91.408986),
		'phone': '+73904231216',
		'url': 'http://info-borus.ru/ski/',
		'info': {
			'trails': 2,
			'max_length': 1,
			'total_length': 1.6,
			'vertical_drop': 160,
			'max_elevation': 555,
			'lifts': 1,
			'type_lift': 'кресельный',
			},
	},
	'База "Ергаки"': {
		'coordinates': (52.837717, 93.255870),
		'phone': '88007076270',
		'url': 'http://ergaki.com/',
		'info': {
			'trails': 1,
			'max_length': 1.2,
			'total_length': 1.2,
			'vertical_drop': 250,
			'max_elevation': 1680,
			'lifts': 1,
			'type_lift': 'бугельный',
			},
	},
	'База "Снежная" (Ергаки)': {
		'coordinates': (52.799549, 93.268188),
		'phone': '+79083272930\n+79029968773',
		'url': 'https://snow611.ru/',
		'info': {
			'trails': 1,
			'max_length': 1.6,
			'total_length': 1.6,
			'vertical_drop': 330,
			'max_elevation': 1750,
			'lifts': 1,
			'type_lift': 'бугельный',
			},
	},
	'Пик Звёздный (Ергаки)': {
		'coordinates': (52.829201, 93.300938),
		'phone': '+79503040055',
		'url': 'http://ergaki-sayan.ru/zvezdnyi/',
		'info': {
			'trails': 'нет данных',
			'max_length': 'нет данных',
			'total_length': 'нет данных',
			'vertical_drop': 'нет данных',
			'max_elevation': 'нет данных',
			'lifts': 'нет данных',
			'type_lift': 'нет данных',
			},
	},
	'Тушканчик кэмп (Ергаки)': {
		'coordinates': (52.803941, 93.247428),
		'phone': '88005003448',
		'url': 'https://tushkanchik.camp/',
		'info': {
			'trails': 1,
			'max_length': 1.8,
			'total_length': 1.8,
			'vertical_drop': 400,
			'max_elevation': 1797,
			'lifts': 1,
			'type_lift': 'бугельный',
			},
	},
	'ГК "Бобровый лог"': {
		'coordinates': (55.962128, 92.794737),
		'phone': '+73912568686',
		'url': 'https://bobrovylog.ru/',
		'info': {
			'trails': 15,
			'max_length': 1.6,
			'total_length': 11,
			'vertical_drop': 350,
			'max_elevation': 517,
			'lifts': 4,
			'type_lift': 'кресельный, бугельный',
			},
	},
	'Приисковый': {
		'coordinates': (54.652993, 88.703671),
		'phone': '88005003449',
		'url': 'https://priiskovy.ru/',
		'info': {
			'trails': 7,
			'max_length': 1.7,
			'total_length': 9.8,
			'vertical_drop': 400,
			'max_elevation': 1657,
			'lifts': 0,
			'type_lift': 'сноукэты, снегоходы',
			},
	},
	'Шерегеш': {
		'coordinates': (52.947942, 87.932612),
		'phone': '',
		'url': 'https://gesh.ru/',
		'info': {
			'trails': 1,
			'max_length': 4.2,
			'total_length': 36.9,
			'vertical_drop': 680,
			'max_elevation': 1270,
			'lifts': 1,
			'type_lift': 'гондольный, кресельный, бугельный',
			},
	},
	'ГК "Оленья подкова"': {
		'coordinates': (54.345838, 93.250253),
		'phone': '+79024688352',
		'url': 'https://vk.com/gora_korona/',
		'info': {
			'trails': 1,
			'max_length': 1,
			'total_length': 1,
			'vertical_drop': 160,
			'max_elevation': 650,
			'lifts': 1,
			'type_lift': 'бугельный',
			},
	},
	'ГК "Сюгеш"': {
		'coordinates': (52.717182, 89.918972),
		'phone': '+79833779577',
		'url': 'https://sugesh.ru/',
		'info': {
			'trails': 0.75,
			'max_length': 0.75,
			'total_length': 0.75,
			'vertical_drop': 120,
			'max_elevation': 670,
			'lifts': 1,
			'type_lift': 'бугельный',
			},
	},
}

trail_maps = {
	'ГК "Гладенькая"': 'gla.jpg',
	'База "Ергаки"': 'ergaki.jpg',
	'Бобровый лог': 'bobr_log.jpg',
	'Шерегеш': 'gesh.jpg',
}

def gis_weather(coordinates):
	token = os.environ.get('GIS_TOKEN')
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
	token = os.environ.get('YA_TOKEN')
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
	token = os.environ.get('OP_TOKEN')
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

import requests
import json
import os

locations = {
	'ГК "Гладенькая"': (
		(52.927255, 91.361045),
		'+79233933300',
		'http://ski-gladenkaya.ru',
	),
	'ГК "Черёмуховый лог"': (
		(52.853902, 91.408986),
		'+73904231216',
		'http://info-borus.ru/ski/',
	),
	'База "Ергаки"': (
		(52.837717, 93.255870),
		'88007076270',
		'http://ergaki.com/',
	),
	'База "Снежная"': (
		(52.799549, 93.268188),
		'+79083272930',
		'https://snow611.ru/',
	),
	'Пик Звёздный': (
		(52.829201, 93.300938),
		'+79503040055',
		'',
	),
	'Тушканчик кэмп': (
		(52.803941, 93.247428),
		'88005003448',
		'https://tushkanchik.camp/',
	),
	'Приисковый': (
		(54.652993, 88.703671),
		'88005003449',
		'https://priiskovy.ru/',
	),
	'Шерегеш': (
		(52.947942, 87.932612),
		'',
		'https://gesh.ru/',
	),
	'Оленья подкова': (
		(54.345838, 93.250253),
		'+79024688352',
		'https://vk.com/gora_korona/',
	),
	'Сюгеш': (
		(52.717182, 89.918972),
		'+79833779577',
		'https://sugesh.ru/',
	),
}


def gis_weather():
	token = os.environ.get('GIS_TOKEN')
	url = 'https://api.gismeteo.net/v2/weather/current/'
	headers = {
		'X-Gismeteo-Token': token,
		'Accept-Encoding': 'gzip',
	}
	params = {
		'lang': 'ru',
		'latitude': '52.916296',
		'longitude': '91.351843',
	}
	text = 'По данным ["Gismeteo"](https://www.gismeteo.ru/) сейчас:\n'
	r = requests.get(url, headers=headers, params=params)
	if r.status_code == 200:
		for name in locations:
			params = {
				'lang': 'ru',
				'latitude': locations[name][0][0],
				'longitude': locations[name][0][1],
			}

			r = requests.get(url, headers=headers, params=params)
			weather = json.loads(r.text)

			temp = weather['response']['temperature']['air']['C']
			cond = weather['response']['description']['full'].lower()
			wind = weather['response']['wind']['speed']['m_s']

			weather = f'{name}: {temp:+.1f} \xb0С, {wind} м/с, {cond}.\n'
			text += weather
		return text
	else:
		return ya_weather()


def ya_weather():
	token = os.environ.get('YA_TOKEN')
	url = 'https://api.weather.yandex.ru/v2/informers/'
	headers = {
		'X-Yandex-API-Key': token,
	}
	params = {
		'lang': 'ru-RU',
		'lat': '52.916296',
		'lon': '91.351843',
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
		for name in locations:
			params = {
				'lat': locations[name][0][0],
				'lon': locations[name][0][1],
				'lang': 'ru_RU',
				'limit': '1',
				'extra': 'true',
				'hours': 'false',
			}
			r = requests.get(url, headers=headers, params=params)
			weather = json.loads(r.text)
			temp = weather['fact']['temp']
			cond = weather['fact']['condition']
			wind = weather['fact']['wind_speed']

			weather = f'{name}: {temp:+.1f} \xb0С, {wind} м/с, {condition[cond]}.\n'
			text += weather
		return text
	else:
		return op_weather()


def op_weather():
	token = os.environ.get('OP_TOKEN')
	url = 'https://api.openweathermap.org/data/2.5/weather/'
	params = {
		'lat': '52.916296',
		'lon': '91.351843',
		'appid': token,
		'units': 'metric',
		'lang': 'ru',
	}
	text = 'По данным ["OpenWeather"](https://openweathermap.org/) сейчас:\n'
	r = requests.get(url, params=params)
	if r.status_code == 200:
		for name in locations:
			params = {
				'lat': locations[name][0][0],
				'lon': locations[name][0][1],
				'appid': token,
				'units': 'metric',
				'lang': 'ru',
			}
			r = requests.get(url, params=params)
			weather = json.loads(r.text)
			temp = weather['main']['temp']
			cond = weather['weather'][0]['description']
			wind = weather['wind']['speed']

			weather = f'{name}: {temp:+.1f} \xb0С, {wind} м/с, {cond}.\n'
			text += weather
		return text
	else:
		return 'Проблемы со связью. Попробуйте немного позже.'


def weather():
	return gis_weather()


if __name__ == '__main__':
	print(weather())

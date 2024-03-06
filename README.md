# Sayanbot
Телеграм бот с полезной информацией для райдеров

![Static Badge](https://img.shields.io/badge/hlystovea-sayanbot-sayanbot)
![GitHub top language](https://img.shields.io/github/languages/top/hlystovea/sayanbot)
![GitHub](https://img.shields.io/github/license/hlystovea/sayanbot)
![GitHub Repo stars](https://img.shields.io/github/stars/hlystovea/sayanbot)
![GitHub issues](https://img.shields.io/github/issues/hlystovea/sayanbot)

## Описание
Показывает погоду на склоне и информацию о горнолыжных курортах.

## Возможности
- Просмотр текущей погоды на склоне
- Запрос координат местоположения курорта
- Просмотр информации о курорте
- Просмотр карты склона
- Запрос ссылок на веб-камеры
- Загрузка и скачивание gps-треков с маршрутами (поддерживается только .gpx формат)

## Технологии
- Python 3.9
- Aiogram
- MongoDB
- Pydantic

## О погоде
Бот получает погоду от сторонних API, отправляя запрос c координатами местоположения курорта. Поддерживаются следующие погодные сервисы: Gismeteo, Yandex, OpenWeather. Опрос сервисов происходит параллельно, но результат отдается по приоритету в указанном выше порядке. Если первый сервис не доступен, пользователю отправляются данные от следующего и т.д. Таким образом, при недоступности первого сервиса, бот не тратит время на новый запрос. 

## Установка (Linux)
У вас должен быть установлен [Docker Compose](https://docs.docker.com/compose/)

1. Клонирование репозитория 

```git clone https://github.com/hlystovea/sayanbot.git```  

2. Переход в директорию sayanbot

```cd sayanbot```

3. Создание файла с переменными окружения

```cp env.example .env```

4. Заполнение файла .env своими переменными

```nano .env```

5. Запуск проекта

```sudo docker compose up -d```

5. Запуск mongo-express:

```docker run --network sayanbot_network --env-file .env -p 8081:8081 mongo-express```

6. По адресу http://127.0.0.1:8081/ будет доступен Mongo Express для администрирования MongoDB.

7. Загрузите в Mongo данные из файла mongo_ski_resort_dump или заполните своими.

## Поддержка
Если у вас возникли сложности или вопросы по использованию проекта, создайте 
[обсуждение](https://github.com/hlystovea/reservoirs_web/issues/new/choose) в данном репозитории или напишите в [Telegram](https://t.me/hlystovea).


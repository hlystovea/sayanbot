[![Sayanbot deploy](https://github.com/hlystovea/sayanbot/actions/workflows/main.yml/badge.svg)](https://github.com/hlystovea/sayanbot/actions/workflows/main.yml)

# Sayanbot (Телеграм бот)

### Описание
Показывает погоду на склоне и информацию о горнолыжных курортах.

### Доступны следующие возможности
- Просмотр текущей погоды на склоне
- Запрос координат местоположения курорта
- Просмотр информации о курорте
- Просмотр карты склона
- Запрос ссылок на веб-камеры
- Загрузка и скачивание gps-треков с маршрутами (поддерживается только .gpx формат)

### Технологии
- Python 3.9
- Aiogram
- MongoDB
- Pydantic

### О погоде
Бот получает погоду от сторонних API, отправляя запрос c координатами местоположения курорта. Поддерживаются следующие погодные сервисы: Gismeteo, Yandex, OpenWeather. Опрос сервисов происходит параллельно, но результат отдается по приоритету в указанном выше порядке. Если первый сервис не доступен, пользователю отправляются данные от следующего и т.д. Таким образом, при недоступности первого сервиса, бот не тратит время на новый запрос. 

### Начало работы

1. Склонируйте проект:

```git clone https://github.com/hlystovea/sayanbot.git```  


2. Создайте файл .env по примеру env.example.


3. Соберите основной контейнер:

```docker build -t <docker_hub>/sayanbot:latest .```


4. Запустите контейнеры:

```docker-compose up -d```


5. Запустите mongo-express:

```docker run --network sayanbot_network --env-file .env -p 8081:8081 mongo-express```


6. По адресу http://127.0.0.1:8081/ будет доступен Mongo Express для администрирования MongoDB.


7. Загрузите в Mongo данные из файла mongo_ski_resort_dump или заполните своими.



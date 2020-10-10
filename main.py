import telebot
import json
import requests
import os
from text_db import (text_db, start_msg, help_msg, phone_msg)
from titles import (bot_names, weather_title, phone_book)
from service import (text_message, weather_yandex, phone)

token = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(token)


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, start_msg)


@bot.message_handler(commands=['help'])
def help_message(message):
    bot.send_message(message.chat.id, help_msg)


@bot.message_handler(content_types=['text'])
def text_waiting(message):  # функция определяет реакцию бота на сообщения
    split_message = message.text.split()
    name = split_message[0]
    if name.lower() in bot_names:  # ждёт обращения к боту
        if len(split_message) < 2:  # проверяет длину сообщения
            bot.send_message(message.chat.id, (f'Ты что-то хотел'
                                               f' {message.from_user.first_name}?'))
        else:  # при длине 2 слова и более ищёт команду
            command = split_message[1]
            if command.lower() in weather_title:  # ищет упоминание погоды
                bot.send_message(message.chat.id, weather_yandex())
            elif command.lower() in phone_book:  # ищет упоминание тел.книги
                bot.send_message(message.chat.id, phone())
            elif command.lower() == 'рация' or command.lower() == 'частота':
                bot.send_message(message.chat.id, '12 канал 464.425 Мгц')
            else:  # если известных команд не найдено, отвечает по шаблону
                bot.send_message(message.chat.id, text_message(message))


bot.polling()

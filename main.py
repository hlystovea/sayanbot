import telebot
import json
import requests
import os
from text_db import (start_msg, help_msg, phone_msg, radio_msg, links_msg)
from titles import (bot_names, weather_title, phone_book)
from service import weather

token = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(token)

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, start_msg)

@bot.message_handler(commands=['help'])
def help_message(message):
    bot.send_message(message.chat.id, help_msg)

@bot.message_handler(commands=['weather'])
def weather_message(message):
    bot.send_message(message.chat.id, weather(), parse_mode='Markdown', disable_web_page_preview=True)

@bot.message_handler(commands=['phone'])
def phone_message(message):
    bot.send_message(message.chat.id, phone_msg)

@bot.message_handler(commands=['radio', 'частота'])
def radio_message(message):
    bot.send_message(message.chat.id, radio_msg)

@bot.message_handler(commands=['links', 'ссылки'])
def radio_message(message):
    bot.send_message(message.chat.id, links_msg, disable_web_page_preview=True)

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
                bot.send_message(message.chat.id, weather())
            elif command.lower() in phone_book:  # ищет упоминание тел.книги
                bot.send_message(message.chat.id, phone_msg)
            elif command.lower() == 'рация' or command.lower() == 'частота':
                bot.send_message(message.chat.id, radio_msg)
            else:  # если известных команд не найдено, отвечает по шаблону
                bot.send_message(message.chat.id, f'Извини. Я в ответах ограничен. Правильно задавай вопросы.')


bot.polling()

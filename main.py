import telebot
import json
import requests
import os
from text_db import (start_msg, phone_msg, links_msg)
from titles import (bot_names, weather_title, phone_book)
from service import weather

token = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(token)

@bot.message_handler(commands=['start', 'help'])
def start_message(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(text='Погода на склоне', callback_data='weather'))
    markup.add(telebot.types.InlineKeyboardButton(text='Телефоны горнолыжных курортов и баз', callback_data='phones'))
    markup.add(telebot.types.InlineKeyboardButton(text='Сайты горнолыжных курортов и баз', callback_data='links'))
    bot.send_message(message.chat.id, start_msg, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    bot.answer_callback_query(callback_query_id=call.id, text='Смотрю на сервере..')
    answer = ''
    if call.data == 'weather':
        answer = weather()
    elif call.data == 'phones':
        answer = phone_msg
    elif call.data == 'links':
        answer = links_msg
    else:
        answer = f'Неисзвестный запрос'
    bot.send_message(call.message.chat.id, answer, parse_mode='Markdown', disable_web_page_preview=True)    
        
@bot.message_handler(commands=['weather'])
def weather_message(message):
    bot.send_message(message.chat.id, weather(), parse_mode='Markdown', disable_web_page_preview=True)

@bot.message_handler(commands=['phones', 'phone'])
def phone_message(message):
    bot.send_message(message.chat.id, phone_msg)

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
            else:  # если известных команд не найдено, отвечает по шаблону
                bot.send_message(message.chat.id, f'Извини. Я в ответах ограничен. Правильно задавай вопросы.')


bot.polling()

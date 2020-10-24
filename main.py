import telebot
import json
import requests
import os
from text_db import (start_msg, phone_msg, links_msg, webcam_msg)
from titles import (bot_names, weather_title, phone_book)
from service import weather

token = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(token)

@bot.message_handler(commands=['start', 'help'])
def start_message(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton
    (text='Погода на склоне', callback_data='weather'))
    markup.add(telebot.types.InlineKeyboardButton
    (text='Телефоны горнолыжных курортов и баз', callback_data='phones'))
    markup.add(telebot.types.InlineKeyboardButton
    (text='Сайты горнолыжных курортов и баз', callback_data='links'))
    markup.add(telebot.types.InlineKeyboardButton
    (text='Веб-камеры горнолыжных курортов', callback_data='webcam'))
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
    elif call.data == 'webcam':
        answer = webcam_msg
    else:
        answer = f'Неисзвестный запрос'
    bot.send_message(call.message.chat.id, answer, parse_mode='Markdown',
                                            disable_web_page_preview=True)
        
@bot.message_handler(commands=['weather', 'погода'])
def weather_message(message):
    bot.send_message(message.chat.id, weather(),
    parse_mode='Markdown', disable_web_page_preview=True)

@bot.message_handler(commands=['phones', 'phone', 'телефоны'])
def phone_message(message):
    bot.send_message(message.chat.id, phone_msg)

@bot.message_handler(commands=['links', 'ссылки'])
def links_message(message):
    bot.send_message(message.chat.id, links_msg,
    disable_web_page_preview=True)

@bot.message_handler(commands=['webcam', 'вебкамеры'])
def webcam_message(message):
    bot.send_message(message.chat.id, webcam_msg,
    disable_web_page_preview=True)

bot.polling()

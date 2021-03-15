import os

import telebot
from telebot.types import (InlineKeyboardButton,
                           InlineKeyboardMarkup,
                           ReplyKeyboardMarkup,)

from service import locations, weather
from text_db import webcam_msg


token = os.environ.get('SAYAN_TOKEN')
bot = telebot.TeleBot(token)


main_kbrd = ReplyKeyboardMarkup(True, True)
main_kbrd.row('Показать список команд')

buttons = {
    1: ('Погода на склоне', 'weather'),
    2: ('Информация', 'info'),
    3: ('Как проехать', 'location'),
    4: ('Веб-камеры', 'webcam'),
}


@bot.message_handler(commands=['start', 'help'])
def start(message):
    text = ('Привет! Я бот, который поможет тебе найти информацию '
            'о горнолыжных курортах юга Сибири. Чтобы начать, нажмите '
            '*"Показать список команд"*')
    bot.send_message(
        message.chat.id,
        text,
        reply_markup=main_kbrd,
        parse_mode='Markdown',
        disable_notification=True,
    )


@bot.message_handler(content_types=['text'])
def list_commands(message):
    keyboard = InlineKeyboardMarkup()
    for b in sorted(buttons):
        button = InlineKeyboardButton(
            buttons[b][0],
            callback_data=buttons[b][1])
        keyboard.add(button)
    text = 'Выберите команду:'
    if message.text.lower() == 'показать список команд':
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(
            message.chat.id,
            text,
            reply_markup=keyboard,
            disable_notification=True,
        )


@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    bot.answer_callback_query(
        callback_query_id=call.id,
        text='Смотрю на сервере..'
        )
    if call.data == 'weather':
        text = weather()
        bot.send_message(
            call.message.chat.id,
            text, parse_mode='Markdown',
            disable_web_page_preview=True,
            disable_notification=True,
        )
    elif call.data == 'location' or call.data == 'info':
        keyboard = InlineKeyboardMarkup()
        for name in locations:
            button = InlineKeyboardButton(
                name,
                callback_data=f'get_{call.data}&{name}',
            )
            keyboard.add(button)
        text = 'Выберите место:'
        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=keyboard,
            disable_notification=True,
        )
    elif 'get_location' in call.data:
        name = call.data.split('&')[1]
        loc = locations[name][0][0]
        lat = locations[name][0][1]
        text = f'{name}:'
        bot.send_message(
            call.message.chat.id,
            text,
            disable_notification=True,
        )
        bot.send_location(
            call.message.chat.id,
            loc,
            lat,
            disable_notification=True,
        )
    elif 'get_info' in call.data:
        name = call.data.split('&')[1]
        phone = locations[name][1]
        url = locations[name][2]
        text = f'{name}:\nТелефон: {phone}\nСайт: {url}'
        bot.send_message(
            call.message.chat.id,
            text,
            disable_web_page_preview=True,
            disable_notification=True,
        )
    else:
        answer = {
            'webcam': webcam_msg,
        }
        text = answer.get(call.data, 'Неизвестный запрос')
        bot.send_message(
            call.message.chat.id,
            text,
            disable_web_page_preview=True,
            disable_notification=True,
        )
    bot.delete_message(call.message.chat.id, call.message.message_id)


bot.polling()

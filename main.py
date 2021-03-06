import os

import telebot
from telebot.apihelper import ApiTelegramException
from telebot.types import (InlineKeyboardButton,
                           InlineKeyboardMarkup, ReplyKeyboardMarkup,)

from text_db import webcam_msg
from utils import places, trail_maps, weather


token = os.environ.get('SAYAN_TOKEN')
bot = telebot.TeleBot(token)


main_kbrd = ReplyKeyboardMarkup(True)
main_kbrd.row('Показать список команд')

buttons = {
    1: ('Погода на склоне', 'weather'),
    2: ('Как проехать', 'location'),
    3: ('Информация', 'info'),
    4: ('Карта склонов', 'trail_maps'),
    5: ('Веб-камеры', 'webcam'),
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
    if call.data == 'trail_maps':
        keyboard = InlineKeyboardMarkup()
        for name in trail_maps:
            button = InlineKeyboardButton(
                name,
                callback_data=f'get_trail&{name}',
            )
            keyboard.add(button)
        text = 'Выберите место:'
        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=keyboard,
            disable_notification=True,
        )     
    elif call.data == 'location' or call.data == 'info' or call.data == 'weather':
        keyboard = InlineKeyboardMarkup()
        for name in places:
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
    elif 'weather' in call.data:
        name = call.data.split('&')[1]
        coordinates = places[name]['coordinates']
        text = weather(coordinates)
        bot.send_message(
            call.message.chat.id,
            text,
            parse_mode='Markdown',
            disable_web_page_preview=True,
            disable_notification=True,
        )
    elif 'get_location' in call.data:
        name = call.data.split('&')[1]
        lat = places[name]['coordinates'][0]
        lon = places[name]['coordinates'][1]
        title = name
        address = f'{lat}, {lon}'
        bot.send_venue(
            call.message.chat.id,
            lat,
            lon,
            title,
            address,
            disable_notification=True,
        )
    elif 'get_info' in call.data:
        name = call.data.split('&')[1]
        text = (
            f"*{name}\n*"
            f"Телефон: {places[name]['phone']}\n"
            f"Сайт: {places[name]['url']}\n"
            f"Количество трасс: {places[name]['info']['trails']}\n"
            f"Самая длинная трасса: {places[name]['info']['max_length']} км\n"
            f"Общая протяженность трасс: {places[name]['info']['total_length']} км\n"
            f"Перепад высот: {places[name]['info']['vertical_drop']} м\n"
            f"Максимальная высота: {places[name]['info']['max_elevation']} м\n"
            f"Количество подъемников: {places[name]['info']['lifts']}\n"
            f"Тип подъемников: {places[name]['info']['type_lift']}\n"
        )
        bot.send_message(
            call.message.chat.id,
            text,
            parse_mode='Markdown',
            disable_web_page_preview=True,
            disable_notification=True,
        )
    elif 'get_trail' in call.data:
        name = call.data.split('&')[1]
        text = f'{name}'
        try:
            with open(f'trail_maps/{trail_maps[name]}', 'rb') as file:
                bot.send_photo(
                    call.message.chat.id,
                    photo=file,
                    caption=text,
                    disable_notification=True,
                )
        except FileNotFoundError as e:
            print(repr(e))
            bot.send_message(
                call.message.chat.id,
                'Упс.. что-то пошло не так',
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
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except ApiTelegramException as e:
        print(repr(e))


bot.polling()

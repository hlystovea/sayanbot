import logging
from logging.handlers import RotatingFileHandler
from os import environ
from typing import List

from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.exceptions import TelegramAPIError
from dotenv import load_dotenv
from pydantic.error_wrappers import ValidationError

from schema.resort import Resort
from store.mongo import MongoDB
from utils import weather

load_dotenv()

BOT_TOKEN = environ['BOT_TOKEN']
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
mongo = MongoDB()

console_out_hundler = logging.StreamHandler()
rotate_file_handler = RotatingFileHandler(
    'log.log',
    maxBytes=5000000,
    backupCount=2,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(funcName)s: %(message)s',
    handlers=[console_out_hundler, rotate_file_handler],
)


main_kbrd = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_kbrd.row('Показать список команд')

buttons = {
    1: ('Погода на склоне', 'weather'),
    2: ('Как проехать', 'coordinates'),
    3: ('Информация', 'info'),
    4: ('Карты склонов', 'trail_map'),
    5: ('Веб-камеры', 'webcam'),
}


def get_keyboard() -> types.InlineKeyboardMarkup:
    """
    Generate keyboard with list of buttons
    """
    keyboard = types.InlineKeyboardMarkup()
    for b in sorted(buttons):
        button = types.InlineKeyboardButton(
            buttons[b][0],
            callback_data=buttons[b][1])
        keyboard.add(button)
    return keyboard


async def send_keyboard_with_resorts(call: types.CallbackQuery, resorts: List[Resort]): # noqa
    keyboard = types.InlineKeyboardMarkup()
    for resort in resorts:
        button = types.InlineKeyboardButton(
            resort.name,
            callback_data=f'get_{call.data}&{resort.slug}',
        )
        keyboard.add(button)
    text = 'Выберите место:'
    await call.message.reply(
        text,
        reply_markup=keyboard,
        disable_notification=True,
    )


@dp.message_handler(commands=['start', 'help'])
async def start(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    text = ('Привет! Я бот, который поможет тебе найти информацию '
            'о горнолыжных курортах юга Сибири. Чтобы начать, нажмите '
            '*"Показать список команд"*')
    await message.reply(
        text,
        reply_markup=main_kbrd,
        parse_mode='Markdown',
        disable_notification=True,
    )


@dp.message_handler(content_types=['text'])
async def list_commands(message: types.Message):
    """
    This handler will be called when user sends text "показать список команд"
    """
    if message.text.lower() == 'показать список команд':
        keyboard = get_keyboard()
        text = 'Выберите команду:'
        await message.reply(
            text,
            reply_markup=keyboard,
            disable_notification=True,
        )
        await bot.delete_message(message.chat.id, message.message_id)


@dp.callback_query_handler(lambda callback_query: True)
async def callback_query_handler(call: types.CallbackQuery):
    """
    This handler will be called when user sends callback_query
    """
    try:
        if call.data in ('coordinates', 'info', 'trail_map'):
            resorts = await mongo.find_many_resorts(
                {call.data: {'$nin': [None, '', [], {}]}},
            )
            await send_keyboard_with_resorts(call, resorts)
        elif call.data == 'weather':
            resorts = await mongo.find_many_resorts(
                {'show_weather': True},
            )
            await send_keyboard_with_resorts(call, resorts)
        elif call.data == 'webcam':
            keyboard = types.InlineKeyboardMarkup()
            resorts = await mongo.find_many_resorts(
                {'webcam': {'$nin': [None, '']}}
            )
            for resort in resorts:
                button = types.InlineKeyboardButton(
                    resort.name,
                    url=resort.webcam,
                )
                keyboard.add(button)
            text = 'Веб-камеры ' + u'\U0001F3A5' + '\n'
            await bot.send_message(
                call.message.chat.id,
                text,
                parse_mode='Markdown',
                reply_markup=keyboard,
                disable_web_page_preview=True,
                disable_notification=True,
            )
        elif 'get_weather' in call.data:
            slug = call.data.split('&')[1]
            resort = await mongo.find_one_resort({'slug': slug})
            text = f'{resort.name}\n{weather(resort.coordinates)}'
            await call.message.reply(
                text,
                parse_mode='Markdown',
                disable_web_page_preview=True,
                disable_notification=True,
            )
        elif 'get_coordinates' in call.data:
            slug = call.data.split('&')[1]
            resort = await mongo.find_one_resort({'slug': slug})
            lat = resort.coordinates[0]
            lon = resort.coordinates[1]
            title = resort.name
            address = f'{lat}, {lon}'
            await bot.send_venue(
                call.message.chat.id,
                lat,
                lon,
                title,
                address,
                disable_notification=True,
            )
        elif 'get_info' in call.data:
            slug = call.data.split('&')[1]
            resort = await mongo.find_one_resort({'slug': slug})
            text = (
                f"*{resort.name}\n*"
                f"Телефон: {resort.phone}\n"
                f"Сайт: {resort.url}\n"
                f"Количество трасс: {resort.info.trails}\n"
                f"Самая длинная трасса: {resort.info.max_length} км\n"
                f"Общая протяженность трасс: {resort.info.total_length} км\n"
                f"Перепад высот: {resort.info.vertical_drop} м\n"
                f"Максимальная высота: {resort.info.max_elevation} м\n"
                f"Количество подъемников: {resort.info.lifts}\n"
                f"Тип подъемников: {resort.info.type_lift}\n"
            )
            await bot.send_message(
                call.message.chat.id,
                text,
                parse_mode='Markdown',
                disable_web_page_preview=True,
                disable_notification=True,
            )
        elif 'get_trail_map' in call.data:
            slug = call.data.split('&')[1]
            resort = await mongo.find_one_resort({'slug': slug})
            try:
                with open(f'trail_maps/{resort.trail_map}', 'rb') as file:
                    await bot.send_photo(
                        call.message.chat.id,
                        photo=file,
                        caption=resort.name,
                        disable_notification=True,
                    )
            except FileNotFoundError as error:
                logging.error(repr(error))
                await bot.send_message(
                    call.message.chat.id,
                    'Упс.. что-то пошло не так',
                    disable_notification=True,
                )
        else:
            text = 'Неизвестный запрос'
            logging.error(text)
            await bot.send_message(
                call.message.chat.id,
                text,
                disable_notification=True,
            )
    except ValidationError as error:
        logging.error(repr(error))
        await call.message.reply(
            'Упс.. что-то пошло не так',
            disable_notification=True,
        )
    try:
        await bot.delete_message(call.message.chat.id, call.message.message_id)
    except TelegramAPIError as error:
        logging.error(repr(error))


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

import logging
from logging.handlers import RotatingFileHandler
from os import environ
from typing import Dict, List

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.mongo import MongoStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.callback_data import CallbackData
from dotenv import load_dotenv
from pydantic.error_wrappers import ValidationError

from schema.resort import Resort
from schema.track import Track
from store.mongo import MongoDB
from utils.weather import get_current_weather

load_dotenv()


BOT_TOKEN = environ['BOT_TOKEN']
mongo = MongoDB()
storage = MongoStorage(
    host='mongodb',
    port=27017,
    db_name='sayanbot',
    username=environ['MONGO_INITDB_ROOT_USERNAME'],
    password=environ['MONGO_INITDB_ROOT_PASSWORD'],
)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=storage)

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


class TrackState(StatesGroup):
    waiting_for_track_save = State()
    waiting_for_track_name = State()
    waiting_for_track_region = State()
    waiting_for_track_description = State()
    waiting_for_track_choose = State()


track_cb = CallbackData('track', 'action', 'answer')

buttons = {
    1: ('Погода на склоне', 'weather'),
    2: ('Как проехать', 'coordinates'),
    3: ('Информация', 'info'),
    4: ('Карты склонов', 'trail_map'),
    5: ('Веб-камеры', 'webcam'),
    6: ('GPS-треки', 'tracks'),
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


@dp.message_handler(commands=['start', 'help'], state='*')
async def start(message: types.Message, state: FSMContext):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await state.finish()
    text = ('Привет! Я бот, который поможет тебе найти информацию '
            'о горнолыжных курортах юга Сибири. Чтобы начать, нажмите '
            '*"Показать список команд"*')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Показать список команд')
    await message.reply(
        text,
        reply_markup=markup,
        parse_mode='Markdown',
        disable_notification=True,
    )


@dp.message_handler(text=['Показать список команд'], state='*')
async def list_commands(message: types.Message, state: FSMContext):
    """
    This handler will be called when user sends text "показать список команд"
    """
    await state.finish()
    markup = get_keyboard()
    text = 'Выберите команду:'
    await message.answer(text, reply_markup=markup, disable_notification=True)
    await bot.delete_message(message.chat.id, message.message_id)


@dp.message_handler(content_types=['document'], state='*')
async def file_handler(message: types.File, state: FSMContext):
    """
    This handler will be called when the user sends a file
    """
    if message.document.file_name.split('.')[-1] == 'gpx':
        track = {
            'file_id': message.document.file_id,
            'unique_id': message.document.file_unique_id,
            'name': message.document.file_name,
            'size': message.document.file_size,
            'chat_id': message.chat.id,
        }
        await state.set_data(data=track)
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton(
                'Да',
                callback_data=track_cb.new(action='save', answer='yes'),
            ),
            types.InlineKeyboardButton(
                'Нет',
                callback_data=track_cb.new(action='save', answer='no'),
            ),
        )
        text = ('Добавить этот трек в список маршрутов? '
                'Он будет виден только в этом чате.')
        await message.reply(
            text,
            reply_markup=markup,
            disable_notification=True,
        )
        await TrackState.waiting_for_track_save.set()


@dp.callback_query_handler(
    track_cb.filter(action='save'),
    state=TrackState.waiting_for_track_save,
)
async def save_track_handler(
    query: types.CallbackQuery,
    callback_data: Dict[str, str],
    state: FSMContext,
):
    """
    This handler will be called when the user sets
    the waiting_for_track_save state
    """
    if callback_data['answer'] == 'no':
        await state.finish()
        return await bot.delete_message(
            query.message.chat.id,
            query.message.message_id,
        )

    resorts = await mongo.find_many_resorts(
            {'info': {'$nin': [None, '', [], {}]}},
    )
    markup = types.InlineKeyboardMarkup()
    for resort in resorts:
        button = types.InlineKeyboardButton(
            resort.name,
            callback_data=track_cb.new(action='region', answer=resort.slug),
        )
        markup.add(button)
    await query.message.edit_text(
        'Укажите регион катания:',
        reply_markup=markup,
    )
    await TrackState.waiting_for_track_region.set()


@dp.callback_query_handler(
    track_cb.filter(action='region'),
    state=TrackState.waiting_for_track_region,
)
async def set_track_region(
    query: types.CallbackQuery,
    callback_data: Dict[str, str],
    state: FSMContext,
):
    """
    This handler will be called when the user sets
    the waiting_for_track_region state
    """
    await state.update_data(region=callback_data['answer'])
    await query.message.edit_text(
        'Введите название маршрута. Например, "Ски-тур вокруг Боруса":'
    )
    await TrackState.waiting_for_track_name.set()


@dp.message_handler(state=TrackState.waiting_for_track_name)
async def set_track_name(message: types.Message, state: FSMContext):
    """
    This handler will be called when the user sets
    the waiting_for_track_name state
    """
    if len(message.text) > 40:
        return await message.answer(
            'Название не должно быть длинее 40 cимволов.',
        )
    await state.update_data(name=message.text)
    await message.answer(
        'Введите описание маршрута. Например, '
        '"24 км на лыжах вокруг хребта Борус (12.02.2021)":'
    )
    await TrackState.waiting_for_track_description.set()


@dp.message_handler(state=TrackState.waiting_for_track_description)
async def set_track_description(message: types.Message, state: FSMContext):
    """
    This handler will be called when the user sets
    the waiting_for_track_description state
    """
    await state.update_data(description=message.text)
    track = await state.get_data()
    try:
        await mongo.insert_track(Track(**track))
    except Exception as error:
        logging.error(repr(error))
        await message.answer('Упс.. что-то пошло не так.')
    else:
        await message.answer('Маршрут добавлен.')
    finally:
        await state.finish()


@dp.callback_query_handler(
    track_cb.filter(action='get'),
    state=TrackState.waiting_for_track_choose,
)
async def get_track(
    query: types.CallbackQuery,
    callback_data: Dict[str, str],
    state: FSMContext,
):
    """
    This handler will be called when the user sets
    the waiting_for_track_choose state
    """
    track = await mongo.find_one_track(
        {
            'unique_id': callback_data['answer'],
            'chat_id': query.message.chat.id,
        }
    )
    if track is None:
        logging.error(f'Track not found: unique_id {callback_data["answer"]}')
        return await query.message.edit_text('Упс.. Что-то пошло не так.')
    await query.message.answer_document(
        track.file_id,
        caption=f'*{track.name}:*\n{track.description}',
        disable_notification=True,
        parse_mode='Markdown',
    )
    await query.message.delete()
    await state.finish()


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
        elif call.data == 'tracks':
            tracks = await mongo.find_many_tracks(
                {
                    'chat_id': call.message.chat.id,
                }
            )
            if len(tracks) == 0:
                return await call.message.edit_text(
                    'Список маршрутов пуст. Вы можете загрузить свой маршрут '
                    'отправив gpx файл в этот чат.'
                )
            keyboard = types.InlineKeyboardMarkup()
            for track in tracks:
                button = types.InlineKeyboardButton(
                    track.name,
                    callback_data=track_cb.new(
                        action='get',
                        answer=track.unique_id
                    ),
                )
                keyboard.add(button)
            await call.message.edit_text(
                'Выберите маршрут:',
                reply_markup=keyboard,
            )
            await TrackState.waiting_for_track_choose.set()
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
            text = (f'{resort.name}\n'
                    f'{await get_current_weather(resort.coordinates)}')
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


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

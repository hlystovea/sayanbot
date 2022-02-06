import logging
from logging.handlers import RotatingFileHandler
from os import environ
from typing import Dict, List

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.mongo import MongoStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.callback_data import CallbackData
from pydantic import ValidationError

from db.mongo import MongoDB
from schema.resort import Resort
from schema.track import Track
from schema.weather import Weather
from utils.weather import get_current_weather, get_forecast_24h


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


class WeatherState(StatesGroup):
    waiting_for_weather_action = State()


track_cb = CallbackData('track', 'action', 'answer')
main_cb = CallbackData('main', 'action', 'answer')
weather_cb = CallbackData('weather', 'action', 'answer')


buttons = {
    1: ('Погода на склоне', 'weather'),
    2: ('Как проехать', 'coordinates'),
    3: ('Информация', 'info'),
    4: ('Карты склонов', 'trail_map'),
    5: ('Веб-камеры', 'webcam'),
    6: ('GPS-треки', 'tracks'),
}

weather_actions = {
    'current': 'Погода сейчас {temp}',
    'forecast_24h': 'Прогноз на завтра',
}


def get_start_keyboard() -> types.InlineKeyboardMarkup:
    """
    Generate keyboard with list of buttons
    """
    keyboard = types.InlineKeyboardMarkup()
    for _, b in buttons.items():
        button = types.InlineKeyboardButton(
            b[0],
            callback_data=main_cb.new(action=b[1], answer='_'),
        )
        keyboard.add(button)
    return keyboard


def get_keyboard_with_resorts(action: str, resorts: List[Resort]):
    markup = types.InlineKeyboardMarkup()
    for resort in resorts:
        button = types.InlineKeyboardButton(
            resort.name,
            callback_data=main_cb.new(action=action, answer=resort.slug),
        )
        markup.add(button)
    return markup


async def send_message_with_resorts(query: types.CallbackQuery, action: str):
    resorts = await mongo.find_many_resorts(
        {action: {'$nin': [None, '', [], {}, False]}},
    )
    if len(resorts) == 0:
        logging.error(f'Resorts not found. Action: {action}')
        return await query.message.edit_text('Упс.. что-то пошло не так')
    return await query.message.edit_text(
        'Выберите место:',
        reply_markup=get_keyboard_with_resorts(action, resorts),
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
    await message.answer(
        text,
        reply_markup=markup,
        parse_mode='Markdown',
        disable_notification=True,
    )


@dp.message_handler(text=['Показать список команд'], state='*')
async def list_commands(message: types.Message, state: FSMContext):
    """
    This handler will be called when user sends text "Показать список команд"
    """
    await state.finish()
    markup = get_start_keyboard()
    text = 'Выберите команду:'
    await message.answer(text, reply_markup=markup, disable_notification=True)


@dp.message_handler(content_types=['document'], state='*')
async def track_file_handler(message: types.File, state: FSMContext):
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
    await state.update_data(
        region=callback_data['answer'],
        parent_message_id=query.message.message_id,
    )
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
        return await message.reply(
            'Название не должно быть длинее 40 cимволов',
            disable_notification=True,
        )
    await state.update_data(name=message.text)
    data = await state.get_data()
    text = ('Введите описание маршрута. Например, '
            '"24 км на лыжах вокруг хребта Борус (12.02.2021)":')
    await bot.edit_message_text(
        text,
        chat_id=message.chat.id,
        message_id=data['parent_message_id'],
    )
    await message.delete()
    await TrackState.waiting_for_track_description.set()


@dp.message_handler(state=TrackState.waiting_for_track_description)
async def set_track_description(message: types.Message, state: FSMContext):
    """
    This handler will be called when the user sets
    the waiting_for_track_description state
    """
    await state.update_data(description=message.text)
    data = await state.get_data()
    try:
        await mongo.insert_track(Track(**data))
    except Exception as error:
        logging.error(repr(error))
        await message.answer('Упс.. что-то пошло не так')
    else:
        await bot.edit_message_text(
            'Маршрут добавлен.',
            message.chat.id,
            message_id=data['parent_message_id'],
        )
        await message.delete()
    finally:
        await state.finish()


@dp.callback_query_handler(main_cb.filter(action=['tracks', 'get_track']))
async def get_track_handler(
    query: types.CallbackQuery,
    callback_data: Dict[str, str],
):
    """
    This handler will be called when user sends
    callback_query with tracks or get_track action
    """

    action = callback_data['action']
    answer = callback_data['answer']

    if answer == '_':
        tracks = await mongo.find_many_tracks(
            {
                'chat_id': query.message.chat.id,
            },
        )
        if len(tracks) == 0:
            return await query.message.edit_text(
                'Список маршрутов пуст. Вы можете загрузить свой маршрут '
                'отправив gpx файл в этот чат.'
            )
        regions = [track.region for track in tracks]
        resorts = await mongo.find_many_resorts({'slug': {'$in': regions}})
        return await query.message.edit_text(
            'Выберите район катания:',
            reply_markup=get_keyboard_with_resorts(action, resorts),
        )

    if action == 'tracks':
        tracks = await mongo.find_many_tracks(
            {
                'region': answer,
                'chat_id': query.message.chat.id,
            }
        )
        markup = types.InlineKeyboardMarkup()
        for track in tracks:
            button = types.InlineKeyboardButton(
                track.name,
                callback_data=main_cb.new(
                    action='get_track',
                    answer=track.unique_id,
                ),
            )
            markup.add(button)
        return await query.message.edit_text(
            'Выберите маршрут:',
            reply_markup=markup,
        )

    track = await mongo.find_one_track(
        {
            'unique_id': answer,
            'chat_id': query.message.chat.id,
        },
    )
    if track is None:
        logging.error(f'Track not found: unique_id {answer}')
        return await query.message.edit_text('Упс.. Что-то пошло не так')
    await query.message.answer_document(
        track.file_id,
        caption=f'*{track.name}:*\n{track.description}',
        disable_notification=True,
        parse_mode='Markdown',
    )
    await query.message.delete()


@dp.callback_query_handler(
    weather_cb.filter(action='get_weather'),
    state=WeatherState.waiting_for_weather_action,
)
async def get_weather_handler(
    query: types.CallbackQuery,
    callback_data: Dict[str, str],
    state: FSMContext,
):
    """
    This handler will be called when the user sets
    the waiting_for_weather_action state
    """
    data = await state.get_data()

    if callback_data['answer'] == 'current':
        try:
            current_weather = Weather(**data['current_weather'])
            resort_name = data['resort']
        except (ValidationError, KeyError) as error:
            logging.error(repr(error))
            return await query.message.edit_text('Упс.. Что-то пошло не так')
        text = (f'{resort_name}\n'
                f'По данным [{current_weather.service}]({current_weather.url})'
                f' сейчас {current_weather}.')
        await query.message.edit_text(
            text,
            parse_mode='Markdown',
            disable_web_page_preview=True,
        )

    if callback_data['answer'] == 'forecast_24h':
        try:
            forecast_24h = await get_forecast_24h(
                coordinates=data['coordinates']
            )
            resort_name = data['resort']
        except (IndexError, KeyError) as error:
            logging.error(repr(error))
            return await query.message.edit_text('Упс.. Что-то пошло не так')
        text = (f'{resort_name}\n'
                f'По данным [{forecast_24h[12].service}]({forecast_24h[12].url})'  # noqa (E501)
                f' завтра в {forecast_24h[12].date.strftime("%H:%M")} будет '
                f'{forecast_24h[12]}.')
        await query.message.edit_text(
            text,
            parse_mode='Markdown',
            disable_web_page_preview=True,
        )
    await state.finish()


@dp.callback_query_handler(main_cb.filter(action='weather'), state='*')
async def weather_handler(
    query: types.CallbackQuery,
    callback_data: Dict[str, str],
    state: FSMContext,
):
    """
    This handler will be called when user sends
    callback_query with weather action
    """
    if callback_data['answer'] == '_':
        state.finish()
        return await send_message_with_resorts(query, callback_data['action'])

    resort = await mongo.find_one_resort({'slug': callback_data['answer']})
    if not resort:
        logging.error(f'Resort not found. Slug: {callback_data["answer"]}')
        return await query.message.edit_text('Упс.. что-то пошло не так')

    current_weather = await get_current_weather(resort.coordinates)
    data = {
        'resort': resort.name,
        'coordinates': resort.coordinates,
        'current_weather': current_weather.dict(),
    }
    await state.set_data(data=data)

    markup = types.InlineKeyboardMarkup()
    for slug, text in weather_actions.items():
        button = types.InlineKeyboardButton(
            text.format(temp=f'{current_weather.temp:+.1f} \xb0С'),
            callback_data=weather_cb.new(
                action='get_weather',
                answer=slug,
            ),
        )
        markup.add(button)
    markup.add(
        types.InlineKeyboardButton(
            'Назад',
            callback_data=main_cb.new(
                action='weather',
                answer='_',
            ),
        )
    )
    await query.message.edit_text(
        'Выберите действие:',
        reply_markup=markup,
    )
    await WeatherState.waiting_for_weather_action.set()


@dp.callback_query_handler(
    main_cb.filter(
        action=['info', 'webcam', 'trail_map', 'coordinates']
    ),
)
async def resort_information_handler(
    query: types.CallbackQuery,
    callback_data: Dict[str, str],
):
    """
    This handler will be called when user sends
    callback_query with weather/info/webcam/trail_map/coordinates action
    """

    action = callback_data['action']
    answer = callback_data['answer']

    if answer == '_':
        return await send_message_with_resorts(query, action)

    resort = await mongo.find_one_resort({'slug': answer})
    if not resort:
        logging.error(f'Resort not found. Slug: {answer}')
        return await query.message.edit_text('Упс.. что-то пошло не так')

    if action == 'info':
        await query.message.edit_text(
            resort.get_info(),
            parse_mode='Markdown',
            disable_web_page_preview=True,
        )
    if action == 'webcam':
        await query.message.edit_text(
            resort.webcam,
            disable_web_page_preview=True,
        )
    if action == 'trail_map':
        try:
            with open(f'trail_maps/{resort.trail_map}', 'rb') as file:
                await query.message.answer_photo(
                    photo=file,
                    caption=resort.name,
                    disable_notification=True,
                )
                await query.message.delete()
        except FileNotFoundError as error:
            logging.error(repr(error))
            await query.message.edit_text('Упс.. что-то пошло не так')
    if action == 'coordinates':
        await query.message.answer_venue(
            latitude=resort.coordinates[0],
            longitude=resort.coordinates[1],
            title=resort.name,
            address=f'{resort.coordinates[0]}, {resort.coordinates[1]}',
            disable_notification=True,
        )
        await query.message.delete()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

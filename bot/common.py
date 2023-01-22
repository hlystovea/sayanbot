from aiogram.types import CallbackQuery
from collections import namedtuple

from bot.markups import get_keyboard_with_resorts
from db.mongo import mongo
from logger import logger


Messages = namedtuple(
    typename='Messages',
    field_names=[
        'welcome_message',
        'choose_command',
        'choose_resorts',
        'show_commands_list',
        'error',
        'service_unavailable',
        'track_list_empty',
        'choose_track',
        'save_new_track_question',
        'choose_track_region',
        'input_track_name',
        'input_track_description',
        'max_name_lenght',
        'saved',
        'current_weather',
        'forecast',
    ]
)

MSG = Messages(
    ('Привет! Я бот, который поможет тебе найти информацию '
     'о горнолыжных курортах юга Сибири. Чтобы начать, нажмите '
     '*`Показать список команд`*'),
    'Выберите команду:',
    'Выберите место:',
    'Показать список команд',
    'Упс.. кажется, что-то сломалось. Мы уже в курсе, скоро всё починим.',
    'Сторонний сервис погоды недоступен. Попробуйте позже.',
    ('Список маршрутов пуст. Вы можете загрузить свой маршрут '
     'отправив gpx файл в этот чат.'),
    'Выберите маршрут:',
    ('Добавить этот трек в список маршрутов? '
     'Он будет виден только в этом чате.'),
    'Выберите регион катания:',
    'Введите название маршрута. Например, "Ски-тур вокруг Боруса"',
    ('Введите описание маршрута. Например, '
     '"24 км на лыжах вокруг хребта Борус (12.12.2012)":'),
    'Название не должно быть длинее {} cимволов',
    'Сохранено.',
    '{}\nПо данным [{}]({}) сейчас {}.',
    '{}\nПо данным [{}]({}) завтра в {} будет {}.',
)


async def send_message_with_resorts(query: CallbackQuery, action: str):
    resorts = await mongo.find_many_resorts(
        {action: {'$nin': [None, '', [], {}, False]}}
    )

    if len(resorts) == 0:
        logger.error(f'Resorts not found. Action: {action}')
        return await query.message.edit_text(MSG.error)

    return await query.message.edit_text(
        MSG.choose_resorts,
        reply_markup=get_keyboard_with_resorts(action, resorts)
    )

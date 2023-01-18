from aiogram.types import CallbackQuery

from bot.markups import get_keyboard_with_resorts
from db.mongo import mongo
from logger import logger


async def send_message_with_resorts(query: CallbackQuery, action: str):
    resorts = await mongo.find_many_resorts(
        {action: {'$nin': [None, '', [], {}, False]}}
    )

    if len(resorts) == 0:
        logger.error(f'Resorts not found. Action: {action}')
        return await query.message.edit_text('Упс.. что-то пошло не так')

    return await query.message.edit_text(
        'Выберите место:',
        reply_markup=get_keyboard_with_resorts(action, resorts)
    )

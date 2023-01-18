from aiogram import Dispatcher
from aiogram.types import CallbackQuery

from bot.markups import (get_keyboard_with_resorts, get_keyboard_with_tracks,
                         main_cb, resort_cb, track_cb)
from db.mongo import mongo
from logger import logger


def register_get_track_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        entry_point,
        main_cb.filter(action='tracks')
    )
    dp.register_callback_query_handler(
        region_choice_handler,
        resort_cb.filter(action='tracks')
    )
    dp.register_callback_query_handler(
        track_choice_handler,
        track_cb.filter(action='tracks')
    )
    dp.register_callback_query_handler(
        entry_point,
        track_cb.filter(action='back')
    )


async def entry_point(
    query: CallbackQuery,
    callback_data: dict[str, str]
):
    """
    This handler will be called first when the user sends
    callback with tracks action
    """
    tracks = await mongo.find_many_tracks({'chat_id': query.message.chat.id})

    if len(tracks) == 0:
        return await query.message.edit_text(
            'Список маршрутов пуст. Вы можете загрузить свой маршрут '
            'отправив gpx файл в этот чат.'
        )

    regions = [track.region for track in tracks]
    resorts = await mongo.find_many_resorts({'slug': {'$in': regions}})

    await query.message.edit_text(
        'Выберите район катания:',
        reply_markup=get_keyboard_with_resorts('tracks', resorts)
    )


async def region_choice_handler(
    query: CallbackQuery,
    callback_data: dict[str, str]
):
    """
    This handler will be called when user sends resort callback
    """
    tracks = await mongo.find_many_tracks(
        {
            'region': callback_data['answer'],
            'chat_id': query.message.chat.id,
        }
    )

    await query.message.edit_text(
        'Выберите маршрут:',
        reply_markup=get_keyboard_with_tracks(tracks)
    )


async def track_choice_handler(
    query: CallbackQuery,
    callback_data: dict[str, str]
):
    """
    This handler will be called when user sends track callback
    """
    track = await mongo.find_one_track(
        {
            'unique_id': callback_data['answer'],
            'chat_id': query.message.chat.id,
        }
    )

    if track is None:
        logger.error(f'Track not found: unique_id {callback_data["answer"]}')
        return await query.message.edit_text('Упс.. Что-то пошло не так')

    await query.message.answer_document(
        track.file_id,
        caption=f'*{track.name}:*\n{track.description}',
        disable_notification=True,
        parse_mode='Markdown'
    )
    await query.message.delete()

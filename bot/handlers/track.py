from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import (CallbackQuery, File, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)

from bot.markups import (get_keyboard_with_resorts, get_keyboard_with_tracks,
                         get_track_save_keyboard, main_cb, track_cb)
from db.mongo import mongo
from logger import logger
from schema.track import Track


class TrackState(StatesGroup):
    waiting_for_track_save = State()
    waiting_for_track_name = State()
    waiting_for_track_region = State()
    waiting_for_track_description = State()


def register_track_handlers(dp: Dispatcher):
    dp.register_message_handler(track_file_handler, content_types=['document'], state='*')
    dp.register_message_handler(set_track_name, state=TrackState.waiting_for_track_name)
    dp.register_message_handler(set_track_description, state=TrackState.waiting_for_track_description)
    dp.register_callback_query_handler(
        save_track_handler,
        track_cb.filter(action='save'),
        state=TrackState.waiting_for_track_save,
    )
    dp.register_callback_query_handler(
        set_track_region,
        track_cb.filter(action='region'),
        state=TrackState.waiting_for_track_region,
    )
    dp.register_callback_query_handler(
        get_track_handler,
        main_cb.filter(action='tracks')
    )
    dp.register_callback_query_handler(
        region_choice_handler,
        track_cb.filter(action='region_choice')
    )
    dp.register_callback_query_handler(
        track_choice_handler,
        track_cb.filter(action='track_choice')
    )


async def track_file_handler(message: File, state: FSMContext):
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

        text = ('Добавить этот трек в список маршрутов? '
                'Он будет виден только в этом чате.')
        await message.reply(
            text,
            reply_markup=get_track_save_keyboard(),
            disable_notification=True
        )
        await TrackState.waiting_for_track_save.set()


async def save_track_handler(
    query: CallbackQuery,
    callback_data: dict[str, str],
    state: FSMContext
):
    """
    This handler will be called when the user sets
    the waiting_for_track_save state
    """
    match callback_data['answer']:
        case 'no':
            await state.finish()
            return await query.bot.delete_message(
                query.message.chat.id,
                query.message.message_id
            )

        case 'yes':
            resorts = await mongo.find_many_resorts(
                    {'info': {'$nin': [None, '', [], {}]}}
                )

            await query.message.edit_text(
                'Укажите регион катания:',
                reply_markup=get_keyboard_with_resorts(track_cb, 'region', resorts)
            )
            await TrackState.waiting_for_track_region.set()


async def set_track_region(
    query: CallbackQuery,
    callback_data: dict[str, str],
    state: FSMContext
):
    """
    This handler will be called when the user sets
    the waiting_for_track_region state
    """
    await state.update_data(
        region=callback_data['answer'],
        parent_message_id=query.message.message_id
    )
    await query.message.edit_text(
        'Введите название маршрута. Например, "Ски-тур вокруг Боруса":'
    )
    await TrackState.waiting_for_track_name.set()


async def set_track_name(message: Message, state: FSMContext):
    """
    This handler will be called when the user sets
    the waiting_for_track_name state
    """
    if len(message.text) > 40:
        return await message.reply(
            'Название не должно быть длинее 40 cимволов',
            disable_notification=True
        )

    await state.update_data(name=message.text)
    data = await state.get_data()

    text = ('Введите описание маршрута. Например, '
            '"24 км на лыжах вокруг хребта Борус (12.02.2021)":')
    await message.bot.edit_message_text(
        text,
        chat_id=message.chat.id,
        message_id=data['parent_message_id']
    )

    await message.delete()
    await TrackState.waiting_for_track_description.set()


async def set_track_description(message: Message, state: FSMContext):
    """
    This handler will be called when the user sets
    the waiting_for_track_description state
    """
    await state.update_data(description=message.text)
    data = await state.get_data()

    try:
        await mongo.insert_track(Track(**data))
    except Exception as error:
        logger.error(repr(error))
        await message.answer('Упс.. что-то пошло не так')
    else:
        await message.bot.edit_message_text(
            'Маршрут добавлен.',
            message.chat.id,
            message_id=data['parent_message_id']
        )
        await message.delete()
    finally:
        await state.finish()


async def get_track_handler(
    query: CallbackQuery,
    callback_data: dict[str, str]
):
    """
    This handler will be called when user sends
    callback_query with tracks action
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
        reply_markup=get_keyboard_with_resorts(track_cb, 'region_choice', resorts)
    )


async def region_choice_handler(
    query: CallbackQuery,
    callback_data: dict[str, str]
):
    """
    This handler will be called when user sends
    callback_query region_choice action
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
    This handler will be called when user sends
    callback_query track_choice action
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

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.common import MSG
from bot.markups import (get_keyboard_with_resorts, get_track_save_keyboard,
                         resort_cb, track_cb)
from db.mongo import mongo
from logger import logger
from schemes.track import Track


MAX_TRACK_NAME_LENGHT = 40


class TrackState(StatesGroup):
    waiting_for_track_save = State()
    waiting_for_track_name = State()
    waiting_for_track_region = State()
    waiting_for_track_description = State()


def register_save_track_handlers(dp: Dispatcher):
    dp.register_message_handler(
        entry_point,
        content_types=['document'],
        state='*'
    )
    dp.register_callback_query_handler(
        save_track_handler,
        track_cb.filter(action='save_track'),
        state=TrackState.waiting_for_track_save
    )
    dp.register_callback_query_handler(
        set_track_region,
        resort_cb.filter(action='save_track'),
        state=TrackState.waiting_for_track_region
    )
    dp.register_callback_query_handler(
        back_button_handler,
        track_cb.filter(action='back'),
        state=TrackState.waiting_for_track_region
    )
    dp.register_message_handler(
        set_track_name,
        state=TrackState.waiting_for_track_name
    )
    dp.register_message_handler(
        set_track_description,
        state=TrackState.waiting_for_track_description
    )


async def add_file_info_to_state(message: Message, state: FSMContext):
    await state.finish()

    track = {
        'file_id': message.document.file_id,
        'unique_id': message.document.file_unique_id,
        'name': message.document.file_name,
        'size': message.document.file_size,
        'chat_id': message.chat.id,
    }

    await state.set_data(data=track)


async def entry_point(message: Message, state: FSMContext):
    """
    This handler will be called when the user sends a file
    """
    if message.document.file_name.split('.')[-1] == 'gpx':
        await add_file_info_to_state(message, state)

        await message.reply(
            MSG.save_new_track_question,
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
    match callback_data['answer']:  # noqa(E999)
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
                MSG.choose_track_region,
                reply_markup=get_keyboard_with_resorts(
                    callback_data['action'], resorts, track_cb
                )
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
    await query.message.edit_text(MSG.input_track_name)
    await TrackState.waiting_for_track_name.set()


async def set_track_name(message: Message, state: FSMContext):
    """
    This handler will be called when the user sets
    the waiting_for_track_name state
    """
    if len(message.text) > MAX_TRACK_NAME_LENGHT:
        return await message.reply(
            MSG.max_name_lenght.format(MAX_TRACK_NAME_LENGHT),
            disable_notification=True
        )

    await state.update_data(name=message.text)
    data = await state.get_data()

    await message.bot.edit_message_text(
        MSG.input_track_description,
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
        await message.answer(MSG.error)

    else:
        await message.bot.edit_message_text(
            MSG.saved,
            message.chat.id,
            message_id=data['parent_message_id']
        )
        await message.delete()

    await state.finish()


async def back_button_handler(
    query: CallbackQuery,
    callback_data: dict[str, str]
):
    """
    This handler will be called when user sends callback with back action
    """
    await query.message.edit_text(
        MSG.save_new_track_question,
        reply_markup=get_track_save_keyboard()
    )

    await TrackState.waiting_for_track_save.set()

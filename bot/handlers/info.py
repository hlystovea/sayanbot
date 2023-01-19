from aiogram import Dispatcher
from aiogram.types import CallbackQuery

from bot.common import send_message_with_resorts
from bot.markups import main_cb, resort_cb
from db.mongo import mongo
from logger import logger
from schemes.resort import Resort

INFO_CMD = [
    'info',
    'webcam',
    'trail_map',
    'coordinates',
]


def register_info_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        entry_point,
        main_cb.filter(action=INFO_CMD)
    )
    dp.register_callback_query_handler(
        resort_information_handler,
        resort_cb.filter(action=INFO_CMD)
    )


async def entry_point(
    query: CallbackQuery,
    callback_data: dict[str, str]
):
    """
    This handler will be called first when the user
    sends a callback with the info/webcam/trail_map/coordinates action
    """
    await send_message_with_resorts(query, callback_data['action'])


async def send_message_with_info(
    query: CallbackQuery,
    action: str,
    resort: Resort
):
    match action:  # noqa(E501)
        case 'info':
            await query.message.edit_text(
                resort.get_info(),
                parse_mode='Markdown',
                disable_web_page_preview=True
            )

        case 'webcam':
            await query.message.edit_text(
                resort.webcam,
                disable_web_page_preview=True
            )

        case 'trail_map':
            try:
                with open(f'trail_maps/{resort.trail_map}', 'rb') as file:
                    await query.message.answer_photo(
                        photo=file,
                        caption=resort.name,
                        disable_notification=True
                    )
                    await query.message.delete()
            except FileNotFoundError as error:
                logger.error(repr(error))
                await query.message.edit_text('Упс.. что-то пошло не так')

        case 'coordinates':
            await query.message.answer_venue(
                latitude=resort.coordinates[0],
                longitude=resort.coordinates[1],
                title=resort.name,
                address=f'{resort.coordinates[0]}, {resort.coordinates[1]}',
                disable_notification=True
            )
            await query.message.delete()

        case _:
            logger.error(f'Unknown action: {action}')
            await query.message.edit_text('Упс.. что-то пошло не так')


async def resort_information_handler(
    query: CallbackQuery,
    callback_data: dict[str, str]
):
    """
    This handler will be called when user sends callback with
    info/webcam/trail_map/coordinates action and resort slug in answer
    """
    action = callback_data['action']
    answer = callback_data['answer']

    resort = await mongo.find_one_resort({'slug': answer})

    if not resort:
        logger.error(f'Resort not found. Slug: {answer}')
        return await query.message.edit_text('Упс.. что-то пошло не так')

    await send_message_with_info(query, action, resort)

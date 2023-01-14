from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardMarkup

from bot.markups import get_main_keyboard, get_keyboard_with_resorts, main_cb
from db.mongo import mongo
from logger import logger
from schema.resort import Resort


def register_core_handlers(dp: Dispatcher):
    dp.register_message_handler(start, commands=['start', 'help'], state='*')
    dp.register_message_handler(list_commands, text=['Показать список команд'], state='*')  # noqa (E501)
    dp.register_callback_query_handler(list_commands, main_cb.filter(action='back'), state='*')  # noqa (E501)
    dp.register_callback_query_handler(
        resort_information_handler,
        main_cb.filter(action=['info', 'webcam', 'trail_map', 'coordinates'])
    )


async def send_message_with_resorts(query: CallbackQuery, action: str):
    resorts = await mongo.find_many_resorts(
        {action: {'$nin': [None, '', [], {}, False]}}
    )

    if len(resorts) == 0:
        logger.error(f'Resorts not found. Action: {action}')
        return await query.message.edit_text('Упс.. что-то пошло не так')

    return await query.message.edit_text(
        'Выберите место:',
        reply_markup=get_keyboard_with_resorts(main_cb, action, resorts)
    )


async def send_message_with_info(
    query: CallbackQuery, action: str, resort: Resort
):
    match action:
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


async def start(message: Message, state: FSMContext):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await state.finish()

    text = ('Привет! Я бот, который поможет тебе найти информацию '
            'о горнолыжных курортах юга Сибири. Чтобы начать, нажмите '
            '*"Показать список команд"*')
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Показать список команд')

    await message.answer(
        text,
        reply_markup=markup,
        parse_mode='Markdown',
        disable_notification=True
    )


async def list_commands(message: Message, state: FSMContext):
    """
    This handler will be called when user sends text "Показать список команд"
    """
    await state.finish()

    await message.answer(
        'Выберите команду:',
        reply_markup=get_main_keyboard(),
        disable_notification=True
    )


async def resort_information_handler(
    query: CallbackQuery,
    callback_data: dict[str, str]
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
        logger.error(f'Resort not found. Slug: {answer}')
        return await query.message.edit_text('Упс.. что-то пошло не так')

    await send_message_with_info(query, action, resort)
 
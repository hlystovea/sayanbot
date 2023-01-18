from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardMarkup

from bot.markups import get_main_keyboard, resort_cb


def register_main_handlers(dp: Dispatcher):
    dp.register_message_handler(
        start_command_handler,
        commands=['start', 'help'],
        state='*'
    )
    dp.register_message_handler(
        list_commands_button_handler,
        text=['Показать список команд'],
        state='*'
    )
    dp.register_callback_query_handler(
        back_button_handler,
        resort_cb.filter(action='back'),
        state='*'
    )


async def start_command_handler(message: Message, state: FSMContext):
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


async def list_commands_button_handler(message: Message, state: FSMContext):
    """
    This handler will be called when user sends text `Показать список команд`
    """
    await state.finish()

    await message.answer(
        'Выберите команду:',
        reply_markup=get_main_keyboard(),
        disable_notification=True
    )


async def back_button_handler(
    query: CallbackQuery,
    callback_data: dict[str, str],
    state: FSMContext
):
    """
    This handler will be called when user sends callback with back action
    """
    await state.finish()

    await query.message.edit_text(
        'Выберите команду:',
        reply_markup=get_main_keyboard()
    )

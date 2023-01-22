import logging

from aiogram import Dispatcher
from aiogram.types import Update
from aiogram.utils.exceptions import BotBlocked

logger = logging.getLogger('__name__')


def register_exceptions_handlers(dp: Dispatcher):
    dp.register_errors_handler(error_bot_blocked, exception=BotBlocked)


async def error_bot_blocked(update: Update, exception: BotBlocked):
    logger.error(
        f'Bot was blocked by user with id {update.message.from_user.id}.'
    )
    return True

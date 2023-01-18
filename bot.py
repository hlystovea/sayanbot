import asyncio
from os import environ

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.mongo import MongoStorage
from aiogram.types import BotCommand

from bot.handlers.info import register_info_handlers
from bot.handlers.main import register_main_handlers
from bot.handlers.get_track import register_get_track_handlers
from bot.handlers.save_track import register_save_track_handlers
from bot.handlers.weather import register_weather_handlers


BOT_TOKEN = environ['BOT_TOKEN']

storage = MongoStorage(
    host='mongodb',
    port=27017,
    db_name='sayanbot',
    username=environ['MONGO_INITDB_ROOT_USERNAME'],
    password=environ['MONGO_INITDB_ROOT_PASSWORD'],
)


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(bot, storage=storage)

    commands = [
        BotCommand(command='/start', description='начать'),
        BotCommand(command='/help', description='помощь'),
        BotCommand(command='/menu', description='открыть меню')
    ]
    await bot.set_my_commands(commands)

    register_info_handlers(dp)
    register_main_handlers(dp)
    register_get_track_handlers(dp)
    register_save_track_handlers(dp)
    register_weather_handlers(dp)

    await dp.start_polling()


if __name__ == '__main__':
    asyncio.run(main())

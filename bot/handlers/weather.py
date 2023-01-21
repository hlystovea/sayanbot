import logging
from typing import Any

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import CallbackQuery
from pydantic import ValidationError

from bot.common import send_message_with_resorts
from bot.markups import get_forecast_keyboard, main_cb, resort_cb, weather_cb
from db.mongo import mongo
from schemes.weather import Weather
from utils.weather.weather import get_current_weather, get_forecast


class WeatherState(StatesGroup):
    waiting_for_weather_action = State()


def register_weather_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        entry_point,
        main_cb.filter(action='weather'),
        state='*'
    )
    dp.register_callback_query_handler(
        weather_handler,
        resort_cb.filter(action='weather'),
        state='*'
    )
    dp.register_callback_query_handler(
        forecast_handler,
        weather_cb.filter(action='forecast'),
        state=WeatherState.waiting_for_weather_action
    )
    dp.register_callback_query_handler(
        entry_point,
        weather_cb.filter(action='back'),
        state=WeatherState.waiting_for_weather_action
    )


async def entry_point(
    query: CallbackQuery,
    callback_data: dict[str, str],
    state: FSMContext
):
    """
    This handler will be called first when the user
    sends a callback with the `weather` or `back` action
    """
    await state.finish()
    await send_message_with_resorts(query, 'weather')


async def weather_handler(
    query: CallbackQuery,
    callback_data: dict[str, str],
    state: FSMContext
):
    """
    This handler will be called when user sends callback with `weather` action
    """
    await state.finish()
    resort = await mongo.find_one_resort({'slug': callback_data['answer']})

    if not resort:
        logging.error(f'Resort not found. Slug: {callback_data["answer"]}')
        return await query.message.edit_text('Упс.. что-то пошло не так')

    current_weather = await get_current_weather(resort.coordinates)

    if not current_weather:
        return await query.message.edit_text(
            'Сервис погоды не доступен, попробуйте позднее'
        )

    data = {
        'resort': resort.name,
        'coordinates': resort.coordinates,
        'current_weather': current_weather.dict(),
    }

    await state.set_data(data=data)

    await query.message.edit_text(
        'Выберите действие:',
        reply_markup=get_forecast_keyboard(current_weather),
    )

    await WeatherState.waiting_for_weather_action.set()


async def send_current_weather(query: CallbackQuery, data: dict[str, Any]):
    try:
        current_weather = Weather(**data['current_weather'])
        resort_name = data['resort']

        text = (f'{resort_name}\nПо данным '
                f'[{current_weather.service}]({current_weather.url}) '
                f'сейчас {current_weather}.')

    except (AttributeError, KeyError, ValidationError) as error:
        logging.error(repr(error))
        return await query.message.edit_text('Упс.. Что-то пошло не так')

    await query.message.edit_text(
        text,
        parse_mode='Markdown',
        disable_web_page_preview=True,
    )


async def send_forecast_24h(query: CallbackQuery, data: dict[str, Any]):
    try:
        forecast = await get_forecast(coordinates=data['coordinates'])

        if not forecast:
            return await query.message.edit_text('Сервис погоды недоступен')

        text = (f'{data["resort"]}\nПо данным '
                f'[{forecast[12].service}]({forecast[12].url}) '
                f'завтра в {forecast[12].date.strftime("%H:%M")} будет '
                f'{forecast[12]}.')

    except (AttributeError, IndexError, KeyError) as error:
        logging.error(repr(error))
        return await query.message.edit_text('Упс.. Что-то пошло не так')

    await query.message.edit_text(
        text,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )


async def forecast_handler(
    query: CallbackQuery,
    callback_data: dict[str, str],
    state: FSMContext
):
    """
    This handler will be called when the user sets
    the `waiting_for_weather_action` state
    """
    data = await state.get_data()

    match callback_data['answer']:  # noqa(E999)
        case 'current':
            await send_current_weather(query, data)
        case 'forecast_24h':
            await send_forecast_24h(query, data)

    await state.finish()

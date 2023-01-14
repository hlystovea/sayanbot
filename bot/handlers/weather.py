import logging

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import CallbackQuery
from pydantic import ValidationError

from bot.handlers.core import send_message_with_resorts
from bot.markups import get_forecast_keyboard, main_cb, weather_cb
from db.mongo import mongo
from schema.weather import Weather
from utils.weather import get_current_weather, get_forecast_24h


class WeatherState(StatesGroup):
    waiting_for_weather_action = State()


def register_weather_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        weather_handler,
        main_cb.filter(action='weather'),
        state='*'
    )
    dp.register_callback_query_handler(
        forecast_handler,
        weather_cb.filter(action='forecast'),
        state=WeatherState.waiting_for_weather_action,
    )


async def weather_handler(
    query: CallbackQuery,
    callback_data: dict[str, str],
    state: FSMContext,
):
    """
    This handler will be called when user sends
    callback_query with weather action
    """
    if callback_data['answer'] == '_':
        await state.finish()
        return await send_message_with_resorts(query, callback_data['action'])

    resort = await mongo.find_one_resort({'slug': callback_data['answer']})

    if not resort:
        logging.error(f'Resort not found. Slug: {callback_data["answer"]}')
        return await query.message.edit_text('Упс.. что-то пошло не так')

    current_weather = await get_current_weather(resort.coordinates)

    data = {
        'resort': resort.name,
        'coordinates': resort.coordinates,
        'current_weather': current_weather.dict(),
    }

    await state.set_data(data=data)

    await query.message.edit_text(
        'Выберите действие:',
        reply_markup=await get_forecast_keyboard(current_weather),
    )

    await WeatherState.waiting_for_weather_action.set()


async def forecast_handler(
    query: CallbackQuery,
    callback_data: dict[str, str],
    state: FSMContext,
):
    """
    This handler will be called when the user sets
    the waiting_for_weather_action state
    """
    data = await state.get_data()

    if callback_data['answer'] == 'current':
        try:
            current_weather = Weather(**data['current_weather'])
            resort_name = data['resort']
        except (ValidationError, KeyError) as error:
            logging.error(repr(error))
            return await query.message.edit_text('Упс.. Что-то пошло не так')
        text = (f'{resort_name}\n'
                f'По данным [{current_weather.service}]({current_weather.url})'
                f' сейчас {current_weather}.')
        await query.message.edit_text(
            text,
            parse_mode='Markdown',
            disable_web_page_preview=True,
        )

    if callback_data['answer'] == 'forecast_24h':
        try:
            forecast_24h = await get_forecast_24h(
                coordinates=data['coordinates']
            )
            resort_name = data['resort']
        except (IndexError, KeyError) as error:
            logging.error(repr(error))
            return await query.message.edit_text('Упс.. Что-то пошло не так')
        text = (f'{resort_name}\n'
                f'По данным [{forecast_24h[12].service}]({forecast_24h[12].url})'  # noqa (E501)
                f' завтра в {forecast_24h[12].date.strftime("%H:%M")} будет '
                f'{forecast_24h[12]}.')
        await query.message.edit_text(
            text,
            parse_mode='Markdown',
            disable_web_page_preview=True,
        )

    await state.finish()

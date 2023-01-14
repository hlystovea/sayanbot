from aiogram.utils.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from schema.resort import Resort
from schema.weather import Weather


MAIN_MENU_BUTTONS = {
    'weather': 'Погода на склоне',
    'coordinates': 'Как проехать',
    'info': 'Информация',
    'trail_map': 'Карты склонов',
    'webcam': 'Веб-камеры',
    'tracks': 'GPS-треки',
}


FORECAST_BUTTONS = {
    'current': 'Погода сейчас {temp}',
    'forecast_24h': 'Прогноз на завтра',
}


main_cb = CallbackData('main', 'action', 'answer')
track_cb = CallbackData('track', 'action', 'answer')
weather_cb = CallbackData('weather', 'action', 'answer')


def get_main_keyboard() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()

    for action, text in MAIN_MENU_BUTTONS.items():
        button = InlineKeyboardButton(
            text,
            callback_data=main_cb.new(action=action, answer='_'),
        )
        markup.add(button)

    return markup


def get_keyboard_with_resorts(
    callback: CallbackData, action: str, resorts: list[Resort]
) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()

    for resort in resorts:
        button = InlineKeyboardButton(
            resort.name,
            callback_data=callback.new(action=action, answer=resort.slug),
        )
        markup.add(button)

    markup.add(
        InlineKeyboardButton(
            'Назад',
            callback_data=callback.new(action='back', answer='_')
        )
    )

    return markup


def get_forecast_keyboard(weather: Weather) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()

    for answer, text in FORECAST_BUTTONS.items():
        button = InlineKeyboardButton(
            text.format(temp=f'{weather.temp:+.1f} \xb0С'),
            callback_data=weather_cb.new(action='forecast', answer=answer)
        )
        markup.add(button)

    markup.add(
        InlineKeyboardButton(
            'Назад',
            callback_data=main_cb.new(action='weather', answer='_')
        )
    )

    return markup


def get_track_save_keyboard() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()

    markup.row(
        InlineKeyboardButton(
            'Да',
            callback_data=track_cb.new(action='save', answer='yes'),
        ),
        InlineKeyboardButton(
            'Нет',
            callback_data=track_cb.new(action='save', answer='no'),
        ),
    )

    return markup


def get_keyboard_with_tracks(tracks) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()

    for track in tracks:
        button = InlineKeyboardButton(
            track.name,
            callback_data=track_cb.new(
                action='track_choice',
                answer=track.unique_id,
            )
        )
        markup.add(button)

    return markup

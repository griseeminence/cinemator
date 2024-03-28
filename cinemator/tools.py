# Отдельный декоратор для логгирования
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def debug_requests(f):
    from logging import getLogger
    logger = getLogger(__name__)

    def inner(*args, **kwargs):
        try:
            logger.info(f'Обращение в функцию {__name__}')
            return f(*args, **kwargs)
        except Exception as e:
            logger.exception(f'Ошибка в обработчике {__name__}')
            raise

    return inner


# Вызываемая клавиатура
def get_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("Find Movie", callback_data="ask_movie_name")],
            [InlineKeyboardButton("Random Movie", callback_data="random_movie")],
            [InlineKeyboardButton("Favorite Movie", callback_data="favorite_movie")],
            [InlineKeyboardButton("Movie to watch", callback_data="movie_to_watch")],
        ],
    )
# Отдельный декоратор для логгирования
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
page_number = None

def logger_in_out(f):
    from logging import getLogger
    logger = getLogger(__name__)

    def wrap(*args, **kwargs):
        try:
            logger.info(f'Обращение в функцию {__name__}')
            return f(*args, **kwargs)
        except Exception as e:
            logger.exception(f'Ошибка в обработчике {__name__}')
            raise

    return wrap


# Вызываемая клавиатура
def get_main_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("Find Movie", callback_data="ask_movie_name")],
            [InlineKeyboardButton("Random Movie", callback_data="random_movie")],
            [InlineKeyboardButton("Favorite Movie", callback_data="favorite_movie")],
            [InlineKeyboardButton("Movie to watch", callback_data="movie_to_watch")],
        ],
    )


def get_save_movie_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("Save to Favorite Movie", callback_data="add_to_list_favorite_movie")],
            [InlineKeyboardButton("Save to Movie to watch", callback_data="add_to_list_movie_to_watch")],
            [InlineKeyboardButton("Menu", callback_data="start")],
        ],
    )

def get_pagination_movie_to_watch_keyboard(page_number):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Next Page",
                callback_data=f"next_watch_page_{page_number + 1}"
            )],
            [InlineKeyboardButton(
                text="Previous Page",
                callback_data=f"prev_watch_page_{page_number - 1}"
            )],
            [InlineKeyboardButton(
                text="Delete Movie",
                callback_data=f"delete_from_movie_to_watch_list"
            )]
        ],
    )
    return keyboard


def get_pagination_favorite_keyboard(page_number):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Следующая страница",
                callback_data=f"next_favorite_page_{page_number + 1}"  # Увеличиваем номер страницы для следующей кнопки
            )],
            [InlineKeyboardButton(
                text="Предыдущая страница",
                callback_data=f"prev_favorite_page_{page_number - 1}"  # Увеличиваем номер страницы для следующей кнопки
            )],
            [InlineKeyboardButton(
                text="Удалить фильм",
                callback_data=f"delete_from_favorite_list"
            )]
        ],
    )
import logging
import requests

from dotenv import dotenv_values
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, ConversationHandler

from cinemator.database import init_db, get_movies_to_watch, get_favorite_movies, add_movie_to_watch, add_favorite_movie

env_variables = dotenv_values(".env")

TG_TOKEN = env_variables.get("TG_TOKEN")
KINOPOISK_TOKEN = env_variables.get("KINOPOISK_TOKEN")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

url_random = 'https://api.kinopoisk.dev/v1.4/movie/random'


headers = {
    "accept": "application/json",
    "X-API-KEY": KINOPOISK_TOKEN
}

# Запрос с ответом в чат на рандомное описание
# requests.get(url, headers=headers).json()['description']

# Подключаемся к СУБД
init_db()

# Определяем состояния для диалога
ENTER_MOVIE = 0
ADD_TO_LISTS = 1


# Отдельный декоратора для логгирования
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


async def start(update, context):
    """
    Стартовая клавиатура. Четыре кнопки и приветствие.
    Каждая кнопка перехватывается отдельным обработчиком MessageHandler
    """
    keyboard = get_keyboard()
    await update.message.reply_text(
        "Привет! Давай начнем. Что я могу для тебя сделать?",
        reply_markup=keyboard
    )


# TODO: Random Movie BLOCK
async def random_movie(update, context):
    # TODO: Выдаёт рандомный тайтл. У фильмов часто пустые поля. Придумать, как фильтровать рандом по списку топ-250
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Главное меню", callback_data="start")]
    ])
    url_random_search = 'https://api.kinopoisk.dev/v1.4/movie/random'
    name = requests.get(url_random_search, headers=headers).json()['name']
    id = requests.get(url_random_search, headers=headers).json()['id']
    year = requests.get(url_random_search, headers=headers).json()['year']
    description = requests.get(url_random_search, headers=headers).json()['description']
    poster = requests.get(url_random_search, headers=headers).json()['poster']
    rating = requests.get(url_random_search, headers=headers).json()['rating']['kp']
    message_text = f'{name}\n{year}\n{description}\n{rating}\n{poster}'
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message_text)


# TODO: END Random Movie BLOCK


# TODO: Favorite Movie BLOCK
async def favorite_movie(update, context):
    user = update.effective_user
    movie_list = get_favorite_movies(user_id=user.id)
    formatted_movie_list = "\n\n".join([f"{movie[0]}\n{movie[1]}\n{movie[2]}" for movie in movie_list])
    await context.bot.send_message(chat_id=update.effective_chat.id, text=formatted_movie_list)
# TODO: END Favorite Movie BLOCK

# TODO: Movie to watch BLOCK
async def movie_to_watch(update, context):
    user = update.effective_user
    movie_list = get_movies_to_watch(user_id=user.id)
    formatted_movie_list = "\n\n".join([f"{movie[0]}\n{movie[1]}\n{movie[2]}" for movie in movie_list])
    await context.bot.send_message(chat_id=update.effective_chat.id, text=formatted_movie_list)
# TODO: END Movie to watch BLOCK


# TODO: Find Movie BLOCK
async def start_movie_search(update, context):
    """Начало разговора."""
    # Определяем состояние ввода имени фильма
    context.user_data['state'] = ENTER_MOVIE
    await update.callback_query.message.reply_text(
        "1Как называется фильм, который тебя интересует?"
    )
    return ENTER_MOVIE




async def ask_movie_name(update, context):
    """Задаем вопрос о имени."""
    await update.callback_query.message.reply_text("2Как называется фильм, который тебя интересует?")

    # Ожидаем ответ пользователя
    return ENTER_MOVIE


async def save_movie_name(update, context):
    """Сохраняем ответ пользователя."""
    user_id = update.message.from_user.id
    movie_for_search = update.message.text

    # Сохраняем ответ пользователя
    context.user_data['movie'] = movie_for_search

    await update.message.reply_text(
        f"Спасибо, {update.effective_chat.username}! Выполняю поиск фильма: {movie_for_search}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=movie_for_search)

    url_name_search = f'https://api.kinopoisk.dev/v1.4/movie/search?page=1&limit=10&query={movie_for_search}'
    name = requests.get(url_name_search, headers=headers).json()['docs'][0]['name']
    genres = requests.get(url_name_search, headers=headers).json()['docs'][0]['genres'][0]['name']
    id = requests.get(url_name_search, headers=headers).json()['docs'][0]['id']
    year = requests.get(url_name_search, headers=headers).json()['docs'][0]['year']
    description = requests.get(url_name_search, headers=headers).json()['docs'][0]['description']
    poster = requests.get(url_name_search, headers=headers).json()['docs'][0]['poster']
    rating = requests.get(url_name_search, headers=headers).json()['docs'][0]['rating']['kp']
    message_text = f'{name}\n{year}\n{description}\n{rating}\n{poster}\n{genres}'
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message_text)

    context.user_data['movie_info'] = {
        'name': name,
        'description': description,
        'year': year,
        'genres': genres,
        'rating': rating
    }

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("Save to Favorite Movie", callback_data="add_to_list_favorite_movie")],
            [InlineKeyboardButton("Save to Movie to watch", callback_data="add_to_list_movie_to_watch")],
            [InlineKeyboardButton("Menu", callback_data="start")],
        ],
    )
    await update.message.reply_text(
        "Хочешь сохранить фильм?",
        reply_markup=keyboard
    )

    return ADD_TO_LISTS

async def add_to_lists(update, context):
    user = update.effective_user
    query = update.callback_query

    if query.data == "add_to_list_favorite_movie":
        movie_info = context.user_data.get('movie_info')
        if movie_info:
            add_favorite_movie(
                user_id=user.id,
                title=movie_info['name'],
                description=movie_info['description'],
                year=movie_info['year'],
                genre=movie_info['genres'],
                rating=movie_info['rating']
            )
        await query.message.reply_text(f'Movie {movie_info["name"]} successfully added to favorites!')
    elif query.data == "add_to_list_movie_to_watch":
        movie_info = context.user_data.get('movie_info')
        if movie_info:
            add_movie_to_watch(
                user_id=user.id,
                title=movie_info['name'],
                description=movie_info['description'],
                year=movie_info['year'],
                genre=movie_info['genres'],
                rating=movie_info['rating']
            )
        await query.message.reply_text(f'Movie {movie_info["name"]} successfully added to Movie to watch list!')
#TODO: не работает вызов start
    else:
        await start(update, context)

    # Завершаем разговор
    return ConversationHandler.END


# TODO: END Find Movie BLOCK

# TODO: UNKNOWN BLOCK
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ниже - код для теста: сохраняет в БД отправленное пользователем сообщение
    user = update.effective_user
    if user:
        name = user.first_name
    else:
        name = 'Anonym'
    text = update.effective_message.text


    keyboard = get_keyboard()
    await update.message.reply_text(
        f'Извини, я не умею отвечать на такой запрос :(\nДавай попробуем ещё раз. Что я могу для тебя сделать?',
        reply_markup=keyboard  # TODO: вот сюда можно вставить отдельную функцию get_keyboard, чтобы не дублировать код.
    )


# TODO: END UNKNOWN BLOCK

# TODO: BUTTONS BLOCK
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки."""
    user = update.effective_user
    query = update.callback_query
    if query.data == "ask_movie_name":
        await ask_movie_name(update, context)
    elif query.data == "movie_to_watch":
        await movie_to_watch(update, context)
    elif query.data == "favorite_movie":
        await favorite_movie(update, context)



# TODO: END BUTTONS BLOCK

if __name__ == '__main__':
    application = ApplicationBuilder().token(TG_TOKEN).build()
    start_handler = CommandHandler('start', start)
    start_movie_search_handler = CallbackQueryHandler(start_movie_search, pattern=r'^ask_movie_name$')
    conversation_handler = ConversationHandler(
        entry_points=[start_movie_search_handler],
        states={
            ENTER_MOVIE: [MessageHandler(filters.TEXT & (~filters.COMMAND), save_movie_name)],
            ADD_TO_LISTS: [CallbackQueryHandler(add_to_lists)]
        },
        fallbacks=[],
    )
    random_movie_handler = CallbackQueryHandler(random_movie, pattern=r'^random_movie$')
    favorite_movie_handler = CallbackQueryHandler(favorite_movie, pattern=r'^favorite_movie$')
    movie_to_watch_handler = CallbackQueryHandler(movie_to_watch, pattern=r'^movie_to_watch$')


    unknown_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), unknown)


    application.add_handler(conversation_handler)
    application.add_handler(start_handler)
    application.add_handler(start_movie_search_handler)
    application.add_handler(random_movie_handler)
    application.add_handler(favorite_movie_handler)
    application.add_handler(movie_to_watch_handler)
    application.add_handler(unknown_handler)
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()
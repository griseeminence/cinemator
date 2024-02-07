import logging
import requests

from dotenv import dotenv_values
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, \
    InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes, InlineQueryHandler, \
    CallbackQueryHandler, ConversationHandler, CallbackContext

from cinemator.database import init_db, add_message, list_messages

# Загрузить переменные среды из файла .env
env_variables = dotenv_values(".env")

# Получить значение конкретной переменной
TG_TOKEN = env_variables.get("TG_TOKEN")
KINOPOISK_TOKEN = env_variables.get("KINOPOISK_TOKEN")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

url_random = 'https://api.kinopoisk.dev/v1.4/movie/random'  # Случайный фильм
# url_name_search = "https://api.kinopoisk.dev/v1.4/movie/search?page=1&limit=10&query=Джентельмены" #ПОиск фильма по названию


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
            [
                InlineKeyboardButton(text='Количество сообщений', callback_data='count'),
            ],
            [
                InlineKeyboardButton(text='Мои сообщения', callback_data='list'),
            ],
        ],
    )


async def start(update, context):
    """
    Стартовая клавиатура. Четыре кнопки и приветствие.
    Каждая кнопка перехватывается отдельным обработчиком MessageHandler
    """
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Find Movie", callback_data="ask_movie_name")],
        [InlineKeyboardButton("Random Movie", callback_data="random_movie")],
        [InlineKeyboardButton("Favorite Movie", callback_data="favorite_movie")],
        [InlineKeyboardButton("Movie to watch", callback_data="movie_to_watch")],
    ])
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
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=f'Здесь будет список любимых фильмов. Но меня ещё не подключили к БД :(')


# TODO: END Favorite Movie BLOCK

# TODO: Movie to watch BLOCK
async def movie_to_watch(update, context):
    user = update.effective_user
    query = update.callback_query
    messages = list_messages(user_id=user.id, limit=10)
    text = '\n\n'.join([f'#{message_id} - {message_text}' for message_id, message_text in messages])
    await update.effective_message.reply_text(text=text)
    # await context.bot.send_message(chat_id=update.effective_chat.id,
    #                                text=f'Здесь будет список фильмов, которые ты хочешь посмотреть. Но меня ещё не подключили к БД :(')
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=f'Я всё ещё работаю неправильно, но меня уже подключили к базе данных!')


# TODO: END Movie to watch BLOCK


# TODO: Find Movie BLOCK
async def start_movie_search(update, context):
    """Начало разговора."""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Find Movie", callback_data="ask_movie_name")]
    ])
    await update.message.reply_text(
        "Привет! Давай начнем. Я помогу найти тебе фильм.",
        reply_markup=keyboard
    )
    return ENTER_MOVIE  # Переходим в состояние ENTER_MOVIE


async def ask_movie_name(update, context):
    """Задаем вопрос о имени."""
    await update.callback_query.message.reply_text("Как называется фильм, который тебя интересует?")

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
    id = requests.get(url_name_search, headers=headers).json()['docs'][0]['id']
    year = requests.get(url_name_search, headers=headers).json()['docs'][0]['year']
    description = requests.get(url_name_search, headers=headers).json()['docs'][0]['description']
    poster = requests.get(url_name_search, headers=headers).json()['docs'][0]['poster']
    rating = requests.get(url_name_search, headers=headers).json()['docs'][0]['rating']['kp']
    message_text = f'{name}\n{year}\n{description}\n{rating}\n{poster}'
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message_text)

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
    if text:
        add_message(user_id=user.id, text=text)

    keyboard = ReplyKeyboardMarkup([
        ['Find Movie', 'Random Movie'], ['Favorite Movies', 'Movie for later']
    ], resize_keyboard=True)
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



# TODO: END BUTTONS BLOCK

if __name__ == '__main__':
    application = ApplicationBuilder().token(TG_TOKEN).build()
    start_handler = CommandHandler('start', start)
    start_movie_search_handler = MessageHandler(filters.Regex(r'^Find Movie$'), start_movie_search)
    random_movie_handler = CallbackQueryHandler(random_movie, pattern=r'^random_movie$')
    favorite_movie_handler = CallbackQueryHandler(favorite_movie, pattern=r'^favorite_movie$')
    movie_to_watch_handler = CallbackQueryHandler(movie_to_watch, pattern=r'^movie_to_watch$')
    unknown_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), unknown)
    conversation_handler = ConversationHandler(
        entry_points=[start_movie_search_handler],
        states={
            ENTER_MOVIE: [MessageHandler(filters.TEXT & (~filters.COMMAND), save_movie_name)]
        },
        fallbacks=[]
    )

    application.add_handler(conversation_handler)
    application.add_handler(start_handler)
    application.add_handler(start_movie_search_handler)
    application.add_handler(random_movie_handler)
    application.add_handler(favorite_movie_handler)
    application.add_handler(movie_to_watch_handler)
    application.add_handler(unknown_handler)
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()

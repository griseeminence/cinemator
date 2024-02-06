import logging
import requests

from dotenv import dotenv_values
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, \
    InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes, InlineQueryHandler, \
    CallbackQueryHandler, ConversationHandler, CallbackContext

# Загрузить переменные среды из файла .env
env_variables = dotenv_values(".env")

# Получить значение конкретной переменной
TG_TOKEN = env_variables.get("TG_TOKEN")
KINOPOISK_TOKEN = env_variables.get("KINOPOISK_TOKEN")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

url_random = "https://api.kinopoisk.dev/v1.4/movie/random"  # Случайный фильм
# url_name_search = "https://api.kinopoisk.dev/v1.4/movie/search?page=1&limit=10&query=Джентельмены" #ПОиск фильма по названию


headers = {
    "accept": "application/json",
    "X-API-KEY": KINOPOISK_TOKEN
}

# Запрос с ответом в чат на рандомное описание
# requests.get(url, headers=headers).json()['description']

# Определяем состояния для диалога
ENTER_MOVIE = 0

async def start(update, context):
    """
    Стартовая клавиатура. Четыре кнопки и приветствие.
    Каждая кнопка перехватывается отдельным MessageHandler
    """
    keyboard = ReplyKeyboardMarkup([
        ['Find Movie', 'Random Movie'], ['Favorite Movies', 'Movie for later']
    ], resize_keyboard=True)
    await update.message.reply_text(
        "Привет! Давай начнем. Что я могу для тебя сделать?",
        reply_markup=keyboard
    )

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


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup([
        ['Find Movie', 'Random Movie'], ['Favorite Movies', 'Movie for later']
    ], resize_keyboard=True)
    await update.message.reply_text(
        f'Извини, я не умею отвечать на такой запрос :(\nДавай попробуем ещё раз. Что я могу для тебя сделать?',
        reply_markup=keyboard
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки."""
    query = update.callback_query
    if query.data == "ask_movie_name":
        await ask_movie_name(update, context)

if __name__ == '__main__':
    application = ApplicationBuilder().token(TG_TOKEN).build()
    start_handler = CommandHandler('start', start)
    start_movie_search_handler = MessageHandler(filters.Regex(r'^Find Movie$'), start_movie_search)
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
    application.add_handler(unknown_handler)
    application.add_handler(CallbackQueryHandler(button))


    application.run_polling()
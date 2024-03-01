import logging
import requests
import random

from dotenv import dotenv_values
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes, \
    CallbackQueryHandler, ConversationHandler

from cinemator.database import init_db, get_movies_to_watch, get_favorite_movies, add_movie_to_watch, add_favorite_movie, del_movie_to_watch

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
ADD_RANDOM_TO_LISTS = 0
DELETE_FROM_LISTS = 1
CHOOSE_MOVIE_TO_DELETE = 0


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
    Добавлен случай обработки callback_query для вызова с кнопок (использую для возврата пользователя в меню)
    """
    print(f'Зашёл в функцию старт')
    print(update)
    print(context)
    if update.message:
        keyboard = get_keyboard()
        await update.message.reply_text(
            "Привет! Давай начнем. Что я могу для тебя сделать?",
            reply_markup=keyboard
        )
    elif update.callback_query:
        data = update.callback_query.data
        if data == "start":
            keyboard = get_keyboard()
            await update.callback_query.message.reply_text(
                "Хорошо, начнём с самого начала. Что я могу для тебя сделать?",
                reply_markup=keyboard
            )
    else:
        print("Обновление не содержит ни сообщения, ни данных коллбэка.")
    print(f'Вышел из функции старт')


# TODO: Random Movie BLOCK
async def random_movie(update, context):
    # TODO: Выдаёт рандомный тайтл. У фильмов часто пустые поля. Придумать, как фильтровать рандом по списку топ-250

    # url_random_250 = 'https://api.kinopoisk.dev/v1.4/movie?page=1&limit=250&selectFields=id&selectFields=top250&sortField=top250&sortType=-1'
    # url_random_250 = 'https://api.kinopoisk.dev/v1.4/movie?page=1&limit=250&selectFields=id&selectFields=top250&selectFields=name&selectFields=description&selectFields=year&selectFields=rating&selectFields=poster&selectFields=genres&sortField=top250&sortType=-1'
    url_random_250 = 'https://api.kinopoisk.dev/v1.4/movie?page=1&limit=250&selectFields=id&selectFields=top250&selectFields=name&selectFields=description&selectFields=year&selectFields=rating&selectFields=poster&selectFields=genres&selectFields=type&sortField=top250&sortType=-1&type=movie'
    random_250 = random.randrange(0, 250)

    name = requests.get(url_random_250, headers=headers).json()['docs'][random_250]['name']
    genres = requests.get(url_random_250, headers=headers).json()['docs'][random_250]['genres'][0]['name']
    id = requests.get(url_random_250, headers=headers).json()['docs'][random_250]['id']
    year = requests.get(url_random_250, headers=headers).json()['docs'][random_250]['year']
    description = requests.get(url_random_250, headers=headers).json()['docs'][random_250]['description']
    poster = requests.get(url_random_250, headers=headers).json()['docs'][random_250]['poster']['url']
    rating = requests.get(url_random_250, headers=headers).json()['docs'][random_250]['rating']['kp']
    message_text = f'Название: {name}\nГод: {year}\nОписание: {description}\nРейтинг: {rating}\nЖанр: {genres}\nПостер: {poster}'
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
    await update.callback_query.message.reply_text(
        "Хочешь сохранить фильм?",
        reply_markup=keyboard
    )

    return ADD_TO_LISTS


# TODO: END Random Movie BLOCK


# TODO: Favorite Movie BLOCK
async def favorite_movie(update, context, page_number=1):
    print(f' page_number = {page_number}')
    user = update.effective_user
    limit = 5
    if page_number == 1:
        offset = 0
    elif page_number > 1:
        offset = (page_number - 1) * limit
    print(f'offset = {offset}')
    print(get_favorite_movies(user_id=user.id))
    print(get_favorite_movies(user_id=user.id, limit=5, offset=0))
    print(get_favorite_movies(user_id=user.id, limit=5, offset=5))
    movie_list = get_favorite_movies(user_id=user.id, limit=limit, offset=offset)

    if not movie_list:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Список фильмов пуст.")
        return

    formatted_movie_list = "\n\n".join([f"{movie[0]}\n{movie[1]}\n{movie[2]}" for movie in movie_list])

    keyboard = InlineKeyboardMarkup(
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

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=formatted_movie_list,
        reply_markup=keyboard
    )

    #Здесь передаём состояние диалога в то, в котором в conversationhandler у нас вызывается следующая функция.
    return CHOOSE_MOVIE_TO_DELETE

    #TODO:  старый код, удалить если актуальный работает без ошибок
    # #
    # movie_list = get_favorite_movies(user_id=user.id)
    # formatted_movie_list = "\n\n".join([f"{movie[0]}\n{movie[1]}\n{movie[2]}" for movie in movie_list])
    # await context.bot.send_message(chat_id=update.effective_chat.id, text=formatted_movie_list)
    # #

# TODO: END Favorite Movie BLOCK

# TODO: Movie to watch BLOCK
async def movie_to_watch(update, context, page_number=1):
    print(f' page_number = {page_number}')
    user = update.effective_user
    limit = 5
    if page_number == 1:
        offset = 0
    elif page_number > 1:
        offset = (page_number - 1) * limit
    print(f'offset = {offset}')
    print(get_movies_to_watch(user_id=user.id))
    print(get_movies_to_watch(user_id=user.id, limit=5, offset=0))
    print(get_movies_to_watch(user_id=user.id, limit=5, offset=5))
    movie_list = get_movies_to_watch(user_id=user.id, limit=limit, offset=offset)
    print(movie_list)

    if not movie_list:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Список фильмов пуст.")
        return

    formatted_movie_list = "\n\n".join([f"ID фильма: {movie[0]}\nНазвание фильма{movie[1]}\nОписание фильма:{movie[2]}\nГод: {movie[3]}\nЖанр: {movie[4]}\nРейтинг: {movie[5]}\n" for movie in movie_list])

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Следующая страница",
                callback_data=f"next_watch_page_{page_number + 1}"  # Увеличиваем номер страницы для следующей кнопки
            )],
            [InlineKeyboardButton(
                text="Предыдущая страница",
                callback_data=f"prev_watch_page_{page_number - 1}"  # Увеличиваем номер страницы для следующей кнопки
            )],
            [InlineKeyboardButton(
                text="Удалить фильм",
                callback_data=f"delete_from_movie_to_watch_list"
            )]
        ],
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=formatted_movie_list,
        reply_markup=keyboard
    )
    #Здесь передаём состояние диалога в то, в котором в conversationhandler у нас вызывается следующая функция.
    return CHOOSE_MOVIE_TO_DELETE

async def choose_movie_to_delete(update, context):
    print(f'Захожу в функцию choose_movie_to_delete')
    user = update.effective_user
    query = update.callback_query
    context.user_data['state'] = CHOOSE_MOVIE_TO_DELETE
    context.user_data['delete_button'] = query.data
    print(f'Сейчас в контексте delete_button: {context.user_data["delete_button"]}')
    print(f'Сейчас в контексте state: {context.user_data["state"]}')
    if query.data == "delete_from_movie_to_watch_list" or query.data == "delete_from_favorite_list":
        await update.callback_query.message.reply_text(
            "1Как называется фильм, который ты хочешь удалить?"
        )
        print(f'Выхожу из функции choose_movie_to_delete до return')
        return DELETE_FROM_LISTS
    print(f'Выхожу из функции choose_movie_to_delete')
    return DELETE_FROM_LISTS


async def delete_from_list(update, context):
    print(f'Захожу в функцию delete_from_list')
    user = update.effective_user
    context.user_data['state'] = DELETE_FROM_LISTS
    movie_to_delete = update.message.text
    print(f'Сейчас в контексте state: {context.user_data["state"]}')
    print(f'Переменная movie_to_delete: {movie_to_delete}')
    context.user_data['movie_id'] = movie_to_delete
    print(f'Переменная context.user_data["movie_id"]: {context.user_data["movie_id"]}')
    await update.message.reply_text(
        f"Спасибо, {update.effective_chat.username}! Выполняю удаление фильма: {movie_to_delete}"
    )
    del_movie_to_watch(user_id=user.id, movie_id=movie_to_delete)



    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("Menu", callback_data="start")],
        ],
    )
    await update.message.reply_text(
        "Фильм успешно удалён",
        reply_markup=keyboard
    )
    print(f'Выхожу из функции delete_from_list')
    return ConversationHandler.END

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


async def save_movie_name(update, context):
    """Сохраняем ответ пользователя."""
    user_id = update.message.from_user.id
    movie_for_search = update.message.text
    context.user_data['movie'] = movie_for_search
    await update.message.reply_text(
        f"Спасибо, {update.effective_chat.username}! Выполняю поиск фильма: {movie_for_search}"
    )
    # TODO: Добавить к упл сортировку по рейтингу
    url_name_search = f'https://api.kinopoisk.dev/v1.4/movie/search?page=1&limit=10&query={movie_for_search}'
    name = requests.get(url_name_search, headers=headers).json()['docs'][0]['name']
    genres = requests.get(url_name_search, headers=headers).json()['docs'][0]['genres'][0]['name']
    id = requests.get(url_name_search, headers=headers).json()['docs'][0]['id']
    year = requests.get(url_name_search, headers=headers).json()['docs'][0]['year']
    description = requests.get(url_name_search, headers=headers).json()['docs'][0]['description']
    poster = requests.get(url_name_search, headers=headers).json()['docs'][0]['poster']['url']
    rating = requests.get(url_name_search, headers=headers).json()['docs'][0]['rating']['kp']
    message_text = f'Название: {name}\nГод: {year}\nОписание: {description}\nРейтинг: {rating}\nЖанр: {genres}\nПостер: {poster}'
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
    else:
        await start(update, context)

    # Завершаем разговор
    return ConversationHandler.END


# TODO: END Find Movie BLOCK

# TODO: UNKNOWN BLOCK
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    keyboard = get_keyboard()
    await update.message.reply_text(
        f'Извини, я не умею отвечать на такой запрос :(\nДавай попробуем ещё раз. Что я могу для тебя сделать?',
        reply_markup=keyboard  # TODO: вот сюда можно вставить отдельную функцию get_keyboard, чтобы не дублировать код.
    )


# TODO: END UNKNOWN BLOCK

# TODO: BUTTONS BLOCK
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки."""
    query = update.callback_query
    if query.data == "movie_to_watch":
        await movie_to_watch(update, context)
    elif query.data == "favorite_movie":
        await favorite_movie(update, context)
    elif query.data.startswith("next_watch_page"):
        print(f'query_data = {query.data}')
        page_number = int(query.data.split('_')[-1])  # Извлекаем номер страницы из коллбэк данных
        print(f'before_next_page_number_button = {page_number}')
        # TODO: Здесь была пагинация в аргументах page_number+1, однако передавался сюда аргумент с уже добавленным числом
        # TODO: Не понимаю, на каком этапе он его плюсует - разобраться. В любом случае -пагинация работает.
        # TODO: добавить пагинацию ко второй функции
        await movie_to_watch(update, context, page_number)
        print(f'after_page_number_button = {page_number}')
    elif query.data.startswith('prev_watch_page'):
        print(f'query_data = {query.data}')
        page_number = int(query.data.split('_')[-1])
        print(f'before_prev_page_number_button = {page_number}')
        await movie_to_watch(update, context, page_number)
        print(f'after_page_number_button = {page_number}')
    elif query.data.startswith("next_favorite_page"):
        print(f'query_data = {query.data}')
        page_number = int(query.data.split('_')[-1])  # Извлекаем номер страницы из коллбэк данных
        print(f'before_next_page_number_button = {page_number}')
        # TODO: Здесь была пагинация в аргументах page_number+1, однако передавался сюда аргумент с уже добавленным числом
        # TODO: Не понимаю, на каком этапе он его плюсует - разобраться. В любом случае -пагинация работает.
        # TODO: добавить пагинацию ко второй функции
        await favorite_movie(update, context, page_number)
        print(f'after_page_number_button = {page_number}')
    elif query.data.startswith('prev_favorite_page'):
        print(f'query_data = {query.data}')
        page_number = int(query.data.split('_')[-1])
        print(f'before_prev_page_number_button = {page_number}')
        await favorite_movie(update, context, page_number)
        print(f'after_page_number_button = {page_number}')


# TODO: END BUTTONS BLOCK

if __name__ == '__main__':
    application = ApplicationBuilder().token(TG_TOKEN).build()
    start_handler = CommandHandler('start', start)
    start_movie_search_handler = CallbackQueryHandler(start_movie_search, pattern=r'^ask_movie_name$')
    random_movie_handler = CallbackQueryHandler(random_movie, pattern=r'^random_movie$')
    favorite_movie_handler = CallbackQueryHandler(favorite_movie, pattern=r'^favorite_movie$')
    movie_to_watch_handler = CallbackQueryHandler(movie_to_watch, pattern=r'^movie_to_watch$')
    search_conversation_handler = ConversationHandler(
        entry_points=[start_movie_search_handler],
        states={
            ENTER_MOVIE: [MessageHandler(filters.TEXT & (~filters.COMMAND), save_movie_name)],
            ADD_TO_LISTS: [CallbackQueryHandler(add_to_lists)]
        },
        fallbacks=[],
    )
    random_conversation_handler = ConversationHandler(
        entry_points=[random_movie_handler],
        states={
            ADD_TO_LISTS: [CallbackQueryHandler(add_to_lists)]
        },
        fallbacks=[],
    )
    favorite_movie_conversation_handler = ConversationHandler(
        entry_points=[favorite_movie_handler],
        states={
            CHOOSE_MOVIE_TO_DELETE: [CallbackQueryHandler(choose_movie_to_delete)],
            DELETE_FROM_LISTS: [MessageHandler(filters.TEXT & (~filters.COMMAND), delete_from_list)]
        },
        fallbacks=[],
    )
    movie_to_watch_conversation_handler = ConversationHandler(
        entry_points=[movie_to_watch_handler],
        states={
            CHOOSE_MOVIE_TO_DELETE: [CallbackQueryHandler(choose_movie_to_delete)],
            DELETE_FROM_LISTS: [MessageHandler(filters.TEXT & (~filters.COMMAND), delete_from_list)]
        },
        fallbacks=[],
    )
    unknown_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), unknown)

    application.add_handler(search_conversation_handler)
    application.add_handler(favorite_movie_conversation_handler)
    application.add_handler(movie_to_watch_conversation_handler)
    application.add_handler(random_conversation_handler)
    application.add_handler(start_handler)
    application.add_handler(start_movie_search_handler)
    application.add_handler(random_movie_handler)
    application.add_handler(favorite_movie_handler)
    application.add_handler(movie_to_watch_handler)

    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(unknown_handler)

    application.run_polling()

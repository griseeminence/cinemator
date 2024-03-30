import requests
import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes, \
    CallbackQueryHandler, ConversationHandler

from cinemator.database import get_movies_to_watch, get_favorite_movies, add_movie_to_watch, \
    add_favorite_movie, del_movie_to_watch, init_db, del_favorite_movies
from cinemator.tools import *
from cinemator.constants import *

init_db()


# Решено  #1: Придумать, как вставить клавиатуру из вспомогательного файла (favorite, movie_to_watch)
# Решено  #2: Сломалась пагинация в favorites полность, а в movies_to_watch не работает delete после кнопки next page
# Решено  #3: Сломалось удаление из списков
# TODO #4: Разбить и отрефакторить код ещё больше
# TODO #5: Написать readme
# Решено,  #6: Придумать, как картинку к фильму (постер) присылать ИЗ API без ссылки.
#    Добавил отправку фото с текстом вместо текстового сообщения со ссылкой на фото
#    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=poster, caption=caption, parse_mode='HTML')
# TODO #7: Разобраться с buttons. Есть ощущение, что можно половину оттуда безопасно удалить.
# Решено #8: Разобраться с ошибкой обработчиков Conversation: C:\Development\GitHub\cinemator\cinemator\core.py:424: PTBUserWarning: If 'per_message=False', 'CallbackQueryHandler' will not be tracked for every message. Read this FAQ entry to learn more about the per_* settings: https://github.com/python-telegram-bot/python-telegram-bot/wiki/Frequently-Asked-Questions#what-do-the-per_-settings-in-conversationhandler-do.
#   movie_to_watch_conversation_handler = ConversationHandler(
# Решение: В библиотеке python-telegram-bot нет прямой поддержки параметра per_message.
# Вместо этого, обработчики событий автоматически отслеживаются для каждого сообщения,
# поэтому вам не нужно явно указывать этот параметр.
# TODO #9: При работе в списках кнопки становятся неактивными после первого нажатия. Это ломает логику.
#   Например, если в  своём списка нажать на "next page", то кнопка "delete movie" уже не работает.
#   Придумать, как это исправить.
# Решено ODO: #10 Удаление перестало работать!
# TODO #10: Кнопка delete работает один раз за запуск бота. Потом она неактивна из любого меню.
# TODO #11: После next_page не работает delete в списках фильмов.
@logger_in_out
async def start(update, context):
    """
    Starting keyboard. Four buttons and a greeting.
    Each button is handled by a separate MessageHandler.
    Added a case for processing callback_query to be triggered by buttons (used for returning the user to the menu).
    """

    if update.message:
        keyboard = get_main_keyboard()
        await update.message.reply_text(
            "Hello! Let's get started. What can I do for you?",
            reply_markup=keyboard
        )
    elif update.callback_query:
        data = update.callback_query.data
        # Заменить условия другой логикой
        if data == 'start' or data == 'add_to_list_movie_to_watch' or data == 'add_to_list_favorite_movie' or data == 'delete_from_lists':
            keyboard = get_main_keyboard()
            await update.callback_query.message.reply_text(
                "Alright, let's start from the beginning. What can I do for you?",
                reply_markup=keyboard
            )
    else:
        print('The update contains neither a message nor callback data.')


async def random_movie(update, context):
    await update.callback_query.message.reply_text(
        f"Thanks, {update.effective_chat.username}! I'm choosing movie for you..."
    )
    random_250 = random.randrange(0, 250)  # Подбор 250 лучших фильмов. В апи кинопоиска нет отдельного фильтра.
    request_movie_template = requests.get(url_random_250, headers=headers).json()['docs'][random_250]

    name = request_movie_template['name']
    genres = request_movie_template['genres'][0]['name']
    year = request_movie_template['year']
    description = request_movie_template['description']
    poster = request_movie_template['poster']['url']
    rating = request_movie_template['rating']['kp']

    message_text = (
        f'Название: {name}\n'
        f'Год: {year}\n'
        f'Описание: {description}\n'
        f'Рейтинг: {rating}\n'
        f'Жанр: {genres}\n'
        f'Постер: {poster}'
    )

    await context.bot.send_message(chat_id=update.effective_chat.id, text=message_text)

    context.user_data['movie_info'] = {
        'name': name,
        'description': description,
        'year': year,
        'genres': genres,
        'rating': rating
    }

    keyboard = get_save_movie_keyboard()
    await update.callback_query.message.reply_text(
        "Хочешь сохранить фильм?",
        reply_markup=keyboard
    )

    return ADD_TO_LISTS


async def favorite_movie(update, context, page_number=1):
    # TODO: Не работает удаление (диалог полностью проигрывается, но не происходит удаление из бд)
    # TODO: не решено
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

    formatted_movie_list = "\n\n".join(
        [
            (
                f"{movie[1]}\n"
                f"ID: {movie[0]}\n\n"
                f"- Description:\n{movie[2]}\n\n"
                f"- Year:\n{movie[3]}\n\n"
                f"- Genre:\n{movie[4]}\n\n"
                f"- Rating:\n{movie[5]}\n\n"
                f"_______________________________________________________\n\n"
            )
            for movie in movie_list
        ]
    )

    keyboard = get_pagination_favorite_keyboard(page_number)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=formatted_movie_list,
        reply_markup=keyboard
    )

    print(f'Выхожу из функции favorite')
    user = update.effective_user
    query = update.callback_query
    print(f'query_data = {query.data}')

    return CHOOSE_MOVIE_TO_DELETE


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
        await context.bot.send_message(chat_id=update.effective_chat.id, text="No movies in the list.")
        return

    formatted_movie_list = "\n\n".join(
        [
            (
                f"{movie[1]}\n"
                f"ID: {movie[0]}\n\n"
                f"- Description:\n{movie[2]}\n\n"
                f"- Year:\n{movie[3]}\n\n"
                f"- Genre:\n{movie[4]}\n\n"
                f"- Rating:\n{movie[5]}\n\n"
                f"_______________________________________________________\n\n"
            )
            for movie in movie_list
        ]
    )

    keyboard = get_pagination_movie_to_watch_keyboard(page_number)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=formatted_movie_list,
        reply_markup=keyboard
    )
    print(f'Выхожу из функции movie_to_watch')
    user = update.effective_user
    query = update.callback_query
    print(f'query_data = {query.data}')
    if query.data == "delete_from_movie_to_watch_list" or query.data == "delete_from_favorite_list":
        return CHOOSE_MOVIE_TO_DELETE


async def choose_movie_to_delete(update, context):
    """Write an ID (or smth) to delete """
    print(f'Захожу в функцию choose_movie_to_delete')
    query = update.callback_query
    context.user_data['state'] = CHOOSE_MOVIE_TO_DELETE
    context.user_data['delete_button'] = query.data
    print(f'Сейчас в контексте delete_button: {context.user_data["delete_button"]}')
    print(f'Сейчас в контексте state: {context.user_data["state"]}')
    context.user_data["list_type"] = query.data
    if query.data == "delete_from_movie_to_watch_list" or query.data == "delete_from_favorite_list":
        await update.callback_query.message.reply_text(
            "Write an ID of the movie you want to delete"
        )
        print(f'Выхожу из функции choose_movie_to_delete до return')
        print(f' сейчас в контексте List_type: {context.user_data["list_type"]}')
        return DELETE_FROM_LISTS

    print(f' сейчас в контексте List_type: {context.user_data["list_type"]}')
    print(f'Выхожу из функции choose_movie_to_delete')
    print(f'Сейчас в контексте state: {context.user_data["state"]}')

    return DELETE_FROM_LISTS


async def delete_from_list(update, context):
    """Movie deletion logic"""
    print(f'Захожу в функцию delete_from_list')

    list_type = context.user_data.get('list_type')
    print(context.user_data["list_type"])
    print(f'list_type = {list_type}')

    user = update.effective_user
    context.user_data['state'] = DELETE_FROM_LISTS
    movie_to_delete = update.message.text
    print(f'Сейчас в контексте state: {context.user_data["state"]}')
    print(f'Переменная movie_to_delete: {movie_to_delete}')
    context.user_data['movie_id'] = movie_to_delete
    print(f'Переменная context.user_data["movie_id"]: {context.user_data["movie_id"]}')
    await update.message.reply_text(
        f"Thanks, {update.effective_chat.username}! Deleting: {movie_to_delete}..."
    )
    if list_type == "delete_from_movie_to_watch_list":
        del_movie_to_watch(user_id=user.id, movie_id=movie_to_delete)
    elif list_type == "delete_from_favorite_list":
        del_favorite_movies(user_id=user.id, movie_id=movie_to_delete)

    await start(update, context)
    return ConversationHandler.END


async def start_movie_search(update, context):
    """Start Conversation."""
    context.user_data['state'] = ENTER_MOVIE
    await update.callback_query.message.reply_text(
        'Write the movie title'
    )
    return ENTER_MOVIE


async def save_movie_name(update, context):
    """Saving the user answer."""

    movie_for_search = update.message.text
    context.user_data['movie'] = movie_for_search
    await update.message.reply_text(
        f"Thanks, {update.effective_chat.username}! I'm searching your movie: {movie_for_search}"
    )

    # TODO: Добавить в урл сортировку по рейтингу
    url_name_search = f'https://api.kinopoisk.dev/v1.4/movie/search?page=1&limit=10&query={movie_for_search}'
    request_movie_template = requests.get(url_name_search, headers=headers).json()['docs'][0]

    name = request_movie_template['name']
    genres = request_movie_template['genres'][0]['name']
    year = request_movie_template['year']
    description = request_movie_template['description']
    poster = request_movie_template['poster']['url']
    rating = request_movie_template['rating']['kp']

    context.user_data['movie_info'] = {
        'name': name,
        'description': description,
        'year': year,
        'genres': genres,
        'rating': rating
    }

    message_text = (
        f'- Title: {name}\n'
        f'- Year: {year}\n'
        f'- Description: {description}\n'
        f'- Rating: {rating}\n'
        f'- Genre: {genres}\n'
        f'- Poster: {poster}'
    )

    # Отправка изображения с текстом в чат
    caption = f"<b>{name}</b>\n\nGenres: {genres}\nYear: {year}\nDescription: {description}"
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=poster, caption=caption, parse_mode='HTML')
    # parse_mode даёт возможность использовать разметку и правила HTML (полезно для текста курсив, жирыный, подчеркнутый и тд).
    keyboard = get_save_movie_keyboard()
    await update.message.reply_text(
        "Do you wanna save movie?",
        reply_markup=keyboard
    )

    return ADD_TO_LISTS


async def add_to_lists(update, context):
    """Adding a movie to lists"""
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
        await query.message.reply_text(f'Movie "{movie_info["name"]}" successfully added to favorites!')
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
        await query.message.reply_text(f'Movie "{movie_info["name"]}" successfully added to Movie to watch list!')
        await start(update, context)
    else:
        await start(update, context)

    # Завершаем разговор
    return ConversationHandler.END


async def unknown(update, context):
    """Unknown text/command logic"""
    keyboard = get_main_keyboard()
    await update.message.reply_text(
        f"Sorry, but I can't answer you :(\nLet's try again. What can I do for you?",
        reply_markup=keyboard
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Button logic."""
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

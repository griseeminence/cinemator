import random
import requests

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from cinemator.constants import *
from cinemator.database import (
    add_favorite_movie,
    add_movie_to_watch,
    del_favorite_movies,
    del_movie_to_watch,
    get_favorite_movies,
    get_movies_to_watch,
    init_db,
)
from cinemator.tools import *

init_db()


# TODO #11: После next_page не работает delete в списках фильмов.
# TODO #12: Перенести buttons в tools и настроить логику.
# TODO #13: Переписать под вебхуки

@logger_in_out
async def start(update, context):
    """
    Handles the start command for the Telegram bot.

    This function checks whether the update contains a message or a callback query.
    If a message is received, it sends a greeting and presents the user with a
    main keyboard containing options. If a callback query is detected, it checks
    the data of the query to determine which button was clicked, and responds
    accordingly by displaying the main keyboard again.
    """

    if update.message:
        # Create and send a keyboard with buttons for the user to interact with
        keyboard = get_main_keyboard()
        await update.message.reply_text(
            "Hello! Let's get started. What can I do for you?",
            reply_markup=keyboard
        )
    elif update.callback_query:
        # Handle button clicks from the user
        data = update.callback_query.data
        if data == 'start' or data == 'add_to_list_movie_to_watch' or data == 'add_to_list_favorite_movie' or data == 'delete_from_lists':
            keyboard = get_main_keyboard()
            await update.callback_query.message.reply_text(
                "Alright, let's start from the beginning. What can I do for you?",
                reply_markup=keyboard
            )
    else:
        # Log a message if the update does not contain a message or callback data
        print('The update contains neither a message nor callback data.')


async def random_movie(update, context):
    """
    Selects a random movie from the top 250 and sends information about it to the user.
    After sending the information, it prompts the user to save the movie to their list.

    Returns:
        str: A constant representing the next step in the conversation flow.
    """

    # Inform the user that a movie is being selected
    await update.callback_query.message.reply_text(
        f"Thanks, {update.effective_chat.username}! I'm choosing movie for you..."
    )
    # Select a random index to retrieve a movie from the top 250
    random_250 = random.randrange(0, 250)
    request_movie_template = requests.get(url_random_250, headers=headers).json()['docs'][random_250]

    # Retrieving movie information from the API response
    name = request_movie_template['name']
    genres = request_movie_template['genres'][0]['name']
    year = request_movie_template['year']
    description = request_movie_template['description']
    poster = request_movie_template['poster']['url']
    rating = request_movie_template['rating']['kp']

    # Generating a message with information about the movie
    message_text = (
        f'Название: {name}\n'
        f'Год: {year}\n'
        f'Описание: {description}\n'
        f'Рейтинг: {rating}\n'
        f'Жанр: {genres}\n'
        f'Постер: {poster}'
    )

    # Sending movie information to the user
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message_text)

    # Storing movie information in user_data for future reference
    context.user_data['movie_info'] = {
        'name': name,
        'description': description,
        'year': year,
        'genres': genres,
        'rating': rating
    }

    # Creating a keyboard for saving the movie to the user's list
    keyboard = get_save_movie_keyboard()
    await update.callback_query.message.reply_text(
        'Do you want to save the movie?',
        reply_markup=keyboard
    )

    return ADD_TO_LISTS  # Indicating the next step in the conversation flow


async def favorite_movie(update, context, page_number=1):
    """
    Sends the user a paginated list of favorite movies and allows them to remove movies from the list.

    Returns:
        str: A constant representing the next step in the conversation flow.
    """

    print(f' page_number = {page_number}')
    user = update.effective_user
    limit = 5  # Number of movies to display per page

    # Calculate offset based on the current page number
    if page_number == 1:
        offset = 0
    elif page_number > 1:
        offset = (page_number - 1) * limit

    # Debug prints to check favorite movies retrieval
    print(f'offset = {offset}')
    print(get_favorite_movies(user_id=user.id))
    print(get_favorite_movies(user_id=user.id, limit=5, offset=0))
    print(get_favorite_movies(user_id=user.id, limit=5, offset=5))

    # Retrieve the user's favorite movies with pagination
    movie_list = get_favorite_movies(user_id=user.id, limit=limit, offset=offset)

    if not movie_list:
        # Inform the user if there are no favorite movies
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Список фильмов пуст.")
        return

    # Formatting the list of favorite movies for display
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

    # Generate the pagination keyboard for navigation
    keyboard = get_pagination_favorite_keyboard(page_number)

    # Send the formatted movie list to the user
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=formatted_movie_list,
        reply_markup=keyboard
    )

    print(f'Выхожу из функции favorite')

    # Prepare to handle user's choice on movie deletion
    user = update.effective_user
    query = update.callback_query
    print(f'query_data = {query.data}')

    return CHOOSE_MOVIE_TO_DELETE  # Indicating the next step in the conversation flow


async def movie_to_watch(update, context, page_number=1):
    """
    Sends the user a paginated list of movies they want to watch.

    Returns:
        str: A constant representing the next step in the conversation flow.
    """

    print(f' page_number = {page_number}')
    user = update.effective_user
    limit = 5  # Number of movies to display per page

    # Calculate offset based on the current page number
    if page_number == 1:
        offset = 0
    elif page_number > 1:
        offset = (page_number - 1) * limit

    # Debug prints to check movies retrieval
    print(f'offset = {offset}')
    print(get_movies_to_watch(user_id=user.id))
    print(get_movies_to_watch(user_id=user.id, limit=5, offset=0))
    print(get_movies_to_watch(user_id=user.id, limit=5, offset=5))

    # Retrieve the user's movies to watch with pagination
    movie_list = get_movies_to_watch(user_id=user.id, limit=limit, offset=offset)
    print(movie_list)

    if not movie_list:
        # Inform the user if there are no movies in the watch list
        await context.bot.send_message(chat_id=update.effective_chat.id, text="No movies in the list.")
        return

    # Formatting the list of movies to watch for display
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

    # Generate the pagination keyboard for navigation
    keyboard = get_pagination_movie_to_watch_keyboard(page_number)

    # Send the formatted movie list to the user
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=formatted_movie_list,
        reply_markup=keyboard
    )
    print(f'Выхожу из функции movie_to_watch')

    # Prepare to handle user's choice on movie deletion
    user = update.effective_user
    query = update.callback_query
    print(f'query_data = {query.data}')

    # Check if the user wants to delete a movie from the watch list or favorite list
    if query.data == "delete_from_movie_to_watch_list" or query.data == "delete_from_favorite_list":
        return CHOOSE_MOVIE_TO_DELETE  # Indicating the next step in the conversation flow


# Tests
async def choose_movie_to_delete(update, context):
    """
    Prompts the user to enter the ID of a movie they wish to delete from their list.

    Returns:
        str: A constant representing the next step in the conversation flow.
    """

    print(f'Захожу в функцию choose_movie_to_delete')
    query = update.callback_query
    context.user_data[
        'state'] = CHOOSE_MOVIE_TO_DELETE  # Set the state to indicate the user is choosing a movie to delete
    context.user_data['delete_button'] = query.data  # Store the type of deletion requested

    # Save the type of list from which the user wants to delete a movie
    context.user_data["list_type"] = query.data

    # Check if the deletion is from the watch list or favorite list
    if query.data == "delete_from_movie_to_watch_list" or query.data == "delete_from_favorite_list":
        await update.callback_query.message.reply_text(
            "Write an ID of the movie you want to delete"
        )
        print(f'Выхожу из функции choose_movie_to_delete до return')
        print(f' сейчас в контексте List_type: {context.user_data["list_type"]}')
        return DELETE_FROM_LISTS  # Indicate the next step in the flow

    print(f' сейчас в контексте List_type: {context.user_data["list_type"]}')
    print(f'Выхожу из функции choose_movie_to_delete')
    print(f'Сейчас в контексте state: {context.user_data["state"]}')

    return DELETE_FROM_LISTS  # Default return if no specific deletion was requested


async def delete_from_list(update, context):
    """
    Handles the logic for deleting a movie from the user's list based on the provided ID.

    Returns:
        str: A constant indicating the end of the conversation handler.
    """

    print(f'Захожу в функцию delete_from_list')

    # Retrieve the type of list from which the user wants to delete a movie
    list_type = context.user_data.get('list_type')
    print(context.user_data["list_type"])
    print(f'list_type = {list_type}')

    user = update.effective_user
    context.user_data['state'] = DELETE_FROM_LISTS  # Update the state to indicate deletion
    movie_to_delete = update.message.text  # Get the movie ID from the user's message
    print(f'Сейчас в контексте state: {context.user_data["state"]}')
    print(f'Переменная movie_to_delete: {movie_to_delete}')
    context.user_data['movie_id'] = movie_to_delete  # Store the movie ID for later use
    print(f'Переменная context.user_data["movie_id"]: {context.user_data["movie_id"]}')

    # Acknowledge the deletion request to the user
    await update.message.reply_text(
        f"Thanks, {update.effective_chat.username}! Deleting: {movie_to_delete}..."
    )

    # Perform the deletion based on the type of list
    if list_type == "delete_from_movie_to_watch_list":
        del_movie_to_watch(user_id=user.id, movie_id=movie_to_delete)
    elif list_type == "delete_from_favorite_list":
        del_favorite_movies(user_id=user.id, movie_id=movie_to_delete)

    # Restart the conversation flow
    await start(update, context)
    return ConversationHandler.END  # End the conversation


async def start_movie_search(update, context):
    """
    Initiates the movie search conversation by prompting the user to enter a movie title.

    Returns:
        str: A constant indicating the next state of the conversation (ENTER_MOVIE).
    """

    # Set the user's current state to indicate they are entering a movie title
    context.user_data['state'] = ENTER_MOVIE

    # Prompt the user to write the movie title
    await update.callback_query.message.reply_text(
        'Write the movie title'
    )

    # Return the constant that indicates the next state
    return ENTER_MOVIE


async def save_movie_name(update, context):
    """
    Saves the user's movie search input and retrieves information about the movie.

    Returns:
        str: A constant indicating the next state of the conversation (ADD_TO_LISTS).
    """

    # Get the movie title from the user's message
    movie_for_search = update.message.text

    # Store the movie title in user data for later use
    context.user_data['movie'] = movie_for_search

    # Acknowledge the user's input
    await update.message.reply_text(
        f"Thanks, {update.effective_chat.username}! I'm searching your movie: {movie_for_search}"
    )

    # TODO: Добавить сортировку по рейтингу
    url_name_search = f'https://api.kinopoisk.dev/v1.4/movie/search?page=1&limit=10&query={movie_for_search}'
    request_movie_template = requests.get(url_name_search, headers=headers).json()['docs'][0]

    # Extract movie information from the API response
    name = request_movie_template['name']
    genres = request_movie_template['genres'][0]['name']
    year = request_movie_template['year']
    description = request_movie_template['description']
    poster = request_movie_template['poster']['url']
    rating = request_movie_template['rating']['kp']

    # Save the movie information in user data for future reference
    context.user_data['movie_info'] = {
        'name': name,
        'description': description,
        'year': year,
        'genres': genres,
        'rating': rating
    }

    # Prepare the message text to send to the user
    message_text = (
        f'- Title: {name}\n'
        f'- Year: {year}\n'
        f'- Description: {description}\n'
        f'- Rating: {rating}\n'
        f'- Genre: {genres}\n'
        f'- Poster: {poster}'
    )

    # Send the movie poster image and a caption to the chat
    caption = f"<b>{name}</b>\n\nGenres: {genres}\nYear: {year}\nDescription: {description}"
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=poster, caption=caption, parse_mode='HTML')
    # parse_mode allows the use of HTML formatting (useful for bold, italic, underlined text, etc.)

    # Prompt the user to decide whether to save the movie
    keyboard = get_save_movie_keyboard()
    await update.message.reply_text(
        "Do you want to save the movie?",
        reply_markup=keyboard
    )

    # Return the constant indicating the next state
    return ADD_TO_LISTS


async def add_to_lists(update, context):
    """
    Adds a movie to the user's favorite or 'to watch' lists based on the user's selection.

    Returns:
        str: A constant indicating the end of the conversation (ConversationHandler.END).
    """

    # Get the user who initiated the action
    user = update.effective_user
    query = update.callback_query

    # Check which list the user wants to add the movie to
    if query.data == "add_to_list_favorite_movie":
        movie_info = context.user_data.get('movie_info')
        if movie_info:
            # Add the movie to the favorite list
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
            # Add the movie to the 'to watch' list
            add_movie_to_watch(
                user_id=user.id,
                title=movie_info['name'],
                description=movie_info['description'],
                year=movie_info['year'],
                genre=movie_info['genres'],
                rating=movie_info['rating']
            )
        await query.message.reply_text(f'Movie "{movie_info["name"]}" successfully added to Movie to watch list!')

        # Restart the conversation flow
        await start(update, context)
    # In case of an unexpected query, restart the conversation flow
    else:
        await start(update, context)

    # End the conversation
    return ConversationHandler.END


async def unknown(update, context):
    """
    Handles unknown commands or text input from the user.

    Sends a reply to the user indicating that the command or text is not recognized,
    and provides options to restart the interaction.
    """

    # Get the main keyboard for navigation options
    keyboard = get_main_keyboard()
    # Send a response to the user indicating the command is not recognized
    await update.message.reply_text(
        f"Sorry, but I can't answer you :(\nLet's try again. What can I do for you?",
        reply_markup=keyboard
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles button callbacks from the user.

    Processes user interactions with buttons in the Telegram bot, directing them to
    appropriate functions based on the callback data received.
    """

    # Retrieve the callback query from the update
    query = update.callback_query

    # Handle different button actions based on the callback data
    if query.data == "movie_to_watch":
        await movie_to_watch(update, context)
    elif query.data == "favorite_movie":
        await favorite_movie(update, context)
    elif query.data.startswith("next_watch_page"):
        # Extract page number from callback data for pagination
        page_number = int(query.data.split('_')[-1])
        await movie_to_watch(update, context, page_number)
    elif query.data.startswith('prev_watch_page'):
        page_number = int(query.data.split('_')[-1])
        await movie_to_watch(update, context, page_number)
    elif query.data.startswith("next_favorite_page"):
        # Extract page number from callback data for pagination
        page_number = int(query.data.split('_')[-1])
        await favorite_movie(update, context, page_number)
    elif query.data.startswith('prev_favorite_page'):
        page_number = int(query.data.split('_')[-1])
        await favorite_movie(update, context, page_number)


if __name__ == '__main__':
    # Initialize the application with the provided Telegram bot token
    application = ApplicationBuilder().token(TG_TOKEN).build()

    # Command handler for the '/start' command
    start_handler = CommandHandler('start', start)

    # Callback query handlers for various actions
    start_movie_search_handler = CallbackQueryHandler(start_movie_search, pattern=r'^ask_movie_name$')
    random_movie_handler = CallbackQueryHandler(random_movie, pattern=r'^random_movie$')
    favorite_movie_handler = CallbackQueryHandler(favorite_movie, pattern=r'^favorite_movie$')
    movie_to_watch_handler = CallbackQueryHandler(movie_to_watch, pattern=r'^movie_to_watch$')

    # Conversation handler for the movie search flow
    search_conversation_handler = ConversationHandler(
        entry_points=[start_movie_search_handler],
        states={
            ENTER_MOVIE: [MessageHandler(filters.TEXT & (~filters.COMMAND), save_movie_name)],
            ADD_TO_LISTS: [CallbackQueryHandler(add_to_lists)]
        },
        fallbacks=[],
    )

    # Conversation handler for random movie selection
    random_conversation_handler = ConversationHandler(
        entry_points=[random_movie_handler],
        states={
            ADD_TO_LISTS: [CallbackQueryHandler(add_to_lists)]
        },
        fallbacks=[],
    )

    # Conversation handler for managing favorite movies
    favorite_movie_conversation_handler = ConversationHandler(
        entry_points=[favorite_movie_handler],
        states={
            CHOOSE_MOVIE_TO_DELETE: [CallbackQueryHandler(choose_movie_to_delete)],
            DELETE_FROM_LISTS: [MessageHandler(filters.TEXT & (~filters.COMMAND), delete_from_list)]
        },
        fallbacks=[],
    )

    # Conversation handler for managing movies to watch
    movie_to_watch_conversation_handler = ConversationHandler(
        entry_points=[movie_to_watch_handler],
        states={
            CHOOSE_MOVIE_TO_DELETE: [CallbackQueryHandler(choose_movie_to_delete)],
            DELETE_FROM_LISTS: [MessageHandler(filters.TEXT & (~filters.COMMAND), delete_from_list)]
        },
        fallbacks=[],
    )

    # Handler for unknown commands or messages
    unknown_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), unknown)

    # Add all handlers to the application
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

    # Start polling for updates
    application.run_polling()

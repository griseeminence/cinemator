from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Global variable for page number, initialized to None
page_number = None


def logger_in_out(f):
    """Decorator for logging function entry and exceptions."""
    from logging import getLogger
    logger = getLogger(__name__)

    def wrap(*args, **kwargs):
        try:
            logger.info(f'Entering function {f.__name__}')  # Log function entry
            return f(*args, **kwargs)
        except Exception as e:
            logger.exception(f'Error in handler {f.__name__}')  # Log exception details
            raise

    return wrap


# Function to create the main keyboard for the bot
def get_main_keyboard():
    """Creates the main keyboard with options for the user."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("Find Movie", callback_data="ask_movie_name")],
            [InlineKeyboardButton("Random Movie", callback_data="random_movie")],
            [InlineKeyboardButton("Favorite Movie", callback_data="favorite_movie")],
            [InlineKeyboardButton("Movie to watch", callback_data="movie_to_watch")],
        ],
    )


# Function to create a keyboard for saving movies
def get_save_movie_keyboard():
    """Creates a keyboard for saving movie options."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("Save to Favorite Movie", callback_data="add_to_list_favorite_movie")],
            [InlineKeyboardButton("Save to Movie to watch", callback_data="add_to_list_movie_to_watch")],
            [InlineKeyboardButton("Menu", callback_data="start")],
        ],
    )


# Function to create pagination keyboard for "Movies to Watch" list
def get_pagination_movie_to_watch_keyboard(page_number):
    """Creates a pagination keyboard for the 'Movies to Watch' list."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Next Page",
                callback_data=f"next_watch_page_{page_number + 1}"  # Increment page number for the next button
            )],
            [InlineKeyboardButton(
                text="Previous Page",
                callback_data=f"prev_watch_page_{page_number - 1}"  # Decrement page number for the previous button
            )],
            [InlineKeyboardButton(
                text="Delete Movie",
                callback_data=f"delete_from_movie_to_watch_list"  # Callback for deleting a movie
            )]
        ],
    )
    return keyboard


# Function to create pagination keyboard for the "Favorite Movies" list
def get_pagination_favorite_keyboard(page_number):
    """Creates a pagination keyboard for the 'Favorite Movies' list."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Следующая страница",
                callback_data=f"next_favorite_page_{page_number + 1}"  # Increment page number for the next button
            )],
            [InlineKeyboardButton(
                text="Предыдущая страница",
                callback_data=f"prev_favorite_page_{page_number - 1}"  # Decrement page number for the previous button
            )],
            [InlineKeyboardButton(
                text="Удалить фильм",
                callback_data=f"delete_from_favorite_list"  # Callback for deleting a movie
            )]
        ],
    )

    return keyboard

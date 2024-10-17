# Cinemator Telegram Bot

Cinemator is a Telegram bot that allows users to search for movies, save them to their favorite
lists, and manage their watchlists. It utilizes the Kinopoisk API to fetch movie data and SQLite
for local data storage.

## Features

- **Search Movies**: Users can search for movies by name.
- **Random Movie Recommendation**: Users can get a random movie from the top 250 list.
- **Favorites Management**: Users can save and manage their favorite movies.
- **Watchlist Management**: Users can add movies to their "watch later" list and manage it.
- **Pagination**: The bot supports pagination for long lists of movies.

## Technologies Used

- Python 3.8+
- `python-telegram-bot` v22
- SQLite for database management
- Kinopoisk API for movie data

## Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/cinemator.git
   cd cinemator
   ```

6. Install dependencies:
   ```
    pip install -r requirements.txt
   ```

5. Create a .env file in the root directory with the following variables:
   ```
    TG_TOKEN=your_telegram_bot_token
    KINOPOISK_TOKEN=your_kinopoisk_api_key
   ```


4. Initialize the database:

- You can initialize the database by calling the init_db() function.
  This will create the necessary tables.

# Database Schema

The bot uses SQLite with the following tables:

- users: Stores user information.
- favorite_movies: Stores information about favorite movies.
- movies_to_watch: Stores information about movies users want to watch.
- user_favorite_movies: Associates users with their favorite movies.
- user_movies_to_watch: Associates users with their watchlist movies.

# Usage

- Start the bot and follow the prompts to search for movies, save them, and manage your lists.
- Use the following commands to interact with the bot:
    - /start: Start the bot and show the main menu.
    - Use inline buttons to navigate through movie options.

# Code Structure

- core.py: The main file where the bot is instantiated and commands are defined.
- database.py: Contains functions for database operations such as adding, deleting, and fetching movies.
- tools.py: Utility functions and decorators for logging and managing connections.
- constants.py: Contains constants used throughout the bot.
- requirements.txt: Lists all the dependencies needed to run the bot.

# Contributing

- Contributions are welcome! If you have suggestions for improvements or new features, please
  open an issue or submit a pull request.

# License

- This project is licensed under the MIT License.

# Acknowledgments

- Thanks to the Kinopoisk API for providing movie data.
- Thanks to the python-telegram-bot library for making bot development easy.
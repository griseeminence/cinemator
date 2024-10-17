from dotenv import dotenv_values

# Load environment variables from the .env file
env_variables = dotenv_values(".env")
TG_TOKEN = env_variables.get("TG_TOKEN")  # Telegram bot token
KINOPOISK_TOKEN = env_variables.get("KINOPOISK_TOKEN")  # Kinopoisk API token

# Set up headers for API requests
headers = {
    "accept": "application/json",  # Specify that we want JSON responses
    "X-API-KEY": KINOPOISK_TOKEN  # Include the Kinopoisk API token in headers
}

# Constants for various actions
ENTER_MOVIE = 0
ADD_TO_LISTS = 1
ADD_RANDOM_TO_LISTS = 0
DELETE_FROM_LISTS = 1
CHOOSE_MOVIE_TO_DELETE = 0

# URL for fetching the top 250 movies from Kinopoisk
url_random_250 = (
    'https://api.kinopoisk.dev/v1.4/movie?page=1&limit=250&'
    'selectFields=id&selectFields=top250&selectFields=name&'
    'selectFields=description&selectFields=year&selectFields=rating&'
    'selectFields=poster&selectFields=genres&selectFields=type&'
    'sortField=top250&sortType=-1&type=movie'
)

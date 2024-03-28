from dotenv import dotenv_values

env_variables = dotenv_values(".env")
TG_TOKEN = env_variables.get("TG_TOKEN")
KINOPOISK_TOKEN = env_variables.get("KINOPOISK_TOKEN")

headers = {
    "accept": "application/json",
    "X-API-KEY": KINOPOISK_TOKEN
}

ENTER_MOVIE = 0
ADD_TO_LISTS = 1
ADD_RANDOM_TO_LISTS = 0
DELETE_FROM_LISTS = 1
CHOOSE_MOVIE_TO_DELETE = 0

url_random_250 = 'https://api.kinopoisk.dev/v1.4/movie?page=1&limit=250&selectFields=id&selectFields=top250&selectFields=name&selectFields=description&selectFields=year&selectFields=rating&selectFields=poster&selectFields=genres&selectFields=type&sortField=top250&sortType=-1&type=movie'

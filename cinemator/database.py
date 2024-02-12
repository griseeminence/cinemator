import sqlite3

# TODO: создать реальные таблицы для бота -------------------- СДЕЛАНО
# TODO: создать методы для записи данных в таблицы

__connection = None


def ensure_connection(func):
    """
    Декоратор позволяет не открывать соединение в каждой функции явно.
    Декоратор открывает соединение (путём with...), передаёт его в функцию, к которой он применён.
    А после выхода из with - декортатор закрывает соединения.
    Это делает подключения к базе данных более безопасными.
    """

    def inner(*args, **kwargs):
        with sqlite3.connect('cinemator.db') as conn:
            res = func(*args, conn=conn, **kwargs)
        return res

    return inner


@ensure_connection
def init_db(conn, force: bool = False):
    c = conn.cursor()

    if force:
        #        c.execute('DROP TABLE IF EXISTS user_message')
        c.execute('DROP TABLE IF EXISTS users')
        c.execute('DROP TABLE IF EXISTS favorite_movies')
        c.execute('DROP TABLE IF EXISTS movies_to_watch')
        c.execute('DROP TABLE IF EXISTS user_favorite_movies')
        c.execute('DROP TABLE IF EXISTS user_movies_to_watch')

    #     c.execute('''
    #         CREATE TABLE IF NOT EXISTS user_message (
    #             id INTEGER PRIMARY KEY,
    #             user_id INTEGER NOT NULL,
    #             text TEXT NOT NULL
    #         )
    # ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            chat_id INTEGER NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS favorite_movies (
            movie_id INTEGER PRIMARY KEY,
            title TEXT NOT NULL UNIQUE,
            description TEXT DEFAULT 'Description of the movie is missing',
            year INTEGER DEFAULT 0,
            genre TEXT DEFAULT 'No information about genre',
            rating INTEGER DEFAULT 0
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS movies_to_watch (
            movie_id INTEGER PRIMARY KEY,
            title TEXT NOT NULL UNIQUE,
            description TEXT DEFAULT 'Description of the movie is missing',
            year INTEGER DEFAULT 0,
            genre TEXT DEFAULT 'No information about genre',
            rating INTEGER DEFAULT 0
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS user_favorite_movies (
            user_id INTEGER,
            movie_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (movie_id) REFERENCES favorite_movies(movie_id),
            PRIMARY KEY (user_id, movie_id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS user_movies_to_watch (
            user_id INTEGER,
            movie_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (movie_id) REFERENCES movies_to_watch(movie_id),
            PRIMARY KEY (user_id, movie_id)
        )
    ''')

    conn.commit()


@ensure_connection
def add_movie_to_watch(conn, user_id, title, description, year, genre, rating):
    c = conn.cursor()

    c.execute('''
        SELECT 1 FROM user_movies_to_watch WHERE user_id = ? AND EXISTS (
            SELECT 1 FROM movies_to_watch WHERE title = ?
        )
    ''', (user_id, title))

    if c.fetchone():
        print('Фильм уже добавлен в список "Смотреть позже" для этого пользователя.')
        return False

        # Добавляем фильм в таблицу favorite_movies
    c.execute('INSERT INTO movies_to_watch (title, description, year, genre, rating) VALUES (?, ?, ?, ?, ?)',
              (title, description, year, genre, rating))
    conn.commit()

    # Получаем идентификатор фильма, который только что добавили
    movie_id = c.lastrowid

    # Затем создаем связь между пользователем и фильмом в таблице user_favorite_movies
    c.execute('INSERT INTO user_movies_to_watch (user_id, movie_id) VALUES (?, ?)',
              (user_id, movie_id))
    conn.commit()

    print("Фильм успешно добавлен в список любимых для этого пользователя.")
    return True


@ensure_connection
def add_favorite_movie(conn, user_id, title, description, year, genre, rating):
    c = conn.cursor()

    # Проверяем, есть ли уже такой фильм в списке любимых для данного пользователя
    c.execute('''
        SELECT 1 FROM user_favorite_movies WHERE user_id = ? AND EXISTS (
            SELECT 1 FROM favorite_movies WHERE title = ?
        )
    ''', (user_id, title))

    if c.fetchone():
        print("Фильм уже добавлен в список любимых для этого пользователя.")
        return False

    # Добавляем фильм в таблицу favorite_movies
    c.execute('INSERT INTO favorite_movies (title, description, year, genre, rating) VALUES (?, ?, ?, ?, ?)',
              (title, description, year, genre, rating))
    conn.commit()

    # Получаем идентификатор фильма, который только что добавили
    movie_id = c.lastrowid

    # Затем создаем связь между пользователем и фильмом в таблице user_favorite_movies
    c.execute('INSERT INTO user_favorite_movies (user_id, movie_id) VALUES (?, ?)',
              (user_id, movie_id))
    conn.commit()

    print("Фильм успешно добавлен в список любимых для этого пользователя.")
    return True


@ensure_connection
def get_movies_to_watch(conn, user_id):
    c = conn.cursor()
    c.execute('''
        SELECT m.title, m.description, m.year, m.genre, m.rating
        FROM movies_to_watch m
        INNER JOIN user_movies_to_watch um ON m.movie_id = um.movie_id
        WHERE um.user_id = ?
    ''', (user_id,))
    return c.fetchall()


@ensure_connection
def get_favorite_movies(conn, user_id):
    c = conn.cursor()
    c.execute('''
        SELECT m.title, m.description, m.year, m.genre, m.rating
        FROM favorite_movies m
        INNER JOIN user_favorite_movies um ON m.movie_id = um.movie_id
        WHERE um.user_id = ?
    ''', (user_id,))
    return c.fetchall()


# @ensure_connection
# def add_message(conn, user_id: int, text: str):
#     c = conn.cursor()
#     c.execute('INSERT INTO user_message (user_id, text) VALUES (?, ?)', (user_id, text))
#     conn.commit()
#
#
# @ensure_connection
# def count_message(conn, user_id: int):
#     c = conn.cursor()
#     c.execute('SELECT COUNT(*) FROM user_message WHERE user_id = ?', (user_id,))
#     (res,) = c.fetchall()  # fetchall отдаёт список результатов
#     return res
#
#
# @ensure_connection
# def list_messages(conn, user_id: int, limit: int = 10):
#     c = conn.cursor()
#     c.execute('SELECT id, text FROM user_message WHERE user_id = ? ORDER BY id DESC LIMIT ?', (user_id, limit))
#     return c.fetchall()


if __name__ == '__main__':
    init_db()  # Проверка, есть ли база

    add_favorite_movie(
        user_id=444123456,
        title='Тестовый любимый фильм22222',
        description='Тестовое описание2222',
        year=1111,
        genre='Тестовый жанр2222',
        rating=3
    )

    test_favorite_movie = get_favorite_movies(user_id=123456)
    for i in test_favorite_movie:
        print(*i)


    add_movie_to_watch(
        user_id=123456,
        title='Тестовый любимый фильм2',
        description='Тестовое описание2',
        year=4121,
        genre='Тестовый жанр2',
        rating=3
    )

    test_movie_to_watch = get_movies_to_watch(user_id=123456)
    for i in test_movie_to_watch:
        print(*i)

    # add_message(user_id=123, text='keke222keke')  # Добавляем сообщение
    #
    # r = count_message(user_id=123)  # Считаем количество сообщений у пользователя
    # print(r)
    #
    # r = list_messages(user_id=123, limit=3)
    # for i in r:
    #     print(i)

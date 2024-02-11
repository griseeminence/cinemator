import sqlite3

#TODO: создать реальные таблицы для бота -------------------- СДЕЛАНО
#TODO: создать методы для записи данных в таблицы

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
        c.execute('DROP TABLE IF EXISTS user_message')
        c.execute('DROP TABLE IF EXISTS users')
        c.execute('DROP TABLE IF EXISTS favorite_movies')
        c.execute('DROP TABLE IF EXISTS movies_to_watch')
        c.execute('DROP TABLE IF EXISTS user_favorite_movies')
        c.execute('DROP TABLE IF EXISTS user_movies_to_watch')

    c.execute('''
        CREATE TABLE IF NOT EXISTS user_message (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL
        )
''')

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
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            year INTEGER NOT NULL,
            genre TEXT NOT NULL,
            rating INTEGER NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS movies_to_watch (
            movie_id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            year INTEGER NOT NULL,
            genre TEXT NOT NULL,
            rating INTEGER NOT NULL
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
def add_message(conn, user_id: int, text: str):
    c = conn.cursor()
    c.execute('INSERT INTO user_message (user_id, text) VALUES (?, ?)', (user_id, text))
    conn.commit()

@ensure_connection
def count_message(conn, user_id: int):
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM user_message WHERE user_id = ?', (user_id,))
    (res,) = c.fetchall()  # fetchall отдаёт список результатов
    return res

@ensure_connection
def list_messages(conn, user_id: int, limit: int = 10):
    c = conn.cursor()
    c.execute('SELECT id, text FROM user_message WHERE user_id = ? ORDER BY id DESC LIMIT ?', (user_id, limit))
    return c.fetchall()

if __name__ == '__main__':
    init_db()  # Проверка, есть ли база
    add_message(user_id=123, text='keke222keke')  # Добавляем сообщение

    r = count_message(user_id=123)  # Считаем количество сообщений у пользователя
    print(r)

    r = list_messages(user_id=123, limit=3)
    for i in r:
        print(i)
import sqlite3

__connection = None


def get_connection():
    global __connection
    if __connection is None:
        __connection = sqlite3.connect('cinemator.db')
    return __connection


def init_db(force: bool = False):
    conn = get_connection()
    c = conn.cursor()

    # TODO: Добавить таблицы с инфо о пользователе и другие

    if force:
        c.execute('DROP TABLE IF EXISTS user_movies')

    c.execute('''
        CREATE TABLE IF NOT EXISTS user_message (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL
        )
''')

    conn.commit()


def add_message(user_id: int, text: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT INTO user_message (user_id, text) VALUES (?, ?)', (user_id, text))
    conn.commit()


def count_message(user_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM user_message WHERE user_id = ?', (user_id,))
    (res,) = c.fetchall() #fetchall отдаёт список результатов
    conn.commit()
    return res



if __name__ == '__main__':
    init_db()  # Проверка, есть ли база
    add_message(user_id=123, text='kek')  # Добавляем сообщение

    r = count_message(user_id=123)  # Считаем количество сообщений у пользователя
    print(r)

import sqlite3

#TODO: создать реальные таблицы для бота

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
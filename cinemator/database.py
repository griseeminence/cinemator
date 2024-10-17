import sqlite3

__connection = None


def ensure_connection(func):
    """
    Decorator to manage database connections.

    This decorator opens a connection to the SQLite database when the decorated
    function is called, passes the connection to the function, and ensures that
    the connection is closed after the function completes. This approach enhances
    security and reduces the risk of connection leaks.
    """

    def inner(*args, **kwargs):
        with sqlite3.connect('cinemator.db') as conn:   # Open connection to the database
            res = func(*args, conn=conn, **kwargs)  # Pass the connection to the function
        return res

    return inner


@ensure_connection
def init_db(conn, force: bool = False):
    """
    Initializes the database by creating necessary tables.

    Args:
        conn: The SQLite database connection.
        force: A boolean flag indicating whether to drop existing tables before
               creating new ones. Defaults to False.
    """

    c = conn.cursor()  # Create a cursor object for executing SQL commands

    if force:
        # Optionally drop existing tables
        c.execute('DROP TABLE IF EXISTS users')
        c.execute('DROP TABLE IF EXISTS favorite_movies')
        c.execute('DROP TABLE IF EXISTS movies_to_watch')
        c.execute('DROP TABLE IF EXISTS user_favorite_movies')
        c.execute('DROP TABLE IF EXISTS user_movies_to_watch')

    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            chat_id INTEGER NOT NULL
        )
    ''')

    # Create favorite_movies table
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

    # Create movies_to_watch table
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

    # Create user_favorite_movies table
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_favorite_movies (
            user_id INTEGER,
            movie_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (movie_id) REFERENCES favorite_movies(movie_id),
            PRIMARY KEY (user_id, movie_id)
        )
    ''')

    # Create user_movies_to_watch table
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_movies_to_watch (
            user_id INTEGER,
            movie_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (movie_id) REFERENCES movies_to_watch(movie_id),
            PRIMARY KEY (user_id, movie_id)
        )
    ''')

    conn.commit()  # Commit the transaction to save changes to the database


@ensure_connection
def add_movie_to_watch(conn, user_id, title, description, year, genre, rating):
    """
    Adds a movie to the user's "To Watch" list.

    Args:
        conn: The SQLite database connection.
        user_id: The ID of the user adding the movie.
        title: The title of the movie.
        description: A brief description of the movie.
        year: The release year of the movie.
        genre: The genre of the movie.
        rating: The movie's rating.

    Returns:
        True if the movie was added successfully, False otherwise.
    """

    c = conn.cursor()

    # Check if the movie is already in the user's "To Watch" list
    c.execute('''
        SELECT 1 FROM user_movies_to_watch WHERE user_id = ? AND EXISTS (
            SELECT 1 FROM movies_to_watch WHERE title = ?
        )
    ''', (user_id, title))

    if c.fetchone():
        print('The movie is already in the "To Watch" list for this user.')
        return False

    # Add the movie to the movies_to_watch table
    c.execute('INSERT INTO movies_to_watch (title, description, year, genre, rating) VALUES (?, ?, ?, ?, ?)',
              (title, description, year, genre, rating))
    conn.commit()

    # Get the ID of the movie that was just added
    movie_id = c.lastrowid

    # Create a link between the user and the movie in the user_movies_to_watch table
    c.execute('INSERT INTO user_movies_to_watch (user_id, movie_id) VALUES (?, ?)',
              (user_id, movie_id))
    conn.commit()

    print("The movie has been successfully added to the 'To Watch' list for this user.")
    return True


@ensure_connection
def add_favorite_movie(conn, user_id, title, description, year, genre, rating):
    """
    Adds a movie to the user's favorites list.

    Args:
        conn: The SQLite database connection.
        user_id: The ID of the user adding the movie.
        title: The title of the movie.
        description: A brief description of the movie.
        year: The release year of the movie.
        genre: The genre of the movie.
        rating: The movie's rating.

    Returns:
        True if the movie was added successfully, False otherwise.
    """

    c = conn.cursor()

    # Check if the movie is already in the user's favorites
    c.execute('''
        SELECT 1 FROM user_favorite_movies WHERE user_id = ? AND EXISTS (
            SELECT 1 FROM favorite_movies WHERE title = ?
        )
    ''', (user_id, title))

    if c.fetchone():
        print("The movie is already in the favorites list for this user.")
        return False

    # Add the movie to the favorite_movies table
    c.execute('INSERT INTO favorite_movies (title, description, year, genre, rating) VALUES (?, ?, ?, ?, ?)',
              (title, description, year, genre, rating))
    conn.commit()


    # Get the ID of the movie that was just added
    movie_id = c.lastrowid

    # Create a link between the user and the movie in the user_favorite_movies table
    c.execute('INSERT INTO user_favorite_movies (user_id, movie_id) VALUES (?, ?)',
              (user_id, movie_id))
    conn.commit()

    print("The movie has been successfully added to the favorites list for this user.")
    return True


@ensure_connection
def del_movie_to_watch(conn, user_id, movie_id):
    """
    Deletes a movie from the user's "To Watch" list.

    Args:
        conn: The SQLite database connection.
        user_id: The ID of the user removing the movie.
        movie_id: The ID of the movie to remove.

    Returns:
        True if the movie was removed successfully, False otherwise.
    """

    c = conn.cursor()

    # Check if the movie exists in the user's "To Watch" list
    c.execute('''
        SELECT 1 FROM user_movies_to_watch WHERE user_id = ? AND EXISTS (
            SELECT 1 FROM movies_to_watch WHERE movie_id = ?
        )
    ''', (user_id, movie_id))

    if not c.fetchone():
        print("The movie is not in your 'To Watch' list!")
        return False

    # Delete the link between the user and the movie in the user_movies_to_watch table
    c.execute('DELETE FROM user_movies_to_watch WHERE user_id = ? AND movie_id = ?', (user_id, movie_id))
    conn.commit()

    print("The movie has been successfully removed from your 'To Watch' list.")
    return True


@ensure_connection
def del_favorite_movies(conn, user_id, movie_id):
    """
    Deletes a movie from the user's favorites list.

    Args:
        conn: The SQLite database connection.
        user_id: The ID of the user removing the movie.
        movie_id: The ID of the movie to remove.

    Returns:
        True if the movie was removed successfully, False otherwise.
    """

    c = conn.cursor()

    # Check if the movie exists in the user's favorites
    c.execute('''
        SELECT 1 FROM user_favorite_movies WHERE user_id = ? AND EXISTS (
            SELECT 1 FROM favorite_movies WHERE movie_id = ?
        )
    ''', (user_id, movie_id))

    if not c.fetchone():
        print("The movie is not in your favorites list!")
        return False

    # Delete the link between the user and the movie in the user_favorite_movies table
    c.execute('DELETE FROM user_favorite_movies WHERE user_id = ? AND movie_id = ?', (user_id, movie_id))
    conn.commit()

    print("The movie has been successfully removed from your favorites list.")
    return True


@ensure_connection
def get_movies_to_watch(conn, user_id, limit=1, offset=0):
    """
    Retrieves movies from the user's "To Watch" list.

    Args:
        conn: The SQLite database connection.
        user_id: The ID of the user retrieving movies.
        limit: The maximum number of movies to retrieve.
        offset: The number of movies to skip before starting to retrieve.

    Returns:
        A list of movies in the user's "To Watch" list.
    """

    c = conn.cursor()
    c.execute('''
        SELECT um.movie_id, m.title, m.description, m.year, m.genre, m.rating
        FROM movies_to_watch m
        INNER JOIN user_movies_to_watch um ON m.movie_id = um.movie_id
        WHERE um.user_id = ?
        LIMIT ?
        OFFSET ?
    ''', (user_id, limit, offset))
    return c.fetchall()


@ensure_connection
def get_favorite_movies(conn, user_id, limit=1, offset=0):
    """
    Retrieves movies from the user's favorites list.

    Args:
        conn: The SQLite database connection.
        user_id: The ID of the user retrieving movies.
        limit: The maximum number of movies to retrieve.
        offset: The number of movies to skip before starting to retrieve.

    Returns:
        A list of movies in the user's favorites list.
    """

    c = conn.cursor()
    c.execute('''
        SELECT um.movie_id, m.title, m.description, m.year, m.genre, m.rating
        FROM favorite_movies m
        INNER JOIN user_favorite_movies um ON m.movie_id = um.movie_id
        WHERE um.user_id = ?
        LIMIT ?
        OFFSET ?
    ''', (user_id, limit, offset))
    return c.fetchall()


if __name__ == '__main__':
    init_db()

    # add_favorite_movie(
    #     user_id=444123456,
    #     title='Тестовый любимый фильм22222',
    #     description='Тестовое описание2222',
    #     year=1111,
    #     genre='Тестовый жанр2222',
    #     rating=3
    # )
    #
    # add_movie_to_watch(
    #     user_id=123456,
    #     title='Тестовый любимый фильм2',
    #     description='Тестовое описание2',
    #     year=4121,
    #     genre='Тестовый жанр2',
    #     rating=3
    # )

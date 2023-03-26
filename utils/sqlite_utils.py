import sqlite3
from sqlite3 import Error
import os

def setup_cache(cache_location: str):
    """ create a database connection to a SQLite database """
    db_file = os.path.join(cache_location, 'cache.mbtiles')

    if os.path.isfile(db_file):
        return

    conn = None
    try:
        conn = sqlite3.connect(db_file)
        conn.execute('''
        CREATE TABLE tiles (
            tileset TEXT NOT NULL,
            x INTEGER NOT NULL,
            y INTEGER NOT NULL,
            z INTEGER NOT NULL,
            data BLOB,
            PRIMARY KEY (tileset, x, y, z)
        );
        ''')
        print(sqlite3.version)
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()

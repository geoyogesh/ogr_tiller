import sqlite3
from sqlite3 import Error
import os
from typing import Any, List
import glob 
from rich import print

# setup tile cache
cache_location = None
db_file = None


def update_cache(tileset: str, x: int, y: int, z: int, data: Any):  
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        sql = '''
        INSERT INTO tiles(tileset,x,y,z,data)
              VALUES(?,?,?,?,?) 
        '''
        conn.execute(sql, (tileset, x, y, z, data))
        conn.commit()
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()

def update_multiple_cache(rows: List[Any]):  
    # [(tileset, x, y, z, data)]
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        sql = '''
        INSERT INTO tiles(tileset,x,y,z,data)
              VALUES(?,?,?,?,?) 
        '''
        conn.executemany(sql, rows)
        conn.commit()
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()


def read_cache(tileset: str, x: int, y: int, z: int):
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        sql = """SELECT data from tiles where tileset = ? and x = ? and y = ? and z = ? """
        cursor.execute(sql, (tileset, x, y, z))
        record = cursor.fetchone()
        result = None
        if record is None:
            result = None
        else:
            result = record[0]
        cursor.close()
        return result

    except sqlite3.Error as error:
        print("Failed to read data from sqlite table", error)
    finally:
        if conn:
            conn.close()


def cleanup_mbtile_cache(cache_folder):
    db_file_pattern = os.path.join(cache_folder, 'cache.*')
    files = glob.glob(db_file_pattern, recursive=False)
    for file in files:
        if os.path.isfile(file):
            os.remove(file)


def setup_mbtile_cache(cache_folder):
    global cache_location, db_file

    # update global variablea
    cache_location = cache_folder
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
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()

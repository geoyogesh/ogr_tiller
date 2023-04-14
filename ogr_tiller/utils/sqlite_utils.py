import sqlite3
from sqlite3 import Error
import os
from typing import Any, List
import glob 
from rich import print
import json
from ogr_tiller.poco.tileset_manifest import TilesetManifest

# setup tile cache
cache_location = None
tileset_db_files = {}


def update_cache(tileset: str, x: int, y: int, z: int, tile_data: Any):  
    conn = None
    try:
        conn = sqlite3.connect(tileset_db_files[tileset])
        sql = '''
        INSERT INTO tiles(tile_row,tile_column,zoom_level,tile_data)
              VALUES(?,?,?,?) 
        '''
        conn.execute(sql, (x, y, z, tile_data))
        conn.commit()
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()

def update_multiple_cache(tileset: str, rows: List[Any]):  
    # [(tileset, x, y, z, tile_data)]
    conn = None
    try:
        conn = sqlite3.connect(tileset_db_files[tileset])
        sql = '''
        INSERT INTO tiles(tile_row,tile_column,zoom_level,tile_data)
              VALUES(?,?,?,?) 
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
        conn = sqlite3.connect(tileset_db_files[tileset])
        cursor = conn.cursor()

        sql = """SELECT tile_data from tiles where tile_row = ? and tile_column = ? and zoom_level = ? """
        cursor.execute(sql, (x, y, z))
        record = cursor.fetchone()
        result = None
        if record is None:
            result = None
        else:
            result = record[0]
        cursor.close()
        return result

    except sqlite3.Error as error:
        print("Failed to read tile_data from sqlite table", error)
    finally:
        if conn:
            conn.close()


def cleanup_mbtile_cache(cache_folder):
    db_file_pattern = os.path.join(cache_folder, '*.*')
    files = glob.glob(db_file_pattern, recursive=False)
    for file in files:
        if os.path.isfile(file) and not file.endswith('.gitkeep'):
            os.remove(file)


def setup_mbtile_cache(tileset: str, cache_folder: str, tilejson: any):
    global cache_location, tileset_db_files

    def process_value(key, val):
        if key == 'vector_layers':
            return ['json', json.dumps({'vector_layers': val})]
        if type(val) is dict:
            return [key, val.__repr__()]
        if type(val) is list:
            formated = [str(item) for item in val]
            return [key, ','.join(formated)]
        if type(val) is tuple:
            formated = [str(item) for item in list(val)]
            return [key, ','.join(formated)]
        if type(val) is int:
            return [key, str(val)]
        return [key, val]

    # update global variablea
    cache_location = cache_folder
    tileset_db_files[tileset] = os.path.join(cache_location, f'{tileset}.mbtiles')

    if os.path.isfile(tileset_db_files[tileset]):
        return

    conn = None
    try:
        conn = sqlite3.connect(tileset_db_files[tileset])
        conn.execute('''
        CREATE TABLE tiles (
            tile_row INTEGER NOT NULL,
            tile_column INTEGER NOT NULL,
            zoom_level INTEGER NOT NULL,
            tile_data BLOB,
            PRIMARY KEY (tile_row, tile_column, zoom_level)
        );
        ''')
        conn.execute('CREATE TABLE metadata (name text, value text);')
        conn.commit()
        manifest_rows = [ process_value(k, v) for k, v in tilejson.items()]
        conn.executemany('INSERT INTO metadata(name,value) VALUES(?,?);', manifest_rows)
        conn.commit()
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()

def update_metadata():
    pass
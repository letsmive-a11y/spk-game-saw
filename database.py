import sqlite3
from config import DATABASE

def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(sql_path='database/spk_game.sql'):
    conn = get_connection()
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql = f.read()
    conn.executescript(sql)
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print('Database initialized.')

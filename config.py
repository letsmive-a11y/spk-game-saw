# config.py
import psycopg2

def connect_db():
    return psycopg2.connect(
        host="localhost",
        database="spk_game",    
        user="postgres",
        password="admin",
        port=5432,
        options="-c timezone=Asia/Jakarta"
    )
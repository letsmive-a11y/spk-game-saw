# config.py
import os
import psycopg2

def connect_db():
    database_url = os.environ.get("DATABASE_URL")

    # Kalau di Railway, pakai DATABASE_URL
    if database_url:
        return psycopg2.connect(database_url)

    # Kalau di laptop, pakai database lokal
    return psycopg2.connect(
        host="localhost",
        database="spk_game",
        user="postgres",
        password="admin",
        port=5432,
        options="-c timezone=Asia/Jakarta"
    )
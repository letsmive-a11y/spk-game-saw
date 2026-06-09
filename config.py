import os
import psycopg2

def connect_db():
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        return psycopg2.connect(database_url)

    return psycopg2.connect(
        host="localhost",
        database="spk_game",
        user="postgres",
        password="admin",
        port=5432
    )
import os
import sqlite3

def create_database():# Настройка базы данных SQLite для хранения пользователей
    if not os.path.exists("./database/database.db"):
        conn = sqlite3.connect("./database/database.db")
        cursor = conn.cursor()
        # Создаём таблицу, если её ещё нет
        cursor.execute("CREATE TABLE IF NOT EXISTS users (id INT PRIMARY KEY, username VARCHAR(100), link VARCHAR(300));")
        conn.commit()
        conn.close()


def insert_database(user_id, username, link):
    conn = sqlite3.connect("./database/database.db")
    cursor = conn.cursor()
    cursor.execute(f"INSERT OR IGNORE INTO users (id, username, link) VALUES (?, ?, ?)",(user_id, username, link))
    conn.commit()
    conn.close()
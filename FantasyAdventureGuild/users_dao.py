import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "FantasyAdventureGuild.db"


def new_user(p_username, p_password, p_role):

    query = "INSERT INTO users (username, password, role) VALUES (?,?,?)"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(query, (p_username, p_password, p_role))
    conn.commit()
    cursor.close()
    conn.close()
    
def get_id_by_username(p_username):
    
    query = "SELECT id FROM users WHERE users.username = ?"

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_username,))

    db_user = cursor.fetchone()

    conn.commit()
    cursor.close()
    conn.close()

    return db_user


def get_user_by_username(p_username):

    query = "SELECT id, username, password, role FROM users WHERE username = ?"

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_username,))
    db_user = cursor.fetchone()

    cursor.close()
    conn.close()

    return db_user


def get_user_by_id(p_id):

    query = "SELECT id, username, password, role FROM users WHERE id = ?"

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_id,))
    db_user = cursor.fetchone()

    cursor.close()
    conn.close()

    return db_user


def username_exists(p_username):
    
    query = "SELECT 1 FROM users WHERE username = ? LIMIT 1"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(query, (p_username,))
    db_user = cursor.fetchone()

    cursor.close()
    conn.close()

    return db_user is not None
    

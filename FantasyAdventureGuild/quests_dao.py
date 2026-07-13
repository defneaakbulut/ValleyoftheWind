import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "FantasyAdventureGuild.db"


def get_quests():

    query = "SELECT id, title, duration_minutes, quest_type, difficulty, description, image_filename, created_by FROM quests ORDER BY id"

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query)
    db_quests = cursor.fetchall()

    cursor.close()
    conn.close()

    return db_quests


def new_quest(p_title, p_duration, p_difficulty, p_description, p_quest_type, p_image_filename, p_created_by):

    query = "INSERT INTO quests (title, duration_minutes, difficulty, description, quest_type, image_filename, created_by) VALUES (?,?,?,?,?,?,?)"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(query, (p_title, p_duration, p_difficulty, p_description, p_quest_type, p_image_filename, p_created_by))
    conn.commit()
    cursor.close()
    conn.close()

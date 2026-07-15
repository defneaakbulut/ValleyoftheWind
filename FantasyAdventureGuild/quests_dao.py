import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent.parent / "FantasyAdventureGuild.db"
ROLE_CAPACITIES = {
    "warrior": 4,
    "mage": 3,
    "healer": 2,
}


def add_role_stats(p_session):

    session_id = p_session["session_id"] if "session_id" in p_session else p_session["id"]
    participations = get_participations_by_session(session_id)

    role_counts = {"warrior": 0, "mage": 0, "healer": 0}

    for participation in participations:
        role_counts[participation["selected_role"]] += int(participation["reserved_places"])

    most_requested_count = max(role_counts.values())

    p_session["warrior_taken"] = role_counts["warrior"]
    p_session["mage_taken"] = role_counts["mage"]
    p_session["healer_taken"] = role_counts["healer"]
    p_session["total_reserved_places"] = sum(role_counts.values())
    p_session["participation_count"] = len(participations)
    p_session["most_requested_roles"] = [
        role
        for role, count in role_counts.items()
        if count == most_requested_count and count > 0
    ]
    p_session["taken_roles"] = ",".join([
        role
        for role, capacity in ROLE_CAPACITIES.items()
        if role_counts[role] >= capacity
    ])
    return p_session


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


def get_quests_by_guild_master(p_guild_master_id):

    query = "SELECT id, title, duration_minutes FROM quests WHERE created_by = ? ORDER BY id"

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_guild_master_id,))
    db_quests = cursor.fetchall()

    cursor.close()
    conn.close()

    quests = []

    for quest in db_quests:
        quests.append({
            "id": quest["id"],
            "title": quest["title"],
            "duration_minutes": quest["duration_minutes"],
            "sessions": get_sessions_by_quest_id(quest["id"]),
        })

    return quests


def get_quest_sessions():

    query = 'SELECT quest_sessions.id AS session_id, quest_sessions.quest_id,quest_sessions.day_of_week, quest_sessions.start_time, quest_sessions.location, quests.title, quests.duration_minutes, quests.quest_type, quests.difficulty, quests.description, quests.image_filename FROM quest_sessions JOIN quests ON quest_sessions.quest_id = quests.id ORDER BY quest_sessions.day_of_week, quest_sessions.start_time'

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query)
    db_sessions = cursor.fetchall()

    cursor.close()
    conn.close()

    return [add_role_stats(dict(session)) for session in db_sessions]


def get_platform_statistics():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    total_adventurers = cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'adventurer'").fetchone()[0]
    total_quests = cursor.execute("SELECT COUNT(*) FROM quests").fetchone()[0]
    total_sessions = cursor.execute("SELECT COUNT(*) FROM quest_sessions").fetchone()[0]
    total_participations = cursor.execute("SELECT COUNT(*) FROM participations").fetchone()[0]

    reserved_places = { "warrior": 0, "mage": 0, "healer": 0,}

    role_rows = cursor.execute("SELECT selected_role, reserved_places FROM participations").fetchall()

    for row in role_rows:
        reserved_places[row["selected_role"]] += int(row["reserved_places"])

    most_popular_quest_type = cursor.execute(""" SELECT quest_type, COUNT(*) AS quest_count FROM quests GROUP BY quest_type ORDER BY quest_count DESC, quest_type LIMIT 1""").fetchone()

    busiest_session = None
    admin_sessions = get_quest_sessions()

    for session in admin_sessions:
        if busiest_session is None or session["total_reserved_places"] > busiest_session["total_reserved_places"]:
            busiest_session = session

    cursor.close()
    conn.close()

    return {
        "total_adventurers": total_adventurers,
        "total_quests": total_quests,
        "total_sessions": total_sessions,
        "total_participations": total_participations,
        "reserved_places": reserved_places,
        "most_popular_quest_type": most_popular_quest_type,
        "busiest_session": busiest_session,
    }


def get_quest_by_id(p_quest_id):

    query = "SELECT id, title, duration_minutes, quest_type, difficulty, description, image_filename, created_by FROM quests WHERE id = ?"

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_quest_id,))
    db_quest = cursor.fetchone()

    cursor.close()
    conn.close()

    return db_quest


def get_sessions_by_quest_id(p_quest_id):

    query = 'SELECT quest_sessions.id, quest_sessions.quest_id, quest_sessions.day_of_week,quest_sessions.start_time, quest_sessions.location FROM quest_sessions WHERE quest_sessions.quest_id = ? ORDER BY quest_sessions.day_of_week, quest_sessions.start_time'

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_quest_id,))
    db_sessions = cursor.fetchall()

    cursor.close()
    conn.close()

    return [add_role_stats(dict(session)) for session in db_sessions]


def get_session_by_id(p_session_id):

    query = 'SELECT quest_sessions.id, quest_sessions.quest_id, quest_sessions.day_of_week, quest_sessions.start_time, quest_sessions.location, quests.duration_minutes FROM quest_sessions JOIN quests ON quest_sessions.quest_id = quests.id WHERE quest_sessions.id = ?'

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_session_id,))
    db_session = cursor.fetchone()

    cursor.close()
    conn.close()

    return db_session


def update_quest_session(p_session_id, p_day_of_week, p_start_time, p_location):

    db_session = get_session_by_id(p_session_id)

    if db_session is None:
        return False

    query = "UPDATE quest_sessions SET day_of_week = ?, start_time = ?, location = ? WHERE id = ?"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(query, (p_day_of_week, p_start_time, p_location, p_session_id))
    conn.commit()
    cursor.close()
    conn.close()

    return True


def delete_quest_session(p_session_id):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM participations WHERE session_id = ?", (p_session_id,))
    cursor.execute("DELETE FROM quest_sessions WHERE id = ?", (p_session_id,))
    conn.commit()
    cursor.close()
    conn.close()


def new_quest(p_title, p_duration, p_difficulty, p_description, p_quest_type, p_image_filename, p_created_by):

    query = "INSERT INTO quests (title, duration_minutes, difficulty, description, quest_type, image_filename, created_by) VALUES (?,?,?,?,?,?,?)"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(query, (p_title, p_duration, p_difficulty, p_description, p_quest_type, p_image_filename, p_created_by))
    quest_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()

    return quest_id


def new_quest_session(p_quest_id, p_day_of_week, p_start_time, p_location):

    db_quest = get_quest_by_id(p_quest_id)

    if db_quest is None:
        return None

    query = "INSERT INTO quest_sessions (quest_id, day_of_week, start_time, location) VALUES (?,?,?,?)"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(query, (p_quest_id, p_day_of_week, p_start_time, p_location))
    session_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()

    return session_id


def get_participation(p_user_id, p_session_id):

    query = "SELECT id, user_id, session_id, selected_role, reserved_places, created_at FROM participations WHERE user_id = ? AND session_id = ?"

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_user_id, p_session_id))
    db_participation = cursor.fetchone()

    cursor.close()
    conn.close()

    return db_participation


def get_participations_by_session(p_session_id):

    query = "SELECT id, user_id, session_id, selected_role, reserved_places, created_at FROM participations WHERE session_id = ?"

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_session_id,))
    db_participations = cursor.fetchall()

    cursor.close()
    conn.close()

    return db_participations


def get_participations_by_user(p_user_id):

    query = """SELECT participations.id, participations.user_id,participations.session_id, participations.selected_role, participations.reserved_places,participations.created_at, quests.id AS quest_id, quests.title,quest_sessions.day_of_week, quest_sessions.start_time, quest_sessions.location, quests.duration_minutes
        FROM participations
        JOIN quest_sessions ON participations.session_id = quest_sessions.id
        JOIN quests ON quest_sessions.quest_id = quests.id
        WHERE participations.user_id = ?
        ORDER BY quest_sessions.day_of_week, quest_sessions.start_time"""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_user_id,))
    db_participations = cursor.fetchall()

    cursor.close()
    conn.close()

    return db_participations


def get_participation_by_id(p_participation_id):

    query = "SELECT id, user_id, session_id, selected_role, reserved_places, created_at FROM participations WHERE id = ?"

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_participation_id,))
    db_participation = cursor.fetchone()

    cursor.close()
    conn.close()

    return db_participation


def new_participation(p_session_id, p_user_id, p_selected_role, p_reserved_places):

    query = "INSERT INTO participations (session_id, user_id, selected_role, reserved_places, created_at) VALUES (?,?,?,?,?)"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(query, (p_session_id, p_user_id, p_selected_role, int(p_reserved_places), datetime.now().isoformat(timespec="minutes")))
    participation_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()

    return participation_id


def update_participation(p_participation_id, p_selected_role, p_reserved_places):

    query = "UPDATE participations SET selected_role = ?, reserved_places = ? WHERE id = ?"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(query, (p_selected_role, int(p_reserved_places), p_participation_id))
    conn.commit()
    cursor.close()
    conn.close()


def delete_participation(p_participation_id):

    query = "DELETE FROM participations WHERE id = ?"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(query, (p_participation_id,))
    conn.commit()
    cursor.close()
    conn.close()

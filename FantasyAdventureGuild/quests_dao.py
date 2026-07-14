import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "FantasyAdventureGuild.db"
ROLE_CAPACITIES = {
    "warrior": 4,
    "mage": 3,
    "healer": 2,
}


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


def get_quest_sessions():

    query = """
        WITH role_counts AS (
            SELECT
                session_id,
                COALESCE(SUM(CASE WHEN selected_role = 'warrior' THEN reserved_places ELSE 0 END), 0) AS warrior_taken,
                COALESCE(SUM(CASE WHEN selected_role = 'mage' THEN reserved_places ELSE 0 END), 0) AS mage_taken,
                COALESCE(SUM(CASE WHEN selected_role = 'healer' THEN reserved_places ELSE 0 END), 0) AS healer_taken
            FROM participations
            GROUP BY session_id
        )
        SELECT
            quest_sessions.id AS session_id,
            quest_sessions.quest_id,
            quest_sessions.day_of_week,
            quest_sessions.start_time,
            quest_sessions.location,
            quests.title,
            quests.duration_minutes,
            quests.quest_type,
            quests.difficulty,
            quests.description,
            quests.image_filename,
            COALESCE(role_counts.warrior_taken, 0) AS warrior_taken,
            COALESCE(role_counts.mage_taken, 0) AS mage_taken,
            COALESCE(role_counts.healer_taken, 0) AS healer_taken,
            TRIM(
                CASE WHEN COALESCE(role_counts.warrior_taken, 0) >= 4 THEN 'warrior,' ELSE '' END ||
                CASE WHEN COALESCE(role_counts.mage_taken, 0) >= 3 THEN 'mage,' ELSE '' END ||
                CASE WHEN COALESCE(role_counts.healer_taken, 0) >= 2 THEN 'healer,' ELSE '' END,
                ','
            ) AS taken_roles
        FROM quest_sessions
        JOIN quests ON quest_sessions.quest_id = quests.id
        LEFT JOIN role_counts ON role_counts.session_id = quest_sessions.id
        ORDER BY quest_sessions.day_of_week, quest_sessions.start_time
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query)
    db_sessions = cursor.fetchall()

    cursor.close()
    conn.close()

    return db_sessions


def get_admin_quest_sessions():

    query = """
        WITH role_counts AS (
            SELECT
                session_id,
                COALESCE(SUM(CASE WHEN selected_role = 'warrior' THEN reserved_places ELSE 0 END), 0) AS warrior_taken,
                COALESCE(SUM(CASE WHEN selected_role = 'mage' THEN reserved_places ELSE 0 END), 0) AS mage_taken,
                COALESCE(SUM(CASE WHEN selected_role = 'healer' THEN reserved_places ELSE 0 END), 0) AS healer_taken,
                COALESCE(SUM(reserved_places), 0) AS total_reserved_places,
                COUNT(id) AS participation_count
            FROM participations
            GROUP BY session_id
        )
        SELECT
            quest_sessions.id AS session_id,
            quest_sessions.day_of_week,
            quest_sessions.start_time,
            quest_sessions.location,
            quests.id AS quest_id,
            quests.title,
            quests.quest_type,
            quests.difficulty,
            quests.duration_minutes,
            COALESCE(role_counts.warrior_taken, 0) AS warrior_taken,
            COALESCE(role_counts.mage_taken, 0) AS mage_taken,
            COALESCE(role_counts.healer_taken, 0) AS healer_taken,
            COALESCE(role_counts.total_reserved_places, 0) AS total_reserved_places,
            COALESCE(role_counts.participation_count, 0) AS participation_count
        FROM quest_sessions
        JOIN quests ON quest_sessions.quest_id = quests.id
        LEFT JOIN role_counts ON role_counts.session_id = quest_sessions.id
        ORDER BY quest_sessions.day_of_week, quest_sessions.start_time
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query)
    db_sessions = cursor.fetchall()

    cursor.close()
    conn.close()

    return db_sessions


def get_platform_statistics():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    total_adventurers = cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'adventurer'").fetchone()[0]
    total_quests = cursor.execute("SELECT COUNT(*) FROM quests").fetchone()[0]
    total_sessions = cursor.execute("SELECT COUNT(*) FROM quest_sessions").fetchone()[0]
    total_participations = cursor.execute("SELECT COUNT(*) FROM participations").fetchone()[0]

    reserved_places = {
        "warrior": 0,
        "mage": 0,
        "healer": 0,
    }

    role_rows = cursor.execute("""
        SELECT selected_role, COALESCE(SUM(reserved_places), 0) AS reserved_places
        FROM participations
        GROUP BY selected_role
    """).fetchall()

    for row in role_rows:
        reserved_places[row["selected_role"]] = int(row["reserved_places"])

    most_popular_quest_type = cursor.execute("""
        SELECT quest_type, COUNT(*) AS quest_count
        FROM quests
        GROUP BY quest_type
        ORDER BY quest_count DESC, quest_type
        LIMIT 1
    """).fetchone()

    busiest_session = cursor.execute("""
        SELECT
            quest_sessions.id AS session_id,
            quests.title,
            quest_sessions.day_of_week,
            quest_sessions.start_time,
            quest_sessions.location,
            COALESCE(SUM(participations.reserved_places), 0) AS reserved_places
        FROM quest_sessions
        JOIN quests ON quest_sessions.quest_id = quests.id
        LEFT JOIN participations ON participations.session_id = quest_sessions.id
        GROUP BY quest_sessions.id
        ORDER BY reserved_places DESC, quest_sessions.day_of_week, quest_sessions.start_time
        LIMIT 1
    """).fetchone()

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

    query = """
        SELECT
            quest_sessions.id,
            quest_sessions.quest_id,
            quest_sessions.day_of_week,
            quest_sessions.start_time,
            quest_sessions.location,
            COALESCE(SUM(CASE WHEN participations.selected_role = 'warrior' THEN participations.reserved_places ELSE 0 END), 0) AS warrior_taken,
            COALESCE(SUM(CASE WHEN participations.selected_role = 'mage' THEN participations.reserved_places ELSE 0 END), 0) AS mage_taken,
            COALESCE(SUM(CASE WHEN participations.selected_role = 'healer' THEN participations.reserved_places ELSE 0 END), 0) AS healer_taken
        FROM quest_sessions
        LEFT JOIN participations ON participations.session_id = quest_sessions.id
        WHERE quest_sessions.quest_id = ?
        GROUP BY quest_sessions.id
        ORDER BY quest_sessions.day_of_week, quest_sessions.start_time
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_quest_id,))
    db_sessions = cursor.fetchall()

    cursor.close()
    conn.close()

    return db_sessions


def get_session_by_id(p_session_id):

    query = """
        SELECT
            quest_sessions.id,
            quest_sessions.quest_id,
            quest_sessions.day_of_week,
            quest_sessions.start_time,
            quest_sessions.location,
            quests.duration_minutes
        FROM quest_sessions
        JOIN quests ON quest_sessions.quest_id = quests.id
        WHERE quest_sessions.id = ?
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_session_id,))
    db_session = cursor.fetchone()

    cursor.close()
    conn.close()

    return db_session


def get_session_by_schedule(p_day_of_week, p_start_time, p_location):

    query = """
        SELECT id, quest_id, day_of_week, start_time, location
        FROM quest_sessions
        WHERE day_of_week = ? AND start_time = ? AND location = ?
        LIMIT 1
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_day_of_week, p_start_time, p_location))
    db_session = cursor.fetchone()

    cursor.close()
    conn.close()

    return db_session


def get_sessions_by_day_and_location(p_day_of_week, p_location):

    query = """
        SELECT
            quest_sessions.id,
            quest_sessions.quest_id,
            quest_sessions.day_of_week,
            quest_sessions.start_time,
            quest_sessions.location,
            quests.duration_minutes
        FROM quest_sessions
        JOIN quests ON quest_sessions.quest_id = quests.id
        WHERE quest_sessions.day_of_week = ? AND quest_sessions.location = ?
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_day_of_week, p_location))
    db_sessions = cursor.fetchall()

    cursor.close()
    conn.close()

    return db_sessions


def _time_to_minutes(p_start_time):

    hours, minutes = p_start_time.split(":")

    return int(hours) * 60 + int(minutes)


def _session_start_minutes_from_week_start(p_day_of_week, p_start_time):

    return (int(p_day_of_week) - 1) * 24 * 60 + _time_to_minutes(p_start_time)


def sessions_overlap(p_first_session, p_second_session):

    first_start = _session_start_minutes_from_week_start(p_first_session["day_of_week"], p_first_session["start_time"])
    first_end = first_start + int(p_first_session["duration_minutes"])
    second_start = _session_start_minutes_from_week_start(p_second_session["day_of_week"], p_second_session["start_time"])
    second_end = second_start + int(p_second_session["duration_minutes"])

    return first_start < second_end and second_start < first_end


def quest_session_overlaps(p_day_of_week, p_start_time, p_location, p_duration, p_excluded_session_id=None):

    new_start = _time_to_minutes(p_start_time)
    new_end = new_start + int(p_duration)

    for db_session in get_sessions_by_day_and_location(p_day_of_week, p_location):
        if p_excluded_session_id is not None and int(db_session["id"]) == int(p_excluded_session_id):
            continue

        existing_start = _time_to_minutes(db_session["start_time"])
        existing_end = existing_start + int(db_session["duration_minutes"])

        if new_start < existing_end and existing_start < new_end:
            return True

    return False


def get_quests_with_sessions_by_guild_master(p_guild_master_id):

    query = """
        SELECT
            quests.id AS quest_id,
            quests.title,
            quests.duration_minutes,
            quest_sessions.id AS session_id,
            quest_sessions.day_of_week,
            quest_sessions.start_time,
            quest_sessions.location,
            COALESCE(SUM(participations.reserved_places), 0) AS total_reserved_places,
            COALESCE(SUM(CASE WHEN participations.selected_role = 'warrior' THEN participations.reserved_places ELSE 0 END), 0) AS warrior_taken,
            COALESCE(SUM(CASE WHEN participations.selected_role = 'mage' THEN participations.reserved_places ELSE 0 END), 0) AS mage_taken,
            COALESCE(SUM(CASE WHEN participations.selected_role = 'healer' THEN participations.reserved_places ELSE 0 END), 0) AS healer_taken,
            COUNT(participations.id) AS participation_count
        FROM quests
        LEFT JOIN quest_sessions ON quest_sessions.quest_id = quests.id
        LEFT JOIN participations ON participations.session_id = quest_sessions.id
        WHERE quests.created_by = ?
        GROUP BY quests.id, quest_sessions.id
        ORDER BY quests.title, quest_sessions.day_of_week, quest_sessions.start_time
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_guild_master_id,))
    db_rows = cursor.fetchall()

    cursor.close()
    conn.close()

    quests = {}

    for row in db_rows:
        quest_id = row["quest_id"]

        if quest_id not in quests:
            quests[quest_id] = {
                "id": quest_id,
                "title": row["title"],
                "duration_minutes": row["duration_minutes"],
                "sessions": [],
            }

        if row["session_id"] is None:
            continue

        role_counts = {
            "warrior": int(row["warrior_taken"]),
            "mage": int(row["mage_taken"]),
            "healer": int(row["healer_taken"]),
        }
        most_requested_count = max(role_counts.values())
        most_requested_roles = [
            role
            for role, count in role_counts.items()
            if count == most_requested_count and count > 0
        ]

        quests[quest_id]["sessions"].append({
            "id": row["session_id"],
            "quest_id": quest_id,
            "day_of_week": row["day_of_week"],
            "start_time": row["start_time"],
            "location": row["location"],
            "total_reserved_places": int(row["total_reserved_places"]),
            "warrior_taken": role_counts["warrior"],
            "mage_taken": role_counts["mage"],
            "healer_taken": role_counts["healer"],
            "warrior_remaining": ROLE_CAPACITIES["warrior"] - role_counts["warrior"],
            "mage_remaining": ROLE_CAPACITIES["mage"] - role_counts["mage"],
            "healer_remaining": ROLE_CAPACITIES["healer"] - role_counts["healer"],
            "participation_count": int(row["participation_count"]),
            "most_requested_roles": most_requested_roles,
        })

    return list(quests.values())


def guild_master_owns_session(p_guild_master_id, p_session_id):

    query = """
        SELECT 1
        FROM quest_sessions
        JOIN quests ON quest_sessions.quest_id = quests.id
        WHERE quest_sessions.id = ? AND quests.created_by = ?
        LIMIT 1
    """

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(query, (p_session_id, p_guild_master_id))
    db_match = cursor.fetchone()

    cursor.close()
    conn.close()

    return db_match is not None


def get_participation_count_by_session(p_session_id):

    query = "SELECT COUNT(*) FROM participations WHERE session_id = ?"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(query, (p_session_id,))
    participation_count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return int(participation_count)


def update_quest_session(p_session_id, p_day_of_week, p_start_time, p_location):

    db_session = get_session_by_id(p_session_id)

    if db_session is None:
        return False

    if quest_session_overlaps(
        p_day_of_week,
        p_start_time,
        p_location,
        db_session["duration_minutes"],
        p_excluded_session_id=p_session_id,
    ):
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

    if quest_session_overlaps(p_day_of_week, p_start_time, p_location, db_quest["duration_minutes"]):
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


def get_participations_by_user(p_user_id):

    query = """
        SELECT
            participations.id,
            participations.user_id,
            participations.session_id,
            participations.selected_role,
            participations.reserved_places,
            participations.created_at,
            quests.id AS quest_id,
            quests.title,
            quest_sessions.day_of_week,
            quest_sessions.start_time,
            quest_sessions.location,
            quests.duration_minutes
        FROM participations
        JOIN quest_sessions ON participations.session_id = quest_sessions.id
        JOIN quests ON quest_sessions.quest_id = quests.id
        WHERE participations.user_id = ?
        ORDER BY quest_sessions.day_of_week, quest_sessions.start_time
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_user_id,))
    db_participations = cursor.fetchall()

    cursor.close()
    conn.close()

    return db_participations


def get_reserved_places_for_role(p_session_id, p_selected_role):

    query = "SELECT COALESCE(SUM(reserved_places), 0) FROM participations WHERE session_id = ? AND selected_role = ?"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(query, (p_session_id, p_selected_role))
    reserved_places = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return int(reserved_places)


def role_has_capacity(p_session_id, p_selected_role, p_reserved_places, p_existing_participation_id=None):

    capacity = ROLE_CAPACITIES[p_selected_role]
    reserved_places = get_reserved_places_for_role(p_session_id, p_selected_role)

    if p_existing_participation_id is not None:
        existing = get_participation_by_id(p_existing_participation_id)

        if existing is not None and existing["selected_role"] == p_selected_role:
            reserved_places -= int(existing["reserved_places"])

    return reserved_places + int(p_reserved_places) <= capacity


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


def user_has_weekly_capacity(p_user_id, p_session_id):

    existing_participation = get_participation(p_user_id, p_session_id)
    user_participations = get_participations_by_user(p_user_id)

    if existing_participation is not None:
        return True

    return len(user_participations) < 3


def user_session_overlaps(p_user_id, p_session_id):

    new_session = get_session_by_id(p_session_id)

    for participation in get_participations_by_user(p_user_id):
        if int(participation["session_id"]) == int(p_session_id):
            continue

        if sessions_overlap(new_session, participation):
            return True

    return False


def participation_can_be_changed(p_session_id, p_current_day_of_week, p_current_time):

    db_session = get_session_by_id(p_session_id)
    current_minutes = _session_start_minutes_from_week_start(p_current_day_of_week, p_current_time)
    session_minutes = _session_start_minutes_from_week_start(db_session["day_of_week"], db_session["start_time"])

    if session_minutes < current_minutes:
        session_minutes += 7 * 24 * 60

    return session_minutes - current_minutes > 8 * 60


def new_participation(p_session_id, p_user_id, p_selected_role, p_reserved_places):

    query = "INSERT INTO participations (session_id, user_id, selected_role, reserved_places, created_at) VALUES (?,?,?,?,?)"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(query, (p_session_id, p_user_id, p_selected_role, int(p_reserved_places), datetime_now()))
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


def datetime_now():

    from datetime import datetime

    return datetime.now().isoformat(timespec="minutes")

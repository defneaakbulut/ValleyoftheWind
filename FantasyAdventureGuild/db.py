import sqlite3
from pathlib import Path

sql = "INSERT INTO users (username, password, role) VALUES (?, ?, ?)"

conn = sqlite3.connect('FantasyAdventureGuild.db')

cursor = conn.cursor()

cursor.execute(sql, ('windseeker', 'wind2026', 'adventurer'))

conn.commit()

cursor.close()

conn.close()

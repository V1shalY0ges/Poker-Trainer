from game_clean.managers.PlayerProfileManager  import PlayerProfileManager
import sqlite3

db_path = "game_clean/database/player_profiles.db"

conn = sqlite3.connect(db_path)
cur = conn.cursor()

print("--- Player Profiles ---")
for row in cur.execute("SELECT * FROM player_profiles"):
    print(row)

print("\n--- Action History ---")
for row in cur.execute("SELECT * FROM action_history"):
    print(row)

conn.close()

ppm = PlayerProfileManager()

print(ppm.get_profile("TestPlayer"))

ppm.update_profile("TestPlayer", vpip=0.5, pfr=0.3, aggression=0.7)

cur = ppm.conn.cursor()
cur.execute("SELECT * FROM player_profiles")
rows = cur.fetchall()

print("ROWS IN DB:", rows)

ppm.close()

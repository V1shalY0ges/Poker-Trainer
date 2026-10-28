from game_clean.managers.PlayerProfileManager import PlayerProfileManager
import os

db_path = "game_clean/database/player_profiles.db"
os.makedirs(os.path.dirname(db_path), exist_ok=True)  # ensure directory exists
profiles = PlayerProfileManager(db_path=db_path)

# Log a sample action
profiles.log_action(
    name="TestPlayer",
    stage="flop",
    vpip=0.3,
    pfr=0.2,
    aggression=0.5,
    board_wetness=0.4,
    pot_size=100,
    to_call=20,
    stack_size=500,
    equity=0.6,
    action="raise",
    result="win"
)

# Query the action_history table
cur = profiles.conn.cursor()
cur.execute("SELECT * FROM action_history")
rows = cur.fetchall()
print("Rows in action_history:", rows)

profiles.close()

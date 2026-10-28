# test_ppm_db.py
from game_clean.managers.PlayerProfileManager import PlayerProfileManager
from datetime import datetime
import os

# Ensure the database folder exists
db_folder = "game_clean/database"
os.makedirs(db_folder, exist_ok=True)

# Initialise the PlayerProfileManager
ppm = PlayerProfileManager()

player_name = "Alice"

# --- Test: update a profile ---
print(f"Updating profile for {player_name}...")
ppm.update_profile(player_name, vpip=0.3, pfr=0.2, aggression=0.5, avg_bet_size=50)

# --- Test: log some actions ---
print(f"Logging actions for {player_name}...")
ppm.log_action(
    name=player_name,
    stage="flop",
    vpip=0.3,
    pfr=0.2,
    aggression=0.5,
    board_wetness=0.4,
    pot_size=100,
    to_call=10,
    stack_size=500,
    equity=0.5,
    action="CALL",
    result="simulated"
)

ppm.log_action(
    name=player_name,
    stage="turn",
    vpip=0.3,
    pfr=0.2,
    aggression=0.5,
    board_wetness=0.5,
    pot_size=120,
    to_call=20,
    stack_size=480,
    equity=0.55,
    action="RAISE",
    result="simulated"
)

# --- Fetch and display contents of the tables ---
print("\n--- Player Profiles ---")
profiles = ppm.conn.execute("SELECT * FROM player_profiles").fetchall()
for row in profiles:
    print(row)

print("\n--- Action History ---")
actions = ppm.conn.execute("SELECT * FROM action_history").fetchall()
for row in actions:
    print(row)

# Close the connection
ppm.close()
print("\n[Test Complete] Database entries should now be visible above.")

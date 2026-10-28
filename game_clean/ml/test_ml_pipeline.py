# test_ml_pipeline.py
import os
import numpy as np
from ml_model_manager import MLModelManager
from game_clean.managers.PlayerProfileManager import PlayerProfileManager


db_path = "game_clean/database/player_profiles.db"
os.makedirs(os.path.dirname(db_path), exist_ok=True)  # ensure directory exists
profiles = PlayerProfileManager(db_path=db_path)

# -------------------------------
# Initialise Managers
# -------------------------------
ml = MLModelManager(base_dir="ml/models")

# -------------------------------
# Simulate some fake hands for multiple players
# -------------------------------
fake_hands = [
    # player_name, equity, pot_size, to_call, stack_size, vpip, pfr, aggression, board_wetness, action, bet
    ("Alice", 0.10, 100, 10, 800, 0.2, 0.1, 0.3, 0.6, "fold", 0),
    ("Alice", 0.65, 200, 25, 700, 0.35, 0.2, 0.6, 0.4, "raise", 150),
    ("Bob",   0.35, 150, 20, 750, 0.25, 0.15, 0.5, 0.5, "call", 0),
    ("Bob",   0.85, 250, 30, 650, 0.4, 0.25, 0.8, 0.3, "raise", 300),
]

# -------------------------------
# Log actions into database
# -------------------------------
for hand in fake_hands:
    name, equity, pot_size, to_call, stack_size, vpip, pfr, aggression, board_wetness, action, bet = hand
    result = "win" if equity > 0.5 else "lose"  # simple placeholder
    profiles.log_action(name, stage="flop", vpip=vpip, pfr=pfr, aggression=aggression,
                        board_wetness=board_wetness, pot_size=pot_size, to_call=to_call, stack_size=stack_size,equity=equity,
                        action=action, result=result)
    # Update the aggregate player profile
    print(f"Logged action for {name}")

    profiles.update_profile(name, vpip=vpip, pfr=pfr, aggression=aggression, avg_bet_size=bet)

# -------------------------------
# Prepare training data for global model
# -------------------------------
cur = profiles.conn.cursor()
cur.execute("SELECT equity, pot_size, to_call, stack_size, vpip, pfr, aggression, board_wetness, action, CASE WHEN action='raise' THEN avg_bet_size ELSE 0 END as bet_size FROM action_history")
rows = cur.fetchall()

X_global = np.array([row[:8] for row in rows])
y_actions_global = np.array([{"fold":0, "call":1, "raise":2}[row[8]] for row in rows])
y_bets_global = np.array([row[9] for row in rows])

# -------------------------------
# Train the global model
# -------------------------------
ml.train_global_models(X_global, y_actions_global, y_bets_global)

# -------------------------------
# Train a personalized model for Alice
# -------------------------------
cur.execute("SELECT equity, pot_size, to_call, stack_size, vpip, pfr, aggression, board_wetness, action, CASE WHEN action='raise' THEN avg_bet_size ELSE 0 END as bet_size FROM action_history WHERE name = ?", ("Alice",))
rows_alice = cur.fetchall()

X_alice = np.array([row[:8] for row in rows_alice])
y_actions_alice = np.array([{"fold":0, "call":1, "raise":2}[row[8]] for row in rows_alice])
y_bets_alice = np.array([row[9] for row in rows_alice])

ml.train_player_model("Alice", X_alice, y_actions_alice, y_bets_alice)

# -------------------------------
# Make predictions for both Alice and Bob
# -------------------------------
features_alice = ml.prepare_features(0.62, 200, 20, 800, 0.3, 0.12, 0.6, 0.2)
action_alice, bet_alice = ml.predict_for_player("Alice", features_alice)
print(f"Alice model → Action: {action_alice}, Bet: {bet_alice:.2f}")

features_bob = ml.prepare_features(0.55, 180, 15, 900, 0.25, 0.10, 0.5, 0.4)
action_bob, bet_bob = ml.predict_for_player("Bob", features_bob)
print(f"Bob (no personal model) → Action: {action_bob}, Bet: {bet_bob:.2f}")

# -------------------------------
# Clean up
# -------------------------------
profiles.close()

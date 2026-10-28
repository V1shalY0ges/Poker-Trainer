# train_ml_models.py
import numpy as np
from game_clean.ml.ml_model_manager import MLModelManager
from game_clean.ml.feature_extractor import FeatureExtractor

# -----------------------------
# Generate fake poker data
# -----------------------------
def generate_fake_poker_data(n_hands=5000):
    """
    Generates synthetic poker data for training:
    - Features: equity, pot, bet_to_call, stack, vpip, pfr, aggression, board_wetness
    - Labels: action (fold/call/raise), bet size
    """
    X_features = []
    y_actions = []
    y_bets = []

    for _ in range(n_hands):
        equity = np.random.rand()
        pot = np.random.randint(10, 500)
        bet_to_call = np.random.randint(0, 100)
        stack = np.random.randint(100, 2000)
        vpip = np.random.rand()
        pfr = np.random.rand()
        aggression = np.random.rand()
        board_wetness = np.random.rand()
        position = np.random.randint(1, 10)  # positions 1-9
        stage = np.random.choice(["preflop", "flop", "turn", "river"])

        # Extract features using FeatureExtractor
        fe = FeatureExtractor()
        features = fe.extract(
            equity=equity,
            pot=pot,
            bet_to_call=bet_to_call,
            stack=stack,
            vpip=vpip,
            pfr=pfr,
            aggression=aggression,
            board_wetness=board_wetness,
            position=position,
            stage=stage
        )
        X_features.append(features)

        # Decide action and bet size using simple rules
        if equity < 0.3:
            action = 0  # fold
            bet = 0
        elif equity < 0.6:
            action = 1  # call
            bet = bet_to_call
        else:
            action = 2  # raise
            bet = int(pot * (0.5 + 0.5 * equity))

        y_actions.append(action)
        y_bets.append(bet)

    return np.array(X_features), np.array(y_actions), np.array(y_bets)

# -----------------------------
# Main training routine
# -----------------------------
if __name__ == "__main__":
    print("[TRAIN] Initialising ML Model Manager...")
    ml_manager = MLModelManager()

    print("[TRAIN] Generating synthetic poker data...")
    X, y_actions, y_bets = generate_fake_poker_data(n_hands=5000)

    print("[TRAIN] Training global models...")
    ml_manager.train_global_models(X, y_actions, y_bets)

    print("[TRAIN] Training player-specific model for Alice...")
    ml_manager.train_player_model("Alice", X, y_actions, y_bets)

    print("[TRAIN] Training complete. Models saved in ml/models/")

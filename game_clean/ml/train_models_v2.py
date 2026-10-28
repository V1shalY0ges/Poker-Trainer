import random
import numpy as np
from game_clean.ml.ml_model_manager import MLModelManager
from game_clean.ml.feature_extractor import FeatureExtractor

def generate_training_data(samples=3000):
    """
    Generates training data for ML models using 8 features:
    equity, pot, bet_to_call, stack, vpip, pfr, aggression, board_wetness
    """
    fe = FeatureExtractor()
    X, y_actions, y_bets = [], [], []

    for _ in range(samples):
        # Random values for game state
        equity = random.random()  # 0-1
        pot = random.randint(50, 500)
        to_call = random.randint(0, 50)
        stack = random.randint(200, 2000)

        vpip = random.uniform(0.15, 0.45)
        pfr = random.uniform(0.10, 0.30)
        aggression = random.uniform(0.20, 0.70)
        board_wetness = random.random()

        # Extract features using only 8 features (ignore position/stage)
        features = fe.extract(
            equity, pot, to_call, stack,
            vpip, pfr, aggression, board_wetness,
            position=None, stage=None  # ensures 8 features
        )

        # Bootstrapped labels based on equity
        if equity < 0.3:
            action = 0  # fold
            bet = 0
        elif equity < 0.6:
            action = 1  # call
            bet = 0
        else:
            action = 2  # raise
            bet = pot * equity

        X.append(features)
        y_actions.append(action)
        y_bets.append(bet)

    return np.array(X), np.array(y_actions), np.array(y_bets)

if __name__ == "__main__":
    ml = MLModelManager()

    # Generate training data
    X, y_actions, y_bets = generate_training_data(samples=3000)

    # Train global models
    ml.train_global_models(X, y_actions, y_bets)

    # Train player-specific model
    ml.train_player_model("ADAPTIVE_BOT", X, y_actions, y_bets)

    print("[Training Complete] Models trained with 8 features for consistency with AdvancedBot.")

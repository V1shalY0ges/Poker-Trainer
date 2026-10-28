# test_advanced_bot_ml.py
import numpy as np
from sklearn.metrics import mean_squared_error
from game_clean.ml.ml_model_manager import MLModelManager  # <-- make sure this matches your file name


def generate_fake_poker_data(n_hands=1000):
    X, y_actions, y_bets = [], [], []

    for _ in range(n_hands):
        equity = np.random.rand()
        pot_size = np.random.randint(10, 500)
        to_call = np.random.randint(0, 100)
        stack_size = np.random.randint(100, 2000)
        vpip = np.random.rand()
        pfr = np.random.rand()
        aggression = np.random.rand()
        board_wetness = np.random.rand()

        X.append([equity, pot_size, to_call, stack_size, vpip, pfr, aggression, board_wetness])

        # Simple action rules
        if equity < 0.3:
            action = 0
            bet = 0
        elif equity < 0.6:
            action = 1
            bet = 0
        else:
            action = 2
            bet = pot_size * (0.5 + 0.5 * equity)

        y_actions.append(action)
        y_bets.append(bet)

    return np.array(X), np.array(y_actions), np.array(y_bets)


def test_ml_readiness(ml_manager, player_name="Alice", n_tests=500):
    X_test, y_actions_test, y_bets_test = generate_fake_poker_data(n_tests)
    action_map = {0: 'fold', 1: 'call', 2: 'raise'}

    correct_actions = 0
    predicted_bets = []
    true_bets = []

    for features, true_action, true_bet in zip(X_test, y_actions_test, y_bets_test):
        features_reshaped = features.reshape(1, -1)
        pred_action, pred_bet = ml_manager.predict_for_player(player_name, features_reshaped)

        if pred_action == action_map[true_action]:
            correct_actions += 1

        predicted_bets.append(pred_bet)
        true_bets.append(true_bet)

    action_accuracy = correct_actions / n_tests
    bet_mse = mean_squared_error(true_bets, predicted_bets)

    print(f"[ML Test] Action Accuracy: {action_accuracy * 100:.2f}%")
    print(f"[ML Test] Bet MSE: {bet_mse:.2f}")
    print("[ML Test] Example predictions:")
    for i in range(5):
        pred_action, pred_bet = ml_manager.predict_for_player(player_name, X_test[i].reshape(1, -1))
        print(f"Equity {X_test[i][0]:.2f}, True: {action_map[y_actions_test[i]]}, "
              f"{y_bets_test[i]:.2f} → Pred: {pred_action}, {pred_bet:.2f}")


if __name__ == "__main__":
    ml = MLModelManager()

    # Generate fake training data
    X_train, y_actions_train, y_bets_train = generate_fake_poker_data(2000)

    # Train global models
    ml.train_global_models(X_train, y_actions_train, y_bets_train)

    # Train a personalised model for Alice
    ml.train_player_model("Alice", X_train, y_actions_train, y_bets_train)

    # Run ML readiness test
    test_ml_readiness(ml, "Alice", n_tests=500)

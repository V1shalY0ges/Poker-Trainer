# COMMENTS ARE DONE

from pathlib import Path
import joblib
# joblib is used to save and load trained machine learning models to/from disk

import numpy as np
# numpy is used for numerical operations and handling feature arrays

import os
# os is used for file paths and directory management
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
# RandomForestClassifier predicts discrete actions (fold/call/raise)
# RandomForestRegressor predicts continuous values (bet sizes)

from sklearn.metrics import mean_squared_error
# Used to evaluate bet size prediction accuracy during testing



class MLModelManager:
    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parent / "ml" / "models"

        self.base_dir = str(base_dir)
        """
        Manages all machine learning models
        Handles global models, player-specific models, training, prediction
        and safe fallbacks if models are not yet trained
        """

        # Base directory where all ML models are stored

        # Directory for shared global models (used as baseline)
        self.global_dir = os.path.join(base_dir, "global")

        # Directory for personalised player models
        self.players_dir = os.path.join(base_dir, "players")


        #create a directory for new players who we assign a global base model and existing players where we use the existing directory for them
        # Global models are shared by all new players
        # Player directories store personalised learning data

        os.makedirs(self.global_dir, exist_ok=True)
        os.makedirs(self.players_dir, exist_ok=True)

        # Paths for global models
        self.global_action_path = os.path.join(self.global_dir, "action_model.pkl")
        self.global_betsize_path = os.path.join(self.global_dir, "betsize_model.pkl")

        # Load or initialise global models
        self.global_action_model = self._load_or_init_model(self.global_action_path, "classifier")
        self.global_betsize_model = self._load_or_init_model(self.global_betsize_path, "regressor")

        if not hasattr(self.global_action_model, "estimators_") or not hasattr(self.global_betsize_model,
                                                                               "estimators_"):
            print("[ML] Global models not fitted yet. Training with default data to avoid crashes...")
            # adding a check here to see if we have the data for the global models if not resort to default data
            X_fake, y_actions_fake, y_bets_fake = generate_fake_poker_data(200) # generate the data to train the model on
            self.train_global_models(X_fake, y_actions_fake, y_bets_fake)

        # Dictionary storing loaded player-specific models in memory
        # Format: { player_name: { "action": model, "bet": model } }
        self.player_models = {}



    def _load_or_init_model(self, path, model_type):
            """
            Loads a machine learning model from disk if it exists
            Otherwise it creates a new untrained model of the specified type
            """
            if os.path.exists(path): # checking if the specified directory of the model exists and if it does load it
                print(f"[ML] loaded model from {path}")
                return joblib.load(path) # load the model from disk
            else:
                # it doesnt exist so we create a new model depending on if we getting the action or the bet size
                print(f"[ML] creating new {model_type} model")
                if model_type == "classifier":
                    return RandomForestClassifier(n_estimators=100, random_state=42)
                elif model_type == "regressor":
                    return RandomForestRegressor(n_estimators=100, random_state=42)
                #may need to vary some algorithms or hyperparameters

    def prepare_features(self, equity, pot_size, to_call, stack_size,vpip, pfr, aggression, board_wetness):
        # this converts everything/game variables into a numpy array for the ml agent

        # Return a 2D array as required by scikit-learn
        return np.array([[equity, pot_size, to_call, stack_size,vpip, pfr, aggression, board_wetness]])

    # Player model loading
    # -------------------------------
    def load_player_model(self, player_name):
        """
        Loads a personalised action and bet model for a specific player
        If none exist the global models are used as a fallback
        """

        # checking if the player directory exists if it doesnt, we make it
        player_dir = os.path.join(self.players_dir, player_name)

        # Create directory if this is a new player
        os.makedirs(player_dir, exist_ok=True)

        # File paths for the player's models
        action_path = os.path.join(player_dir, "action_model.pkl")
        bet_path = os.path.join(player_dir, "betsize_model.pkl")

        if os.path.exists(action_path) and os.path.exists(bet_path):
            # checking that the action and bet models for the player exist in which they are loading
            print(f"[ML] Loaded personalised model for {player_name}")
            # adding the models to the dictionary
            self.player_models[player_name] = {
                "action": joblib.load(action_path),
                "bet": joblib.load(bet_path)
            }
        else:
            # models dont exist so we create one by using the baseline global models
            print(f"[ML] No personalised model for {player_name} — using global model")
            self.player_models[player_name] = {
                "action": self.global_action_model,
                "bet": self.global_betsize_model
            }

    # Player model training
    # -------------------------------
    def train_player_model(self, player_name, X, y_actions, y_bets):
        """
        Trains new personalised models for a player using their gameplay data.
        """
        # check that player directory exists
        player_dir = os.path.join(self.players_dir, player_name)
        os.makedirs(player_dir, exist_ok=True)

        # create both the action and bet models using the classifier and regressor
        action_model = RandomForestClassifier(n_estimators=100, random_state=42)
        bet_model = RandomForestRegressor(n_estimators=100, random_state=42)

        # apply and train the models
        action_model.fit(X, y_actions)
        bet_model.fit(X, y_bets)

        # Save trained models to disk
        joblib.dump(action_model, os.path.join(player_dir, "action_model.pkl"))
        joblib.dump(bet_model, os.path.join(player_dir, "betsize_model.pkl"))

        print(f"[ML] Trained and saved personalised models for {player_name}")


    def predict_for_player(self, player_name, features):
        """
        Predicts the best action and bet size for a given player
        using either personalised or global models.
        """

        features = np.array(features).reshape(1, -1)  # ensures features are correctly shaped

        # Load model if not already cached
        if player_name not in self.player_models:
                self.load_player_model(player_name)
        # Retrieve models
        models = self.player_models[player_name]
        action_model = models["action"]
        bet_model = models["bet"]

        #  safe fallback to check if models are fitted

        if not hasattr(action_model, "estimators_"):
            print(f"[ML Warning] {player_name}'s action model not fitted. Using global model.")
            action_model = self.global_action_model
            bet_model = self.global_betsize_model

        # Map numerical predictions to poker actions
        actions = ['fold', 'call', 'raise']
        pred_action = actions[int(action_model.predict(features)[0])]

        # Only predict bet size if raising
        if pred_action == "raise":
            raw_bet = float(bet_model.predict(features)[0])
            return pred_action, raw_bet
        else:
            return pred_action, 0.0

    # Train global models
    # -------------------------------
    def train_global_models(self, X, y_actions, y_bets):
        """
        Trains the shared global models using aggregated data.
        """

        # apply and train the models
        self.global_action_model.fit(X, y_actions)
        self.global_betsize_model.fit(X, y_bets)

        # Save updated models to disk
        joblib.dump(self.global_action_model, self.global_action_path)
        joblib.dump(self.global_betsize_model, self.global_betsize_path)
        print("[ML] Updated global models")

def generate_fake_poker_data(n_hands=1000):
    """
    Generates synthetic poker hand data for training and testing.
    Used when real gameplay data is unavailable.
    """
    X = []
    y_actions = []
    y_bets = []

    for _ in range(n_hands):
        # Randomly generated poker state features
        equity = np.random.rand()  # 0.0 to 1.0
        pot_size = np.random.randint(10, 500)
        to_call = np.random.randint(0, 100)
        stack_size = np.random.randint(100, 2000)
        vpip = np.random.rand()  # 0 to 1
        pfr = np.random.rand()
        aggression = np.random.rand()
        board_wetness = np.random.rand()  # 0 = dry, 1 = very wet

        X.append([equity, pot_size, to_call, stack_size, vpip, pfr, aggression, board_wetness])

        # Simple rules for actions
        if equity < 0.3:
            action = 0  # fold
            bet = 0
        elif equity < 0.6:
            action = 1  # call
            bet = 0
        else:
            action = 2  # raise
            bet = pot_size * (0.5 + 0.5 * equity)  # raise between 50%-100% of pot

        y_actions.append(action)
        y_bets.append(bet)

    return np.array(X), np.array(y_actions), np.array(y_bets)


def test_ml_readiness(ml_manager, player_name="Alice", n_tests=500):
    # Generate new fake hands for testing
    X_test, y_actions_test, y_bets_test = generate_fake_poker_data(n_tests)

    action_map = {0: 'fold', 1: 'call', 2: 'raise'}

    correct_actions = 0
    predicted_bets = []
    true_bets = []

    for features, true_action, true_bet in zip(X_test, y_actions_test, y_bets_test):
        features_reshaped = features.reshape(1, -1)
        pred_action, pred_bet = ml_manager.predict_for_player(player_name, features_reshaped)

        # Check action
        if pred_action == action_map[true_action]:
            correct_actions += 1

        # Store bets for MSE
        predicted_bets.append(pred_bet)
        true_bets.append(true_bet)

    action_accuracy = correct_actions / n_tests
    bet_mse = mean_squared_error(true_bets, predicted_bets)

    print(f"[ML Test] Action Accuracy: {action_accuracy * 100:.2f}%")
    print(f"[ML Test] Bet MSE: {bet_mse:.2f}")
    print("[ML Test] Example predictions:")
    for i in range(5):
        print(
            f"Equity {X_test[i][0]:.2f}, True: {action_map[y_actions_test[i]]}, {y_bets_test[i]:.2f} → Pred: {ml_manager.predict_for_player(player_name, X_test[i].reshape(1, -1))}")


if __name__ == "__main__":
    ml = MLModelManager()

    # Fake training data
    X_fake = np.array([
        [0.10, 100, 10, 800, 0.2, 0.1, 0.3, 0.6],
        [0.35, 150, 20, 750, 0.25, 0.15, 0.5, 0.5],
        [0.65, 200, 25, 700, 0.35, 0.20, 0.6, 0.4],
        [0.85, 250, 30, 650, 0.4, 0.25, 0.8, 0.3],
    ])
    y_actions = np.array([0, 1, 2, 2])
    y_bets = np.array([0, 0, 150, 300])

    # Train global models
    ml.train_global_models(X_fake, y_actions, y_bets)

    # Train personalised model for Alice
    ml.train_player_model("Alice", X_fake, y_actions, y_bets)

    # Predict using Alice’s model
    features = ml.prepare_features(0.62, 200, 20, 800, 0.3, 0.12, 0.6, 0.2)
    action, bet = ml.predict_for_player("Alice", features)
    print(f"Alice → Action: {action}, Bet: {bet:.2f}")

    # Predict using Bob’s fallback to global
    features = ml.prepare_features(0.55, 180, 15, 900, 0.25, 0.10, 0.5, 0.4)
    action, bet = ml.predict_for_player("Bob", features)
    print(f"Bob → Action: {action}, Bet: {bet:.2f}")

    X_train, y_actions_train, y_bets_train = generate_fake_poker_data(2000)
    ml.train_global_models(X_train, y_actions_train, y_bets_train)
    ml.train_player_model("Alice", X_train, y_actions_train, y_bets_train)
    # Run readiness test
    test_ml_readiness(ml, "Alice", n_tests=500)

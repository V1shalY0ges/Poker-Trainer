from game_clean.ml.ml_model_manager import MLModelManager  #  existing ML manager file
from game_clean.poker.advanced_bot_v2 import AdvancedBot  #  bot class
import random
import numpy as np
from itertools import product


# ----------------------------------
# Generate fake poker data
# ----------------------------------
def generate_fake_poker_data(n_hands=1000):
    X = []
    y_actions = []
    y_bets = []

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

        if equity < 0.3:
            action = 0  # fold
            bet = 0
        elif equity < 0.6:
            action = 1  # call
            bet = 0
        else:
            action = 2  # raise
            bet = pot_size * (0.5 + 0.5 * equity)

        y_actions.append(action)
        y_bets.append(bet)

    return np.array(X), np.array(y_actions), np.array(y_bets)

# ----------------------------------
# Main testing script
# ----------------------------------
if __name__ == "__main__":
    ml = MLModelManager()

    X_fake, y_actions, y_bets = generate_fake_poker_data(1000)
    ml.train_global_models(X_fake, y_actions, y_bets)
    ml.train_player_model("Alice", X_fake, y_actions, y_bets)

    bot = AdvancedBot(name="Alice", ml_manager=ml)

    bot.set_state(
        hole_cards=['Ah', 'Kd'],                # example hole cards
        community_cards=['Qs', 'Jd', '10c'],    # example board
        opponent_profile={'vpip': 0.25, 'pfr': 0.15, 'aggression': 0.3},
        pot=150,
        bet_to_call=20,
        stack=1000,
        position=1
    )

    action, amount = bot.make_decision()
    print(f"AdvancedBot Decision → Action: {action}, Bet: {amount}")

    # Optional: test multiple random hands
    for i in range(5):
        equity = np.random.rand()
        pot = np.random.randint(50, 400)
        to_call = np.random.randint(0, 50)
        stack = np.random.randint(100, 2000)
        bot.set_state(
            hole_cards=['9h', '7d'],
            community_cards=['2c', '5s', 'Jd'],
            opponent_profile={'vpip': 0.2, 'pfr': 0.1, 'aggression': 0.25},
            pot=pot,
            bet_to_call=to_call,
            stack=stack,
            position=1
        )
        action, amount = bot.make_decision()
        print(f"[Test {i+1}] Action: {action}, Bet: {amount}")

import random
import itertools
import numpy as np
from game_clean.ml.ml_model_manager import MLModelManager  # adjust import if needed

# Simple deck generation
SUITS = ['H', 'D', 'C', 'S']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']


def create_deck():
    return [r + s for r, s in itertools.product(RANKS, SUITS)]


# Simple board wetness estimation
def board_wetness(board):
    suits = [c[-1] for c in board]
    suit_counts = {s: suits.count(s) for s in SUITS}
    return max(suit_counts.values()) / 5.0 if board else 0.0


# Pot odds
def pot_odds(pot, to_call):
    return to_call / (pot + to_call) if (pot + to_call) > 0 else 0


# Equity estimation (very simplified)
def estimate_equity(hole_cards, board):
    # Use a hand strength: count high cards + connectedness
    rank_strength = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12,
                     'K': 13, 'A': 14}
    cards = hole_cards + board
    strength = sum(rank_strength[c[:-1]] for c in cards) / (14 * len(cards))
    return min(1.0, strength)  # normalised 0-1


def simulate_hand(ml_manager, player_name="Alice", initial_pot=100):
    deck = create_deck()
    random.shuffle(deck)

    hole_cards = [deck.pop(), deck.pop()]
    board = [deck.pop() for _ in range(3)]  # flop
    pot = initial_pot
    to_call = random.randint(0, 20)  # assume small blind or current bet
    stack_size = 1000  # arbitrary
    vpip = 0.3  # example stat
    pfr = 0.2
    aggression = 0.5

    equity = estimate_equity(hole_cards, board)
    wetness = board_wetness(board)
    odds = pot_odds(pot, to_call)

    features = ml_manager.prepare_features(equity, pot, to_call, stack_size, vpip, pfr, aggression, wetness)
    action, bet = ml_manager.predict_for_player(player_name, features)

    return {
        "hole": hole_cards,
        "board": board,
        "equity": round(equity, 3),
        "pot_odds": round(odds, 3),
        "board_wetness": round(wetness, 3),
        "action": action,
        "bet": round(bet, 2)
    }


if __name__ == "__main__":
    ml = MLModelManager()
    ml.load_player_model("Alice")  #  Alice needs a trained model

    hands_to_simulate = 20
    results = []
    for i in range(hands_to_simulate):
        hand_result = simulate_hand(ml, "Alice")
        results.append(hand_result)
        print(f"[Hand {i + 1}] Hole: {hand_result['hole']}, Board: {hand_result['board']}")
        print(
            f"Equity: {hand_result['equity']}, Pot Odds: {hand_result['pot_odds']}, Board Wetness: {hand_result['board_wetness']}")
        print(f"Alice → Action: {hand_result['action']}, Bet: {hand_result['bet']}")
        print("-" * 60)

    # save to CSV for NEA report
    import csv

    with open("bot_simulation_log.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print("[Simulation] Saved log to bot_simulation_log.csv")

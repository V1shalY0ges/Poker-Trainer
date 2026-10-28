# test_river_random.py
# COMMENTS ARE DONE
import random
from functools import partial

from game_clean.poker.partial_hand_evaluator import PartialHandEvaluator
from game_clean.poker.hand_evaluator_no_p import HandEvaluator


# --- Initialise PartialHandEvaluator ---
partial_evaluator = PartialHandEvaluator(full_evaluator=HandEvaluator())

# --- Helper: generate random deck and deal cards ---
def deal_random_hand(deck, n=2):
    return [deck.pop(random.randrange(len(deck))) for _ in range(n)]

def generate_random_board(deck, num_cards=5):
    return [deck.pop(random.randrange(len(deck))) for _ in range(num_cards)]

# --- Run random tests ---
num_tests = 25  # generate 10 random river hands

ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
suits = ['H', 'D', 'C', 'S']

for i in range(num_tests):
    deck = [r + s for r in ranks for s in suits]

    # Deal hole cards
    hole_cards = deal_random_hand(deck, 2)

    # Deal community cards (river)
    community_cards = generate_random_board(deck, 5)

    # Estimate river equity
    equity = partial_evaluator.estimate_river_equity(hole_cards, community_cards)

    print(f"Test {i+1}: Hole: {hole_cards}, Board: {community_cards}, Estimated River Equity: {equity:.2f}")

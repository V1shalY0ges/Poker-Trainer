from game_clean.poker.intermediate_bot import IntermediateBot
from game_clean.poker.partial_hand_evaluator import PartialHandEvaluator
import random
# COMMENTS ARE DONE
# --- Setup bot and evaluator ---
bot = IntermediateBot(name="IntermediateBot", chips=1000)
evaluator = PartialHandEvaluator()

# --- Deck setup ---
ranks = "23456789TJQKA"
suits = "CDHS"
deck_template = [r + s for r in ranks for s in suits]

# --- Deal function ---
def deal_hand():
    deck = deck_template[:]
    random.shuffle(deck)
    return deck[:2], deck[2:5]  # 2 hole cards, 3 community cards (flop)

# --- Counters for analysis ---
actions = {"fold": 0, "call": 0, "raise": 0}
total_equity = 0

print("=== IntermediateBot 50-Hand Postflop Test ===\n")

for i in range(1, 51):
    hole, community = deal_hand()
    result = bot.postflop_strategy(hole, community, stage="flop", pot=100, to_call=20)
    equity = bot.last_equity
    total_equity += equity
    actions[result["type"]] += 1

    print(f"Hand {i}: Hole: {hole}, Community: {community}, "
          f"Equity: {equity:.2f}, Action: {result}")

# --- Summary statistics ---
print("\n=== Summary ===")
print(f"Total Hands Tested: 50")
print(f"Average Equity: {total_equity / 50:.2f}")
for action, count in actions.items():
    print(f"{action.capitalise()} Frequency: {count} ({count / 50:.1%})")

# test_advanced_bot_full.py
import os
import random
from game_clean.ml.ml_model_manager import MLModelManager
from game_clean.managers.PlayerProfileManager import PlayerProfileManager
from game_clean.poker.advanced_bot_v2 import AdvancedBot

# ----------------------------
# Setup
# ----------------------------
os.makedirs("game_clean/database", exist_ok=True)

ml_manager = MLModelManager()
ppm = PlayerProfileManager()

bot_name = "Alice"
bot = AdvancedBot(name=bot_name, ml_manager=ml_manager)

# ----------------------------
# Define test hands
# ----------------------------
test_hands = [
    # Format: hole_cards, community_cards, opponent_profile, pot, bet_to_call, stack, position
    (['Ah', 'Kd'], ['Qs', 'Jd', '10c'], ppm.get_average_profile(), 100, 10, 800, 1),
    (['9h', '7d'], ['2c', '5s', 'Jd'], ppm.get_average_profile(), 80, 8, 500, 2),
    (['Qs', 'Qc'], ['Kh', '10h', '3d'], ppm.get_average_profile(), 150, 15, 1200, 3),
    (['7s', '6s'], ['8s', '9d', '2c'], ppm.get_average_profile(), 60, 5, 400, 4),
]

# ----------------------------
# Run simulation
# ----------------------------
print("\n=== AdvancedBot Test Simulation ===\n")

for i, hand in enumerate(test_hands, 1):
    hole_cards, community_cards, opp_profile, pot, to_call, stack, position = hand

    bot.set_state(hole_cards, community_cards, opp_profile, pot, to_call, stack, position)
    action, bet = bot.make_decision()

    # Print debug info
    print(f"[Hand {i}] Hole: {hole_cards}, Board: {community_cards}")
    print(f"Equity: {bot.last_equity:.3f}, Pot Odds: {to_call / (pot + to_call):.3f}, "
          f"Board Wetness: {bot.estimate_board_wetness():.3f}")
    print(f"ML-based Decision integrated → Action: {action.upper()}, Bet: {bet}\n")

    # Log to database
    ppm.update_profile(bot_name,
                       vpip=opp_profile['vpip'],
                       pfr=opp_profile['pfr'],
                       aggression=opp_profile['aggression'],
                       avg_bet_size=bet)

    ppm.log_action(bot_name,
                   stage="flop",
                   vpip=opp_profile['vpip'],
                   pfr=opp_profile['pfr'],
                   aggression=opp_profile['aggression'],
                   board_wetness=bot.estimate_board_wetness(),
                   pot_size=pot,
                   to_call=to_call,
                   stack_size=stack,
                   equity=bot.last_equity,
                   action=action,
                   result="simulated")

# ----------------------------
# Optional: Run random hands
# ----------------------------
print("\n=== Randomised Test Hands ===\n")
possible_holes = [['Ah', 'Kd'], ['9h', '7d'], ['Qs', 'Qc'], ['7s', '6s']]
possible_boards = [['Qs', 'Jd', '10c'], ['2c', '5s', 'Jd'], ['Kh', '10h', '3d'], ['8s', '9d', '2c']]

for i in range(5):
    hole_cards = random.choice(possible_holes)
    community_cards = random.choice(possible_boards)
    pot = random.randint(50, 400)
    to_call = random.randint(0, 50)
    stack = random.randint(100, 2000)

    bot.set_state(hole_cards, community_cards, ppm.get_average_profile(), pot, to_call, stack, 1)
    action, bet = bot.make_decision()

    print(f"[Random Test {i + 1}] Hole: {hole_cards}, Board: {community_cards}")
    print(f"Equity: {bot.last_equity:.3f}, Pot Odds: {to_call / (pot + to_call):.3f}, "
          f"Board Wetness: {bot.estimate_board_wetness():.3f}")
    print(f"ML-based Decision integrated → Action: {action.upper()}, Bet: {bet}\n")

ppm.close()
print("\n[TEST COMPLETE] PlayerProfileManager updated, actions logged.\n")

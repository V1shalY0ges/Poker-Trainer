# test_advanced_bot.py
import random
from game_clean.ml.ml_model_manager import MLModelManager
from game_clean.managers.PlayerProfileManager import PlayerProfileManager
from game_clean.poker.advanced_bot_v2 import AdvancedBot
import os
# --- Setup ---

db_folder = "game_clean/database"
os.makedirs(db_folder, exist_ok=True)

ml_manager = MLModelManager()
ppm = PlayerProfileManager()

# Create the bot
bot_name = "Alice"
bot = AdvancedBot(name=bot_name, ml_manager=ml_manager)

# Generate some fake poker hands for testing
test_hands = [
    # Format: (hole_cards, community_cards, opponent_profile, pot, bet_to_call, stack, position)
    (['Ah', 'Kd'], ['Qs', 'Jd', '10c'], ppm.get_average_profile(), 100, 10, 800, 1),
    (['9h', '7d'], ['2c', '5s', 'Jd'], ppm.get_average_profile(), 80, 8, 500, 2),
    (['Qs', 'Qc'], ['Kh', '10h', '3d'], ppm.get_average_profile(), 150, 15, 1200, 3),
    (['7s', '6s'], ['8s', '9d', '2c'], ppm.get_average_profile(), 60, 5, 400, 4),
]

# --- Play simulated hands ---
for i, hand in enumerate(test_hands):
    hole_cards, community_cards, opp_profile, pot, to_call, stack, position = hand
    bot.set_state(hole_cards, community_cards, opp_profile, pot, to_call, stack, position)

    # Bot makes a decision
    action, bet = bot.make_decision()

    # Log to database
    ppm.update_profile(bot_name, vpip=opp_profile['vpip'], pfr=opp_profile['pfr'],
                       aggression=opp_profile['aggression'], avg_bet_size=bet)
    ppm.log_action(bot_name, stage="flop", vpip=opp_profile['vpip'], pfr=opp_profile['pfr'],
                   aggression=opp_profile['aggression'], board_wetness=bot.estimate_board_wetness(),
                   pot_size=pot, to_call=to_call, stack_size=stack,
                   equity=bot.last_equity, action=action, result="simulated")

print("\n[TEST COMPLETE] Database should now have profiles and action history for Alice.")
ppm.close()

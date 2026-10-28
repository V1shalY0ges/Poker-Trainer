from game_clean.poker.advanced_bot_v2 import AdvancedBot
# COMMENTS ARE DONE

class DummyMLManager:
    def prepare_features(self, *args, **kwargs):
        return args

    def predict_for_player(self, name, features):
        # Simulate a random model prediction
        import random
        actions = ["fold", "call", "raise", "check"]
        action = random.choice(actions)
        bet = random.randint(10, 200)
        return action, bet


# Create an advanced bot with dummy ML
bot = AdvancedBot(name="AdvancedBot_Test", ml_manager=DummyMLManager())

# Dummy opponent profile
opponent_profile = {
    "vpip": 0.3,        # moderate loose player
    "pfr": 0.15,        # standard preflop raiser
    "aggression": 0.4   # somewhat aggressive
}

# Set up a test hand
hole_cards = ["AH", "KH"]         # strong hand
community_cards = ["QH", "JH", "3C"]  # strong draw (royal flush potential)
pot = 200
bet_to_call = 40
stack = 800
position = "BTN"  # button position (late)

# Set the dummy states
bot.set_state(hole_cards, community_cards, opponent_profile, pot, bet_to_call, stack, position)

# Run a decision
action, amount = bot.make_decision()
print(f"\nFinal Decision: {action.upper()} for {amount}\n")

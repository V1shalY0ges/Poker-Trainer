from game_clean.poker.advanced_bot_v2 import AdvancedBot

# Dummy ML manager to simulate decision predictions
class DummyMLManager:
    def prepare_features(self, *args, **kwargs):
        return args

    def predict_for_player(self, name, features):
        import random
        actions = ["fold", "call", "raise", "check"]
        action = random.choice(actions)
        bet = random.randint(10, 200)
        return action, bet


# Instantiate bot
bot = AdvancedBot(name="AdvancedBot_Test", ml_manager=DummyMLManager())

# Dummy opponent profile
opponent_profile = {
    "vpip": 0.35,        # moderately loose
    "pfr": 0.18,         # typical raiser
    "aggression": 0.45   # semi-aggressive
}

# Diverse test hands (preflop + postflop variety)
test_hands = [
    # === Preflop ===
    (["AH", "KH"], []),                        # Premium (AK suited)
    (["9D", "9C"], []),                        # Mid pocket pair
    (["5H", "4H"], []),                        # Suited connectors
    (["2C", "7D"], []),                        # Trash hand

    # === Flop / Postflop ===
    (["AH", "KH"], ["QH", "JH", "3C"]),        # Royal flush draw
    (["AH", "10H"], ["KH", "3H", "9C"]),       # Top pair + flush draw
    (["7S", "7H"], ["7C", "QH", "3D"]),        # Flopped trips
    (["KH", "10C"], ["KS", "10S", "2D"]),      # Two pair
    (["9H", "9S"], ["9D", "3C", "3H"]),        # Full house
    (["8D", "9D"], ["10D", "JD", "2C"]),       # Made straight flush draw
    (["QC", "JD"], ["10S", "9H", "3C"]),       # Open-ended straight draw
    (["3S", "3C"], ["7H", "10D", "2S"]),       # Weak pocket pair
    (["AS", "KD"], ["2C", "7S", "9H"]),        # Two overcards, dry board
]

# Testing parameters
pot = 200
bet_to_call = 40
stack = 800
position = "BTN"  # button

# Run tests using the test hands
for i, (hole, board) in enumerate(test_hands, start=1):
    print(f"\n=== TEST {i} ===")
    print(f"Hole Cards: {hole}")
    print(f"Board: {board}")

    # Generate the action after defining the state
    bot.set_state(hole, board, opponent_profile, pot, bet_to_call, stack, position)
    equity = bot.estimate_equity(num_simulations=500)
    action, amount = bot.make_decision()
    # Print the result
    print(f"→ Final Equity: {equity:}")
    print(f"→ Final Decision: {action.upper()} for {amount}")
    print("=" * 40)

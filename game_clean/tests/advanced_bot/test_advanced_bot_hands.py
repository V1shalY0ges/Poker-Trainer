

from game_clean.poker.advanced_bot_v2 import AdvancedBot


# === Dummy ML manager (for predictable test output) ===
class DummyMLManager:
    def prepare_features(self, *args, **kwargs):
        return args

    def predict_for_player(self, name, features):
        # Simulate a semi-random model suggestion
        import random
        actions = ["fold", "call", "raise", "check"]
        action = random.choice(actions)
        bet = random.randint(20, 150)
        return action, bet


# === Bot Setup ===
bot = AdvancedBot(name="AdvancedBot_Test", ml_manager=DummyMLManager())

# === Opponent Profiles ===
tight = {"vpip": 0.15, "pfr": 0.1, "aggression": 0.3}
loose = {"vpip": 0.45, "pfr": 0.25, "aggression": 0.7}
balanced = {"vpip": 0.3, "pfr": 0.15, "aggression": 0.4}

# === Test Scenarios ===
test_cases = [
    # --- Preflop ---
    {
        "desc": "Premium preflop hand",
        "hole": ["AH", "KH"],
        "board": [],
        "profile": loose,
        "pot": 60,
        "call": 20,
        "stack": 1000,
        "pos": "BTN"
    },
    # --- Flop ---
    {
        "desc": "Strong flush draw (royal draw)",
        "hole": ["AH", "KH"],
        "board": ["QH", "JH", "3C"],
        "profile": balanced,
        "pot": 200,
        "call": 40,
        "stack": 800,
        "pos": "BTN"
    },
    # --- Turn ---
    {
        "desc": "Top pair + nut flush draw",
        "hole": ["AH", "10H"],
        "board": ["10C", "5H", "7H", "3S"],
        "profile": tight,
        "pot": 180,
        "call": 30,
        "stack": 900,
        "pos": "CO"
    },
    # --- River ---
    {
        "desc": "Weak top pair facing aggression",
        "hole": ["KQ", "9D"],
        "board": ["KS", "2D", "7C", "10H", "4S"],
        "profile": loose,
        "pot": 300,
        "call": 100,
        "stack": 600,
        "pos": "SB"
    },
    # --- Bluffs / Marginal ---
    {
        "desc": "Missed flush draw (air hand)",
        "hole": ["9H", "8H"],
        "board": ["AH", "KH", "2C", "7S", "3D"],
        "profile": balanced,
        "pot": 250,
        "call": 60,
        "stack": 700,
        "pos": "BTN"
    }
]


# === Run Tests ===
print("\n===============================")
print("   ADVANCED BOT TEST SUITE")
print("===============================\n")

for i, test in enumerate(test_cases, 1):
    print(f"\n--- TEST {i}: {test['desc']} ---")

    bot.set_state(
        test["hole"], test["board"],
        test["profile"],
        pot=test["pot"], bet_to_call=test["call"],
        stack=test["stack"], position=test["pos"]
    )

    equity = bot.estimate_equity(num_simulations=200)
    action, amount = bot.make_decision()

    print(f"[RESULT] Equity: {equity:.3f}")
    print(f"[RESULT] Final Action: {action.upper()} for {amount}")
    print("-" * 40)

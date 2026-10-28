#THIS ONE KEEPS LOOPINH FOR SOME REASON

from game.poker.table import Table

# ------------------------------
# Mock Player Class
# ------------------------------
class Player:
    def __init__(self, name, chips=500, is_agent=False):
        self.name = name
        self.chips = chips
        self.is_agent = is_agent
        self.hole_cards = []
        self.current_bet = 0
        self.total_contributed = 0
        self.folded = False
        self.all_in = False
        self.starting_stack = chips
        self.hand_score = 0

    def reset_for_new_hand(self):
        self.hole_cards = []
        self.current_bet = 0
        self.total_contributed = 0
        self.folded = False
        self.all_in = False

    def reset_for_new_round(self, stage):
        self.current_bet = 0

# ------------------------------
# Simulation
# ------------------------------
def simulate_n_hands(n_hands=10):
    players = [
        Player("Agent", is_agent=True),
        Player("Bot1"),
        Player("Bot2"),
        Player("Bot3")
    ]

    table = Table(players, big_blind=20, small_blind=10, invalid_mode="soft")

    for hand_num in range(1, n_hands + 1):
        print(f"\n=== Starting Hand {hand_num} ===")
        state = table.start_new_hand()
        done = False
        total_reward = 0

        while not done:
            agent_action, agent_amount = table.choose_bot_action(table.agent_player)
            state, reward, done, info = table.step(agent_action, agent_amount)
            total_reward += reward if isinstance(reward, (int, float)) else 0

        print(f"=== Hand {hand_num} Finished ===")
        print(f"Agent Reward: {total_reward}")
        print("Chips after hand:")
        for p in players:
            print(f"{p.name}: {p.chips}")
        print("-" * 50)

# ------------------------------
# Run Simulation
# ------------------------------
if __name__ == "__main__":
    simulate_n_hands(20)  # Run 20 hands as example

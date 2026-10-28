# test_table_simulation.py

from game_clean.poker.table import Table

# ------------------------------
# Mock Player class with agent flag
# ------------------------------
class Player:
    def __init__(self, name, chips, is_agent=False):
        self.name = name
        self.chips = chips
        self.starting_stack = chips
        self.current_bet = 0
        self.total_contributed = 0
        self.folded = False
        self.all_in = False
        self.hole_cards = []
        self.hand_score = 0
        self.is_agent = is_agent

    def reset_for_new_hand(self):
        self.current_bet = 0
        self.total_contributed = 0
        self.folded = False
        self.all_in = False
        self.hole_cards = []

    def reset_for_new_round(self, stage=None):
        self.current_bet = 0  # bets reset each round

# ------------------------------
# Full Table Simulation
# ------------------------------
def simulate_full_table():
    # Create players: 1 agent + 3 bots
    players = [
        Player("Agent", 500, is_agent=True),
        Player("Bot1", 500),
        Player("Bot2", 300),
        Player("Bot3", 100)
    ]

    table = Table(players)

    # Start first hand
    state = table.start_new_hand()
    print("\n=== Initial Table State ===")
    table.print_table_state()

    # Simulate agent actions in each stage
    done = False
    while not done:
        agent = table.agent_player

        # Agent simple strategy for test: always call if possible
        to_call = table.betmanager.current_bet - agent.current_bet
        if to_call > 0:
            action = "call"
            amount = to_call
        else:
            action = "check"
            amount = None

        state, reward, done, info = table.step(action, amount)

        # Print current table state
        print(f"\nAgent action: {action} {amount if amount else ''}")
        table.print_table_state()

        if done:
            print("\n=== Hand Finished ===")
            print("Reward:", reward)
            print("Final Chips:")
            for p in table.players:
                print(f"{p.name}: {p.chips}")
            break

# ------------------------------
# Run Simulation
# ------------------------------
simulate_full_table()

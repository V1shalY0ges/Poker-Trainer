# --- test_betting.py ---
# COMMENTS ARE DONE
from game_clean.poker.betting import BetManager
from game_clean.poker.potmanager import PotManager

# ------------------------------
# Mock Player class
# ------------------------------
class Player:
    def __init__(self, name, chips):
        self.name = name
        self.chips = chips
        self.current_bet = 0
        self.total_contributed = 0
        self.folded = False
        self.all_in = False
        self.hand_score = 0  # for showdown

    def __repr__(self):
        return f"{self.name}(chips={self.chips}, bet={self.current_bet}, all_in={self.all_in}, folded={self.folded})"

# ------------------------------
# Test function
# ------------------------------
def test_betting_scenarios():
    # Create players
    alice = Player("Alice", 500)
    bob = Player("Bob", 500)
    charlie = Player("Charlie", 300)
    dave = Player("Dave", 100)

    players = [alice, bob, charlie, dave]

    # Assign simple hand scores for showdown
    alice.hand_score = 10
    bob.hand_score = 8
    charlie.hand_score = 9
    dave.hand_score = 7

    # Initialise pot and betting manager
    pot = PotManager(seat_order=[p.name for p in players])
    bm = BetManager(pot)

    # ------------------------------
    # Start a preflop round
    # ------------------------------
    print("\n--- Preflop Round ---")
    bm.reset_for_new_round(players, stage='preflop', big_blind=20)

    # Actions: Alice calls, Bob raises, Charlie calls, Dave all-in
    bm.apply_action(alice, 'call')
    bm.apply_action(bob, 'raise', 100)
    bm.apply_action(charlie, 'call')
    bm.apply_action(dave, 'raise', 100)  # only has 100, should go all-in

    # Remaining players call to match
    next_p = bm.next_player()
    while next_p:
        if next_p.chips >= bm.current_bet - next_p.current_bet:
            bm.apply_action(next_p, 'call')
        else:
            bm.apply_action(next_p, 'call')  # triggers all-in
        next_p = bm.next_player()

    print("\nPlayers after preflop actions:")
    for p in players:
        print(p)

    # ------------------------------
    # Build pots
    # ------------------------------
    pot.build_pots()
    print("\nPots built:")
    for p in pot.pots:
        print(p)

    # ------------------------------
    # Showdown distribution
    # ------------------------------
    winners = [alice, bob, charlie, dave]  # ranked by hand_score in this example
    winnings = pot.distribute_showdown(sorted(winners, key=lambda x: x.hand_score, reverse=True))

    print("\nWinnings after showdown:")
    for name, amount in winnings.items():
        print(f"{name}: {amount}")

# ------------------------------
# Run the test
# ------------------------------
test_betting_scenarios()

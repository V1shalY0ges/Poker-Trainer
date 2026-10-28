from game_clean.poker.betting import BetManager
from game_clean.poker.potmanager import PotManager
import random
# COMMENTS ARE DONE
# Create a simple mock player class
class Player:
    def __init__(self, name, chips):
        self.name = name
        self.chips = chips
        self.current_bet = 0
        self.total_contributed = 0
        self.folded = False
        self.all_in = False
        self.hand_score = 0

def simulate_random_hand(hand_id, debug=False):
    players = [Player("Alice", 500), Player("Bob", 400), Player("Charlie", 300), Player("Diana", 100)]
    pot = PotManager(seat_order=[p.name for p in players])
    bm = BetManager(pot)

    bm.reset_for_new_round(players, stage='preflop', big_blind=20)
    # Random actions
    for p in players:
        if p.folded or p.all_in:
            continue
        action = random.choice(['call', 'raise', 'fold'])
        if action == 'raise':
            bm.apply_action(p, 'raise', random.choice([50, 100, 150]))
        else:
            bm.apply_action(p, action)

    pot.build_pots()

    # Assign random hand strengths
    for p in players:
        p.hand_score = random.randint(1, 10)
    ranked_players = sorted([p for p in players if not p.folded], key=lambda x: x.hand_score, reverse=True)
    winnings = pot.distribute_showdown(ranked_players)

    total_pot = sum(p.amount for p in pot.pots)
    total_distributed = sum(winnings.values())
    # Checkking the winnings feature worked
    if abs(total_pot - total_distributed) > 0:
        if debug:
            print(f"\n[ERROR] Hand {hand_id}: pot={total_pot}, distributed={total_distributed}")
            print("--- Players ---")
            for pl in players:
                print(f"{pl.name}: chips={pl.chips}, bet={pl.current_bet}, contrib={pl.total_contributed}, all_in={pl.all_in}, folded={pl.folded}")
            print("--- Pots ---")
            for pt in pot.pots:
                print(pt)
            print("--- Winnings ---")
            for name, amt in winnings.items():
                print(f"{name}: {amt}")
        return False
    return True


def run_mass_test():
    success = 0
    errors = 0
    for i in range(500):
        if simulate_random_hand(i):
            success += 1
        else:
            errors += 1
    print(f"\nCompleted 500 hands.\n✔ Successful pots: {success}\n Errors detected: {errors}")
    return errors

if __name__ == "__main__":
    bad = run_mass_test()
    if bad > 0:
        print("\n--- Now showing first few error hands in detail ---")
        for i in range(10):
            simulate_random_hand(i, debug=True)

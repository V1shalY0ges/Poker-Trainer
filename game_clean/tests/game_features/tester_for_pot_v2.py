# test_pot_manager.py
# COMMENTS ARE DONE
from game_clean.poker.potmanager import PotManager  # assuming your fixed version is saved as pot_manager.py

# Dummy player class
class DummyPlayer:
    def __init__(self, name, hand_score=0):
        self.name = name
        self.hand_score = hand_score
        self.total_contributed = 0

    def __repr__(self):
        return f"{self.name}(score={self.hand_score}, contrib={self.total_contributed})"

# Show all the pots and the winnings for each
def print_pots_and_winners(pots, results):
    print("\n--- Pots ---")
    for pot in pots:
        print(pot)
    print("\n--- Winnings ---")
    for k, v in results.items():
        print(f"{k}: {v}")


# Different test cases

def test_basic_pot():
    print("\n=== Test 1: Normal Pot ===")

    #Create the players
    p1, p2, p3 = DummyPlayer("Alice", 5), DummyPlayer("Bob", 2), DummyPlayer("Charlie", 3)
    pm = PotManager()

    # Create one pot by having equal contributions
    pm.add_contribution(p1, 100)
    pm.add_contribution(p2, 100)
    pm.add_contribution(p3, 100)
    pm.build_pots()

    # Distribute that one pot and display the results
    results = pm.distribute_showdown([p1, p2, p3])
    print_pots_and_winners(pm.pots, results)


def test_single_all_in():
    print("\n=== Test 2: Single All-In ===")
    p1, p2, p3 = DummyPlayer("Alice", 5), DummyPlayer("Bob", 3), DummyPlayer("Charlie", 4)
    pm = PotManager()

    # Alice goes all-in with less
    pm.add_contribution(p1, 50)
    pm.add_contribution(p2, 100)
    pm.add_contribution(p3, 100)
    pm.build_pots()

    results = pm.distribute_showdown([p1, p2, p3])
    print_pots_and_winners(pm.pots, results)


def test_multiple_all_in():
    print("\n=== Test 3: Multiple All-Ins ===")
    p1, p2, p3, p4 = (
        DummyPlayer("A", 5),
        DummyPlayer("B", 4),
        DummyPlayer("C", 3),
        DummyPlayer("D", 2),
    )
    pm = PotManager()

    # 4 players go all-in for increasing amounts
    pm.add_contribution(p1, 50)
    pm.add_contribution(p2, 100)
    pm.add_contribution(p3, 200)
    pm.add_contribution(p4, 400)
    pm.build_pots()

    results = pm.distribute_showdown([p1, p2, p3, p4])
    print_pots_and_winners(pm.pots, results)


def test_folded_player():
    print("\n=== Test 4: Folded Player ===")
    p1, p2, p3 = DummyPlayer("Alice", 10), DummyPlayer("Bob", 5), DummyPlayer("Charlie", 8)
    pm = PotManager()

    pm.add_contribution(p1, 100)
    pm.add_contribution(p2, 100)
    pm.add_contribution(p3, 100)

    pm.mark_folded(p2)  # Bob folds
    pm.build_pots()

    # Tests that we dont include Bob in the winnings as he folds
    results = pm.distribute_showdown([p1, p2, p3])
    print_pots_and_winners(pm.pots, results)


def test_tied_winners_with_remainder():
    print("\n=== Test 5: Tied Winners + Remainder ===")
    p1, p2, p3 = DummyPlayer("Alice", 9), DummyPlayer("Bob", 9), DummyPlayer("Charlie", 3)
    pm = PotManager(seat_order=["Alice", "Bob", "Charlie"])

    pm.add_contribution(p1, 101)
    pm.add_contribution(p2, 101)
    pm.add_contribution(p3, 101)
    pm.build_pots()

    results = pm.distribute_showdown([p1, p2, p3])
    print_pots_and_winners(pm.pots, results)


# Do each test separately as these are the cases for how endgames work out
test_basic_pot()
test_single_all_in()
test_multiple_all_in()
test_folded_player()
test_tied_winners_with_remainder()

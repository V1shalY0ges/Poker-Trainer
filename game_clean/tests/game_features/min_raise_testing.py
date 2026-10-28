from game_clean.poker.betting import BetManager
# COMMENTS ARE DONE
# Mock player class for testing
class Player:
    def __init__(self, name, chips):
        self.name = name
        self.chips = chips
        self.current_bet = 0
        self.total_contributed = 0
        self.folded = False
        self.all_in = False
        self.facing_raise = False
        self.is_intermediate = False  # bot flag
        self.is_human = True  # human flag for testing

# Mock pot class
class Pot:
    def __init__(self):
        self.pots = []
        self.contributions = {}

    def add_contribution(self, player, amount):
        self.contributions[player.name] = self.contributions.get(player.name, 0) + amount

    def build_pots(self):
        print("Building pots:", self.contributions)
        self.pots.append(self.contributions.copy())

# Testing function
def test_min_raise_logic():
    # Setup
    pot = Pot()
    betmanager = BetManager(pot)
    player1 = Player("Player1", 1000)
    bot = Player("Bot", 500)
    bot.is_human = False
    bot.is_intermediate = True

    players = [player1, bot]

    # Initialise preflop round with big blind = 20
    betmanager.reset_for_new_round(players, stage='preflop', big_blind=20)

    print("\n--- Player1 raises 100 ---")
    betmanager.apply_action(player1, 'raise', 100)
    print(f"Current bet: {betmanager.current_bet}, Min raise: {betmanager.min_raise}\n")

    # Testing that the min raise should not be changed
    print("\n--- Bot tries partial raise 50 (should NOT update min raise) ---")
    betmanager.apply_action(bot, 'raise', 50)
    print(f"Current bet: {betmanager.current_bet}, Min raise: {betmanager.min_raise}\n")

    print("\n--- Player1 raises full raise 200 ---")
    betmanager.apply_action(player1, 'raise', 200)
    print(f"Current bet: {betmanager.current_bet}, Min raise: {betmanager.min_raise}\n")

    print("\n--- Bot goes all-in 300 ---")
    betmanager.apply_action(bot, 'raise', 300)
    print(f"Current bet: {betmanager.current_bet}, Min raise: {betmanager.min_raise}\n")

if __name__ == "__main__":
    test_min_raise_logic()

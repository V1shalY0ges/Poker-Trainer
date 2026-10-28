
# COMMENTS ARE DONE
from itertools import product
from game_clean.poker.hand_evaluator_no_p import HandEvaluator
import random

'''
Copies existing methods which we test out to see if they work

'''
class PokerBot:
    def __init__(self, full_evaluator = None):
        self.full_evaluator = full_evaluator

    def normalise_ranks(self, cards):
        # Make sure cards are always in format like 'AH', '10D', etc.
        return [c.upper() for c in cards]

    def _evaluate_partial_made_hand(self, hole_cards, community_cards):
        """
        Simple placeholder hand evaluator
        This just counts high cards and pairs to give a rough strength number.
        """
        ranks = '23456789TJQKA'
        all_cards = hole_cards + community_cards
        rank_counts = {r: 0 for r in ranks}
        for card in all_cards:
            rank_counts[card[0]] += 1

        # Basic scoring: pairs + high card
        score = 0
        for r, count in rank_counts.items():
            if count == 2:
                score += 10
            elif count == 3:
                score += 30
            elif count == 4:
                score += 100
        # add high card bonus
        high = max(ranks.index(c[0]) for c in all_cards)
        score += high
        return score

    def estimate_strength(self, hole_cards, community_cards, num_simulations=2500, num_opponents=2):
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        suits = ['H', 'D', 'C', 'S']
        full_deck = [r + s for r, s in product(ranks, suits)]

        # Create a deck and eliminate the known cards so player's cards and cards on the board
        known_cards = set(self.normalise_ranks(hole_cards + community_cards))
        deck = [c for c in full_deck if c not in known_cards]
        remaining = 5 - len(community_cards)

        wins = 0
        ties = 0

        for _ in range(num_simulations):
            random.shuffle(deck)

            # Step 1: assign hole cards to each opponent
            opponents = []
            draw_index = 0
            for _ in range(num_opponents):
                opponents.append(deck[draw_index:draw_index + 2])
                draw_index += 2

            # Step 2: complete the community cards
            remaining_community = deck[draw_index:draw_index + remaining]
            full_community = community_cards + remaining_community

            # Step 3: evaluate hands
            if self.full_evaluator:
                my_hand,my_score = self.full_evaluator.evaluate_hand(hole_cards, full_community)
                opp_hand,opp_scores = [
                    self.full_evaluator.evaluate_hand(opp, full_community)
                    for opp in opponents
                ]
            else:
                my_score = self._evaluate_partial_made_hand(hole_cards, full_community)
                opp_scores = [
                    self._evaluate_partial_made_hand(opp, full_community)
                    for opp in opponents
                ]

            # Step 4: compare
            result = 1
            tie_flag = False
            for opp_score in opp_scores:
                cmp_result = self.compare_hands(my_score, opp_score)
                if cmp_result < 0:
                    result = -1  # lost to at least one opponent
                    break
                elif cmp_result == 0:
                    tie_flag = True

            # Step 5: count outcomes
            if result == 1 and not tie_flag:
                wins += 1
            elif tie_flag and result != -1:
                ties += 1

        win_prob = (wins + 0.5 * ties) / num_simulations
        return win_prob


    def compare_hands(self, hand1, hand2):
        for i, j in zip(hand1, hand2):
            if i > j:
                return 1
            elif i < j:
                return -1
        return 0  # complete tie


# --- TEST CODE ---
if __name__ == "__main__":
    bot = PokerBot(full_evaluator= HandEvaluator())

    hole_cards = ['Ah', 'Kd']                 # your hand
    community_cards = ['2c', '7d', '9s']     # example flop

    print("Running Monte Carlo simulation vs 2 opponents...\n")
    win_prob = bot.estimate_strength(hole_cards, community_cards,
                                     num_simulations=3000,
                                     num_opponents=2)

    print(f"Estimated Win Probability (2 opponents): {win_prob:.3f}")

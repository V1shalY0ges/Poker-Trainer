# need to add the import here

import random
from itertools import combinations, product
from collections import Counter

class PartialHandEvaluator:
    def __init__(self, full_evaluator = None):
        self.full_evaluator = full_evaluator


    def estimate_strength(self, hole_cards, community_cards, num_simulations=2500):
        """
        Estimate how strong the hand is likely to be by the river.
        """
        # Use Monte Carlo simulation:
        # 1. Randomly deal remaining community cards
        # 2. Compare against random opponent hands
        # 3. Average win percentage



        '''
        method
        # 1 create a 52 card deck and remove all the hole cards of player and the community cards because these are the known cards
        # 2 run simulations by drawing random cards according to the round so if the round is the turn draw 1 extra card, if flop draw 2 and use a parameter for the number of simulations
        # 3 call existing hand strength evaluator on the complete set of cards to see how strong the hand is
        # 4 MAYBE depending on how long it takes compare hands against opponents to generate some equity
        # 5 Estimate win probability and record wins and losses over all simulations (maybe sql here)
        # 6 calculate expected value using win prob and pot odds
        #7 use the heuristics to determine final action and amount and return
        '''

        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        suits = ['H', 'D', 'C', 'S']
        full_deck = [r + s for r, s in product(ranks, suits)]

        known_cards = set(self.normalise_ranks(hole_cards + community_cards))
        deck = [c for c in full_deck if c not in known_cards]

        remaining = 5 - len(community_cards)

        wins = 0
        ties = 0

        for _ in range(num_simulations):
            # this is where we simulate random completion
            random.shuffle(deck)
            opp_hole = deck[:2]
            remaining_community = deck[2:2 + remaining]
            full_community = community_cards + remaining_community

            # evaluate both hands
            if self.full_evaluator:
                # Use a proper evaluator
                my_hand, my_score = self.full_evaluator.evaluate_hand(hole_cards, full_community)
                opp_hand, opp_score = self.full_evaluator.evaluate_hand(opp_hole, full_community)

                result = self.compare_hands(my_score, opp_score)
            else:
                # Fallback: use heuristic
                my_score = self._evaluate_partial_made_hand(hole_cards, full_community)
                opp_score = self._evaluate_partial_made_hand(opp_hole, full_community)

                result = (my_score > opp_score) - (my_score < opp_score)

            if result > 0:
                wins += 1
            elif result == 0:
                ties += 1
                #ignoring losses for now

        win_prob = (wins + 0.5 * ties) / num_simulations
        return win_prob

    def compare_hands(self, hand1, hand2):
        for i, j in zip(hand1, hand2):
            if i > j:
                return 1
            elif i < j:
                return -1
        return 0  # complete tie


    def monte_carlo(self, hole_cards, community_cards, num_simulations=500, num_opponents=1):

        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        suits = ['H', 'D', 'C', 'S']
        full_deck = [r + s for r, s in product(ranks, suits)]

        # Remove known cards
        known_cards = set(self.normalise_ranks(hole_cards + community_cards))
        deck = [c for c in full_deck if c not in known_cards]

        remaining = 5 - len(community_cards)
        total_equity = 0.0



        for _ in range(num_simulations):
            random.shuffle(deck)

            # --- Step 1: Assign hole cards to opponents ---
            opponents = []
            hand_type_counter = Counter()
            draw_index = 0
            for _ in range(num_opponents):
                opponents.append(deck[draw_index:draw_index + 2])
                draw_index += 2

            # --- Step 2: Complete the community cards ---
            remaining_community = deck[draw_index:draw_index + remaining]
            full_community = community_cards + remaining_community

            # --- Step 3: Evaluate your hand ---
            if self.full_evaluator:
                my_hand, my_score = self.full_evaluator.evaluate_hand(hole_cards, full_community)
                primary_hand = my_hand[0]
                hand_type_counter[primary_hand] += 1
                opp_results = [
                    self.full_evaluator.evaluate_hand(opp, full_community)
                    for opp in opponents
                ]

                opp_hands = [hand for hand, score in opp_results]
                opp_scores = [score for hand, score in opp_results]
            else:
                my_hand, my_score = self._evaluate_partial_made_hand(hole_cards, full_community)
                primary_hand = my_hand[0]

                hand_type_counter[primary_hand] += 1
                opp_results = [
                    self.full_evaluator.evaluate_hand(opp, full_community)
                    for opp in opponents
                ]

                opp_hands = [hand for hand, score in opp_results]
                opp_scores = [score for hand, score in opp_results]
            # --- Step 4: Compare against all opponents ---
            fractional_wins = 0
            for opp_score in opp_scores:
                cmp_result = self.compare_hands(my_score, opp_score)
                if cmp_result > 0:
                    fractional_wins += 1
                elif cmp_result == 0:
                    fractional_wins += 0.5

            # --- Step 5: Add simulation contribution ---
            total_equity += fractional_wins / num_opponents


            # --- Step 6: Average over all simulations ---
        top_hand_types = [hand for hand,_ in hand_type_counter.most_common(3)]
        equity = total_equity / num_simulations
        return top_hand_types, equity

    def monte_carlo_river(self, hole_cards, community_cards, num_opponents=1, num_simulations=2500):
        """
        Estimate equity on the river using Monte Carlo against multiple opponents.

        Parameters:
        -----------
        hole_cards : list of str
            The player's hole cards, e.g. ['Ah', 'Kd']
        community_cards : list of str
            The full 5-card board
        num_opponents : int
            Number of opponents
        num_simulations : int
            Number of Monte Carlo simulations

        Returns:
        --------
        equity : float
            Estimated win probability against multiple opponents
        """
        if not self.full_evaluator:
            raise ValueError("Full evaluator not provided!")

        from itertools import product
        import random

        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        suits = ['H', 'D', 'C', 'S']
        full_deck = [r + s for r, s in product(ranks, suits)]

        # Remove known cards
        known_cards = set(hole_cards + community_cards)
        deck = [c for c in full_deck if c not in known_cards]

        total_equity = 0.0

        for _ in range(num_simulations):
            random.shuffle(deck)

            # Assign hole cards to opponents
            opp_hands = [deck[i * 2:(i + 1) * 2] for i in range(num_opponents)]

            # Evaluate player's hand
            player_hand, player_score = self.full_evaluator.evaluate_hand(hole_cards, community_cards)

            # Fractional wins for this simulation
            fractional_wins = 0
            for opp_hole in opp_hands:
                opp_hand,opp_score = self.full_evaluator.evaluate_hand(opp_hole, community_cards)
                cmp_result = self.compare_hands(player_score, opp_score)
                if cmp_result > 0:
                    fractional_wins += 1
                elif cmp_result == 0:
                    fractional_wins += 0.5

            # Normalise by number of opponents and add to total equity
            total_equity += fractional_wins / num_opponents

        # Average over all simulations
        equity = total_equity / num_simulations
        return equity

    def estimate_river_equity(self, hole_cards, community_cards, num_opponents=1, num_simulations=2500):
        """
        Calculate exact equity on the river using the full hand evaluator.

        Parameters:
        -----------
        hole_cards : list of str
            The player's hole cards, e.g. ['Ah', 'Kd']
        community_cards : list of str
            The full 5-card board
        num_opponents : int
            Number of random opponents to simulate
        num_simulations : int
            How many Monte Carlo simulations to run

        Returns:
        --------
        equity : float
            Estimated win probability on the river
        """
        if not self.full_evaluator:
            raise ValueError("Full evaluator not provided!")
        hand_type_counter = Counter()

        # Prepare the deck excluding known cards
        # Prepare the deck excluding known cards
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']  # note '10' stays as '10'
        suits = ['H', 'D', 'C', 'S']
        full_deck = [r + s for r in ranks for s in suits]

        # Remove known cards (raw, as given to evaluator)
        known_cards = set(hole_cards + community_cards)
        deck = [c for c in full_deck if c not in known_cards]

        wins = 0
        ties = 0
        total = 0

        for _ in range(num_simulations):
            random.shuffle(deck)

            # Generate opponents' hands
            opp_hands = [deck[i * 2:(i + 1) * 2] for i in range(num_opponents)]

            # Evaluate player's hand
            player_hand,player_score = self.full_evaluator.evaluate_hand(hole_cards, community_cards)
            hand_type_counter[player_hand[0]] += 1

            # Compare against all opponents
            result = 1  # assume player wins initially
            for opp_hole in opp_hands:
                opp_hand,opp_score = self.full_evaluator.evaluate_hand(opp_hole, community_cards)
                cmp = self.compare_hands(player_score, opp_score)
                if cmp < 0:
                    result = -1  # lost
                    break
                elif cmp == 0:
                    result = 0  # tie

            if result > 0:
                wins += 1
            elif result == 0:
                ties += 1
            total += 1
        top_hand_types = [hand for hand,_ in hand_type_counter.most_common(3)]

        equity = (wins + 0.5 * ties) / total
        return top_hand_types, equity

    # HELPER: EVALUATE MADE HANDS (PAIR / SET / FLUSH)
    # ----------------------------------------------------------------------
    def _evaluate_partial_made_hand(self, hole_cards, community_cards):
        """
        Simple rule-based system to detect made hands
        before the river (pair, two pair, set, trips, etc.).

        Returns:
        --------
        float
            Base strength score between 0.0 and 1.0
            (used by quick_equity_estimate).
        """
        # e.g. Pair = 0.4, Two Pair = 0.6, Set = 0.7, Flush (made) = 0.85, etc.
        cards = self.normalise_ranks(hole_cards + community_cards)
        ranks = [c[:-1] for c in cards]


        suits = [c[-1] for c in cards] #MAY NOT WORK FOR CARDS LIKE 10S

        rank_order = '23456789TJQKA'
        rank_values = {r: i for i, r in enumerate(rank_order)}

        rank_counts = {r: ranks.count(r) for r in set(ranks)}
        suit_counts = {s: suits.count(s) for s in set(suits)}

        #check for flush
        flush = any(count >= 5 for count in suit_counts.values())

        #check for straight
        unique_ranks = sorted(set(rank_values[r] for r in ranks))
        straight = False
        for i in range(len(unique_ranks) - 4):
            if unique_ranks[i + 4] - unique_ranks[i] == 4:
                straight = True
                break

        if set(['A', '2', '3', '4', '5']).issubset(ranks):
            straight = True

        counts = sorted(rank_counts.values(), reverse=True)

        if 4 in counts:
            return 0.95  # Four of a Kind
        elif 3 in counts and 2 in counts:
            return 0.9  # Full House
        elif flush and straight:
            return 1.0  # Straight Flush
        elif flush:
            return 0.8
        elif straight:
            return 0.75
        elif 3 in counts:
            return 0.65
        elif counts.count(2) >= 2:
            return 0.55
        elif 2 in counts:
            return 0.4
        else:
            return 0.2  # High card / nothing yet

    def normalise_ranks(self, cards):
        rank_map = {'10': 'T', 'J': 'J', 'Q': 'Q', 'K': 'K', 'A': 'A'}
        normalised = []
        for c in cards:
            r = c[:-1]
            s = c[-1]
            r = rank_map.get(r, r)  # convert '10' to 'T', leave 2-9 as-is
            normalised.append(r + s)
        return normalised

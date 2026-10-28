# COMMENTS ARE DONE


# add the imports
import random
# Used for shuffling decks and randomly selecting opponent hands in Monte Carlo simulations

from itertools import product
# Used to generate all combinations of ranks and suits to create a full deck of cards

from datetime import datetime
# Used for timestamping bot decisions when logging/debugging

from collections import Counter
# Used to count how often different hand types occur during simulations

from game_clean.managers.PlayerProfileManager import PlayerProfileManager
# Manages stored statistics about opponent behaviour (VPIP, aggression, etc.)

from game_clean.poker.hand_evaluator_no_p import HandEvaluator
# Evaluates poker hands and returns both a hand category and a numerical score

from game_clean.ml.feature_extractor import FeatureExtractor
# Extracts numerical features used by the ML model for prediction



class AdvancedBot:
    '''

    Class is used to create the advanced bot
    It uses both the monte carlo algorihtms combined with the ml models to accurately determine the optimal move
    '''
    def __init__(self, name, ml_manager=None):
        self.name = name
        self.evaluator = HandEvaluator()
        # self.profile_manager = PlayerProfileManager()

        # ML manager handles predicting actions based on extracted features
        self.ml_manager = ml_manager

        # Feature extractor converts game state into ML-ready inputs
        self.feature_extractor = FeatureExtractor()

        self.hole_cards = None
        self.community_cards = []

        # Placeholder for player list (useful for expansion/multiway pots)
        self.players = []

        self.num_simulations = 1000  # Monte Carlo simulations

        # Default aggression level when opponents are new and no data exists
        self.default_aggression = 0.5

        self.last_equity = 0.0
        self.current_pot = 0
        self.bet_to_call = 0
        self.stack = 0
        self.position = None

    def set_state(self, hole_cards, community_cards, opponent_profile, pot, bet_to_call, stack, position):
        # The method is used to store and set the full current game state into the bot

        # this gives the advanced bot all the information it needs of the current stage and position that it is in
        self.hole_cards = hole_cards
        self.community_cards = community_cards

        # Store opponent statistics (vpip, pfr, aggression, etc.)
        self.opponent_profile = opponent_profile


        self.current_pot = pot # How much is currently in the main pot

        # Store how much the bot must pay to call
        self.bet_to_call = bet_to_call
        self.stack = stack

        # Store bot’s position at the table
        self.position = position

    def estimate_equity(self, num_simulations=None):
        '''
        this method is used to calculate the equity by using the monte carlo method to simulate
        all possible hands that the opponent could potentially have
        it then compares your hand score against opponent hand score over all the num of simulations
        it produces a percentage of how likely you are to win

        '''
         # Ensures we have a num of simulations to use if not uses the default defined initially
        if num_simulations is None:
            num_simulations = self.num_simulations


        # Builds a random deck using the ranks and suits combined with itertools
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        suits = ['H', 'D', 'C', 'S']
        full_deck = [r + s for r, s in product(ranks, suits)]

        # These are our private cards and board cards which we need to remove
        known_cards = set(self.hole_cards + self.community_cards)
        deck = [c for c in full_deck if c not in known_cards]

        # Stores in how many simulations do we win or tie
        wins = 0
        ties = 0

        # Stores a counter for the hand type we end up with in each simulation to identify the
        # most common
        hand_types = Counter()

        # Here we get the info of the opponent previous stats from the database and if this is
        # a new opponent use global values
        remaining = 5 - len(self.community_cards)
        vpip = self.opponent_profile.get("vpip", 0.25)
        opp_range = self.get_opponent_range(vpip)

        print(f"Hole Cards: {self.hole_cards}")
        print(f"Board: {self.community_cards}")
        print(f"Opponent range size: {len(opp_range)} hands")

        # Run the Monte Carlo simulations
        for sim in range(num_simulations):
            used_cards = set()

            # Shuffle the remaining deck
            random.shuffle(deck)
            # Filter any opponent hands that clash with known cards
            valid_hands = [h for h in opp_range if not (set(h) & known_cards)]
            if not valid_hands:
                continue
            # Randomnly choose opponent hole cards
            opp_hand = random.choice(valid_hands)
            used_cards.update(opp_hand)
            # Remove used cards from the deck
            remaining_cards = [c for c in deck if c not in used_cards]
            random.shuffle(remaining_cards)
            # Deal the remaining board cards
            extra = remaining_cards[:remaining]
            full_board = self.community_cards + extra
            # Evalaute the bot's hand
            my_hand, my_score = self.evaluator.evaluate_hand(self.hole_cards, full_board)
            # Track the hand category
            primary_hand = my_hand[0]
            hand_types[primary_hand] += 1
            # Evaluate the simualted opponent hands
            opp_hand, opp_score = self.evaluator.evaluate_hand(opp_hand, full_board)
            # Compare the scores
            result = self.compare_hands(my_score, opp_score)
            # Update the counters
            if result > 0:
                wins += 1
            elif result == 0:
                ties += 1

            # Debugging for the first few simulations
            if sim < 5:
                print(f"[Sim {sim}] Opp: {opp_hand}, Board: {full_board}")
                print(f"    My={my_score}, Opp={opp_score}, Result={result}")

        # Calculate final equity
        equity = (wins + 0.5 * ties) / num_simulations

        # Debug summary
        print(f"Total Wins={wins}, Ties={ties}, Simulations={num_simulations}")

        # Store equity
        self.last_equity = equity

        # Return the top 3 most common hand types and the equity
        top_hand_types = [hand for hand, _ in hand_types.most_common(3)]
        return top_hand_types, equity

    def get_opponent_range(self, vpip):

        '''
        Generates a weighted opponent hand range based on VPIP.
        Higher VPIP = looser range.
        '''

        # Hardcoded ranked starting hands
        ranked_hands = [
            # Premium
            ['A', 'A'], ['K', 'K'], ['Q', 'Q'], ['A', 'K'],
            ['J', 'J'], ['A', 'Q'], ['K', 'Q'], ['10', '10'],
            ['A', 'J'], ['K', 'J'], ['Q', 'J'],
            # Medium
            ['9', '9'], ['8', '8'], ['7', '7'], ['A', '10'], ['K', '10'], ['Q', '10'], ['J', '10'],
            # Suited connectors
            ['A', '9'], ['K', '9'], ['Q', '9'], ['10', '9'], ['9', '8'], ['8', '7'], ['7', '6'], ['6', '5']
        ]

        # Determine how many hands to include based on VPIP
        cutoff = int(vpip * len(ranked_hands))
        selected = ranked_hands[:max(1, cutoff)]

        suits = ['H', 'D', 'C', 'S']
        hands = []

        # Generate all suited combinations
        for r1, r2 in selected:
            for s1 in suits:
                for s2 in suits:
                    if s1 != s2:
                        hands.append([r1 + s1, r2 + s2])
        return hands

    def compare_hands(self, hand1, hand2):
        # Compares two numeric hand scores
        if hand1 > hand2:
            return 1
        elif hand1 < hand2:
            return -1
        else:
            return 0

    def make_decision(self):
        '''
        this is the function which the bot uses to make its overall decision
        the way the decision making works is it computes the equity using the filtered monte carlo simulations
        it uses the ml manager to predict the action it should and the amount and it combines both using some decision thresholds
        including other measures like pot odds and stack ratio
        this produces a final action and amount that the bot will play

        '''



        # Compute equity and get the common hand types
        top_hand_types, equity = self.estimate_equity()

        # Calculate pot odds
        pot_odds = self.bet_to_call / (self.current_pot + self.bet_to_call) if self.bet_to_call > 0 else 0

        # Stack to pot ratio
        stack_ratio = self.stack / (self.current_pot + 1)


        # Extract opponent stats
        opp_vpip = self.opponent_profile.get("vpip", 0.25)
        opp_pfr = self.opponent_profile.get("pfr", 0.15)
        opp_aggression = self.opponent_profile.get("aggression", 0.3)

        # Board texture
        board_wetness = self.estimate_board_wetness()

        # ML prediction (if enabled)
        if self.ml_manager:
            features = self.feature_extractor.extract(
                equity=equity,
                pot=self.current_pot,
                bet_to_call=self.bet_to_call,
                stack=self.stack,  # still required for signature but not used
                vpip=opp_vpip,
                pfr=opp_pfr,
                aggression=opp_aggression,
                board_wetness=board_wetness
            )
            # Getting the ml predicted action using the input features
            ml_action, ml_bet = self.ml_manager.predict_for_player(self.name, features)

            # Validating the action to ensure it complies with the current state
            ml_action, ml_bet = self.validate_ml_action(ml_action, ml_bet)
        else:
            ml_action, ml_bet = None, 0

        # Decision thresholds
        call_threshold = pot_odds
        raise_threshold = call_threshold + (0.15 * (1 - opp_aggression))
        fold_threshold = 0.05 / (1 + stack_ratio)


        # Rule-based fallback decision
        if equity < fold_threshold:
            base_action = "fold"
            base_amount = 0
        elif equity < call_threshold:
            base_action = "call"
            base_amount = self.bet_to_call
        elif equity > raise_threshold:
            base_action = "raise"
            base_amount = min(self.stack, int((self.current_pot * equity)))
        else:
            base_action = "check"
            base_amount = 0

        final_action, final_amount = base_action, base_amount

        # ML override logic if enabled to get the combined optimal action and bet size
        if self.ml_manager:
            if ml_action == "raise" and equity > 0.55:
                final_action, final_amount = "raise", ml_bet or base_amount
            elif ml_action == "call" and equity >= call_threshold:
                final_action, final_amount = "call", base_amount
            elif ml_action == "fold" and equity < 0.25:
                final_action, final_amount = "fold", 0

        # Log decision
        self.log_decision(equity, pot_odds, final_action, final_amount)

        return final_action, final_amount

    def estimate_board_wetness(self):
        '''
        This is a method to estimate how dry the board is because the ml manager will use this as a stat for the prediction of an action

        Estimates how draw-heavy the board is (flush + straight potential).

        '''
        if not self.community_cards:
            return 0.0

        ranks = []
        suits = []

        # Extract ranks and suits
        for card in self.community_cards:
            rank = card[:-1]
            suit = card[-1]
            ranks.append(rank)
            suits.append(suit)

        # Flush potential
        suit_counts = max(suits.count(s) for s in suits)
        flush_potential = (suit_counts - 1) / 4

        # Straight potential
        rank_values = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        indices = sorted(rank_values.index(r) for r in ranks if r in rank_values)

        connectivity = 0
        for i in range(1, len(indices)):
            if indices[i] - indices[i - 1] <= 1:
                connectivity += 1

        straight_potential = connectivity / 4

        # Final wetness score
        wetness = min(1.0, flush_potential + straight_potential)
        return wetness

    def validate_ml_action(self, action, bet_amount):
        '''
        This will ensure that the action the ml manager predicts is a vlaid action that the bot can play given any scenario it is put in
        if the action is invalid then default to forced actions
        '''

        # Round bet amount to nearest 5 because ml manager outputs a float
        bet_amount = round(bet_amount / 5) * 5

        # Determine the legal actions
        if self.bet_to_call == 0:
            valid_actions = ["check", "raise"]
        else:
            valid_actions = ["fold", "call", "raise"]

        # Check the action and force new actions if needed
        if action not in valid_actions:
            if self.bet_to_call == 0:
                action = "check"
                bet_amount = 0
            else:
                action = "fold"
                bet_amount = 0

        # Validate the raise amount
        if action == "raise":
            # Get the minimum raise and check that the raise amount complies with it
            min_raise = max(self.bet_to_call * 2, self.bet_to_call + 1)
            if bet_amount < min_raise:
                bet_amount = min_raise
            bet_amount = min(bet_amount, self.stack)
            if bet_amount <= self.bet_to_call:
                if self.stack > self.bet_to_call:
                    action = "call"
                    bet_amount = self.bet_to_call
                else:
                    action = "fold"
                    bet_amount = 0
        elif action == "call":
            if self.bet_to_call == 0:
                action = "check"
                bet_amount = 0
            else:
                bet_amount = min(self.bet_to_call, self.stack)
        elif action in ["fold", "check"]:
            bet_amount = 0

        return action, bet_amount

    def log_decision(self, equity, pot_odds, action, amount):
        # A method to use for debugging as this doesnt add to the database just prints out so we can see if the calculations and actions make sense
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {self.name} Decision:")
        print(f"  Equity: {equity:.3f} | Pot Odds: {pot_odds:.3f}")
        print(f"  Action: {action.upper()} ({amount})\n")

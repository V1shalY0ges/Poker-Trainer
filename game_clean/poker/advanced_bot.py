from game_clean.poker.partial_hand_evaluator import PartialHandEvaluator
from game_clean.poker.hand_evaluator_no_p import HandEvaluator
from game_clean.managers.PlayerProfileManager import PlayerProfileManager
import random
import json


class AdvancedBot:
    """
    Intermediate Poker Bot

    Uses preflop range charts, postflop hand evaluation, equity estimation,
    pot odds comparison, and controlled bluffing logic to decide actions.
    """

    def __init__(self, name, chips, community_cards=None, bluff_frequency=0.08, aggression_factor=1.2):
        """
        Initialise bot parameters and strategy settings.
        """
        self.name = name
        self.chips = chips
        self.bluff_frequency = bluff_frequency
        self.aggression_factor = aggression_factor
        self.partial_hand_evaluator = PartialHandEvaluator(full_evaluator=HandEvaluator())
        self.community_cards = community_cards
        '''
        with open("preflop_chart.json", "r") as file:
            preflop_table = json.load(file)
        '''
        self.preflop_table = None
        self.profile_manager = PlayerProfileManager()


    # -----------------------------
    # PUBLIC INTERFACE
    # -----------------------------

    def get_action(self, game_state, player):
        """
        Main entry point. Returns an action dict such as:
        {"type": "call", "amount": 100}
        """

        if game_state['stage'] == 'preflop':
            action, amount = self.query_preflop(game_state, player)



        # need to add postflop strategy here
        else:
            action_dict = self.postflop_strategy(player.hole_cards,
                                                 self.community_cards, game_state)
            return action_dict

        return action, amount

    # -----------------------------
    # PREFLOP STRATEGY
    # -----------------------------

    def query_preflop(self, game_state, player, num_players=2):
        position = game_state['position']
        hand = player.hole_cards
        try:
            decision = self.preflop_table[str(num_players)][position][hand]
            action = decision["action"]
            size = decision.get("size", None)
            return action, size

        except KeyError:
            # If hand or position not found, default to fold
            return "fold", None

    def preflop_strategy(self, game_state, player):
        """
        Determines preflop action based on hand ranges, table position, and some randomness.
        """
        hand_category = self.determine_hand_category(player)
        position = game_state.get('position', 'BTN')
        facing_raise = game_state.get('facing_raise', False)

        chart = self.preflop_charts.get(position, {})

        print(f"Hand: {hand_category}, Position: {position}, Facing Raise: {facing_raise}")
        print(f"Open range: {chart.get('open_raise', set())}")
        print(f"Three-bet range: {chart.get('three_bet', set())}")
        print(f"Call vs raise range: {chart.get('call_vs_raise', set())}")

        # --- Facing a raise ---
        if facing_raise:
            if self.hand_in_range(hand_category, chart.get("three_bet", set())):
                return {"type": "raise", "amount": game_state["min_raise"] * 3}

            elif self.hand_in_range(hand_category, chart.get("call_vs_raise", set())) or random.random() < 0.05:
                # occasional light call
                return {"type": "call", "amount": game_state["to_call"]}

            else:
                return {"type": "fold"}

        # --- Not facing a raise (open raise or limp) ---
        else:
            if self.hand_in_range(hand_category, chart.get("open_raise", set())):
                return {"type": "raise", "amount": game_state["big_blind"] * 2.5}

            # 25% chance to limp with small pairs / connectors
            suited_connectors = {"65s", "76s", "87s", "98s", "T9s"}
            small_pairs = {"22", "33", "44", "55", "66"}

            if hand_category in suited_connectors or hand_category in small_pairs:
                if random.random() < 0.25:
                    return {"type": "call", "amount": game_state["big_blind"]}

            return {"type": "fold"}

    def normalise_ranks(self, cards):
        # purpose is to convert the ranks into understandable characters
        rank_map = {'10': 'T', 'J': 'J', 'Q': 'Q', 'K': 'K', 'A': 'A'}
        normalised = []
        for c in cards:
            r = c[:-1]
            s = c[-1]
            r = rank_map.get(r, r)  # convert '10' to 'T', leave 2-9 as-is
            normalised.append(r + s)
        return normalised

    def determine_hand_category(self, player):
        """
        Converts two hole cards into shorthand format like 'AKs', 'T9o', '77', etc.
        """
        normalised = self.normalise_ranks(player.hole_cards)
        card1, card2 = normalised
        r1, s1 = card1[:-1], card1[-1]
        r2, s2 = card2[:-1], card2[-1]

        ranks_order = "23456789TJQKA"

        # Ensure r1 is always the higher rank
        if ranks_order.index(r1) < ranks_order.index(r2):
            r1, r2, s1, s2 = r2, r1, s2, s1

        # Pairs
        if r1 == r2:
            return r1 + r2

        # Suited or offsuit
        suited = (s1 == s2)
        return r1 + r2 + ("s" if suited else "o")

    def hand_in_range(self, hand, range_set):
        """
        Checks if a hand like 'AJs' or 'TT' fits inside a range set using standard poker notation.
        """
        ranks = "23456789TJQKA"
        r1, r2, suited_flag = hand[0], hand[1], hand[2] if len(hand) == 3 else ""
        suited = (suited_flag == "s")

        for pattern in range_set:
            # Exact match
            if hand == pattern:
                return True

            # --- Pairs (e.g., '77+' means 77, 88, 99, ..., AA)
            if len(pattern) == 3 and pattern[2] == '+':
                base = pattern[:2]
                if base[0] == base[1] and r1 == r2:
                    if ranks.index(r1) >= ranks.index(base[0]):
                        return True

            # --- Suited or offsuit with '+' (e.g., 'A2s+', 'KTo+') ---
            if len(pattern) == 4 and pattern[3] == '+':
                p_r1, p_r2, p_s = pattern[0], pattern[1], pattern[2]
                if suited and p_s == 's' and r1 == p_r1 and ranks.index(r2) >= ranks.index(p_r2):
                    return True
                if not suited and p_s == 'o' and r1 == p_r1 and ranks.index(r2) >= ranks.index(p_r2):
                    return True

        return False

    # -----------------------------
    # POSTFLOP STRATEGY

    def postflop_strategy(self, hole_cards, community_cards, game_state, num_opponents=1):
        """
        Determines postflop action using equity, pot odds, and bluffing logic.

        """
        num_opponents = num_opponents
        action_dict = {}

        action_dict["type"] = None
        action_dict["amount"] = None
        action_dict["equity"] = None
        action_dict['pot_odds'] = None

        pot = game_state['pot']
        stage = game_state['stage']
        to_call = game_state['to_call']
        min_raise = game_state['min_raise']

        top_hand_types, equity = self.get_hand_equity(hole_cards, community_cards, stage, num_opponents)

        self.last_equity = equity

        # --- Compute pot odds ---
        pot_odds = self.calculate_pot_odds(pot, to_call)

        # Calculate raise amount based on hand strength and aggression
        proposed_raise = self.calculate_raise_amount(
            pot, min_raise=min_raise, max_raise=self.chips,  # NEED TO ADJUST BY ADDING IN THE THE LAST ROUND BET
            hand_strength=equity, stage=stage
        )

        # Chance of bluffing
        do_bluff = self.should_bluff({}, equity, draw_strength=0)
        fold_equity = 0.15 if do_bluff else 0.0

        # Calculate expected value of call and raise
        ev_call = self.evaluate_expected_value(equity, pot, to_call)
        ev_raise = self.evaluate_expected_value(equity, pot, raise_amount=proposed_raise, fold_equity=fold_equity)

        threshold_call = pot_odds * 1.0
        threshold_raise = pot_odds * 1.3 / self.aggression_factor

        # a) Fold weak hands below pot odds if no bluffing
        if equity < threshold_call * 0.9 and not do_bluff:
            action_dict['type'] = 'fold'
            action_dict['amount'] = 0

        # b) Value raise: strong hands
        if (equity >= threshold_raise and equity > 0.45) or ev_raise > ev_call:
            action_dict['type'] = 'raise'
            action_dict['amount'] = proposed_raise

        # c) Semi-bluff: medium-strength draws
        elif 0.25 < equity < 0.45 and random.random() < 0.15:
            bluff_amount = self.calculate_raise_amount(pot, min_raise, self.chips, 0.3, stage)
            action_dict['type'] = 'raise'
            action_dict['amount'] = bluff_amount

        # d) Call if profitable
        elif equity >= max(threshold_call, pot_odds) or ev_call > 0:
            action_dict['type'] = 'call'
            action_dict['amount'] = to_call

        # e) Otherwise fold
        else:
            action_dict['type'] = 'fold'
            action_dict['amount'] = 0

        action_dict['equity'] = equity
        action_dict['pot_odds'] = pot_odds
        action_dict['top_hand_types'] = top_hand_types

        return action_dict

    def get_hand_equity(self, hole_cards, community_cards, stage, num_simulations=2500, num_opponents=1):
        """
        Returns the estimated equity of the hand based on the stage:
        - Flop / Turn: use Monte Carlo simulation
        - River: deterministic evaluation using full evaluator
        """
        stage = stage.lower()

        if stage in ["flop", "turn"]:
            # Use Monte Carlo for accurate probability
            '''
            equity = self.partial_hand_evaluator.estimate_strength(
                hole_cards, community_cards, num_simulations=num_simulations
            )
            '''
            top_hand_types, equity = self.partial_hand_evaluator.monte_carlo(
                hole_cards, community_cards, num_simulations=num_simulations, num_opponents=num_opponents
            )


        elif stage == "river":
            if self.partial_hand_evaluator.full_evaluator:
                # Use the new river function to calculate exact equity
                top_hand_types, equity = self.partial_hand_evaluator.estimate_river_equity(
                    hole_cards, community_cards,
                    num_opponents=num_opponents,
                    num_simulations=num_simulations
                )
            else:
                # Fallback: heuristic evaluation if no full evaluator
                top_hand_types, equity = self.partial_hand_evaluator._evaluate_partial_made_hand(
                    hole_cards, community_cards
                )

        else:
            raise ValueError(f"get_hand_equity() should only be used postflop, not for stage '{stage}'.")

        # Clamp equity to 0-1 range
        return top_hand_types, max(0.0, min(1.0, equity))

    # -----------------------------
    # POT ODDS / EXPECTED VALUE
    # -----------------------------

    def calculate_pot_odds(self, pot, to_call):
        """
        Computes pot odds ratio for deciding whether to call.
        """
        if to_call == 0:
            return 0
        return to_call / (pot + to_call)

    def evaluate_expected_value(self, equity, pot, to_call=0, raise_amount=0, fold_equity=0):
        """
        Calculates expected value (EV) of calling.
        """
        if raise_amount == 0:
            ev = equity * (pot + to_call) - (1 - equity) * to_call
            return ev

        ev_if_fold = fold_equity * pot
        # If opponent calls, EV is like a call with your raise committed
        ev_if_call = (1 - fold_equity) * (equity * (pot + raise_amount) - (1 - equity) * raise_amount)

        ev = ev_if_fold + ev_if_call
        return ev

    # -----------------------------
    # BLUFFING & RANDOMISATION
    # -----------------------------

    def should_bluff(self, game_state, hand_strength, draw_strength):
        """
        Determines whether to bluff or semi-bluff based on conditions and probability.
        """

        # Example: bluff more often if hand is weak but pot is small
        bluff_chance = self.bluff_frequency * (1 - hand_strength)
        return random.random() < bluff_chance

    # -----------------------------
    # BET SIZING
    # -----------------------------

    def select_bet_size(self, pot, stage, strength, for_bluff=False):
        """
        Chooses bet size based on context and aggression factor.
        """
        base_sizing = {
            "flop": (0.4, 0.7),  # typically smaller bets on flop
            "turn": (0.5, 0.9),
            "river": (0.6, 1.2)
        }

        low, high = base_sizing.get(stage, (0.4, 0.8))

        if for_bluff:
            bet_fraction = random.uniform(low * 0.6, low)

        else:
            # Stronger hands bet bigger
            if strength > 0.8:
                bet_fraction = random.uniform(high * 0.8, high)
            elif strength > 0.6:
                bet_fraction = random.uniform(low, high * 0.8)
            elif strength > 0.4:
                bet_fraction = random.uniform(low * 0.8, high * 0.6)
            else:
                bet_fraction = random.uniform(low * 0.5, low * 0.8)

            # Apply aggression factor (default 1.2)
        bet_fraction *= self.aggression_factor

        # Final numeric bet size (rounded)
        bet_amount = int(pot * bet_fraction)
        bet_amount = max(1, bet_amount)  # safety clamp
        return bet_amount

    def calculate_raise_amount(self, pot, min_raise, max_raise, hand_strength, stage='flop'):
        """
        Determines optimal raise amount given current pot and limits.
        """
        base_bet = self.select_bet_size(pot, stage, hand_strength)
        raise_amount = max(min_raise, min(base_bet, max_raise))
        if hand_strength > 0.8:
            raise_amount = min(max_raise, int(raise_amount * self.aggression_factor))

        raise_amount = max(min_raise, raise_amount)

        return int(raise_amount)

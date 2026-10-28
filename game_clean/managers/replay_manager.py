# COMMENTS ARE COMPLETED



from game_clean.managers.database_manager import DatabaseManager
from game_clean.poker.advanced_bot_v2 import AdvancedBot
from game_clean.managers.PlayerProfileManager import PlayerProfileManager
from game_clean.poker.intermediate_bot import IntermediateBot
from game_clean.ml.ml_model_manager import MLModelManager
import os
# do all the imports

class GameState:
    def __init__(self, players, community_by_stage):

        # we initialise the game state which is the template for any replayed game state it will use this and
        # add in the unique info at eaCH state
        self.players = players
        self.community_by_stage = community_by_stage
        # this tracks each player's remaining chips
        # p[0] = player_id, p[3] = starting stack
        self.stacks = {p[0]: p[3] for p in players}
        self.contributions = {p[0]: 0 for p in players}
        self.folded = set()
        self.pot = 0
        self.board = []
        self.stage = 'preflop'
        self.current_bet = 0
        self.last_raise_size = 0



    def apply_action(self, action):

        """
        This applies a single historical action to the game state.
        This is used to rebuild the game step-by-step.
        """

        # Unpack database action tuple

        _, _, player_id, stage, action_type, amount, _ = action


        # If the stage has changed, reset betting state

        if stage != self.stage:

            self.stage = stage
            self.board = self.community_by_stage.get(stage, [])             # Load new community cards for this stage

            # Reset betting round
            self.current_bet = max(self.contributions.values())
            self.contributions = {pid: 0 for pid in self.contributions}
            self.last_raise_size = 0


        # Handle fold action

        if action_type == "fold":
            self.folded.add(player_id)

        # Handle bet or raise

        elif action_type in ("bet", "raise"):
            # Prevent betting more chips than available
            bet = min(amount, self.stacks[player_id])
            to_call = self.current_bet - self.contributions[player_id]
            total_contribution = to_call + bet
            # Track raise size for minimum raise rules

            if bet > 0:
                self.last_raise_size = bet

            # Apply the bet
            self.stacks[player_id] -= total_contribution
            self.contributions[player_id] += total_contribution

            # Update current bet
            self.current_bet = max(self.current_bet, self.contributions[player_id])



        # Handle call action
        elif action_type == "call":
            to_call = self.current_bet - self.contributions[player_id]
            call_amt = min(to_call, self.stacks[player_id])
            self.stacks[player_id] -= call_amt
            self.contributions[player_id] += call_amt
        # Update total pot size
        self.pot = sum(self.contributions.values())


# --------------------------------------------------
# This class controls replay analysis and decision
# comparison for the hero player.
# --------------------------------------------------
class ReplayManager:
    def __init__(self, game_id, hero_id, db_path= 'game_clean/database/poker_replays.db'):

        """
                this initialises the replay system for a specific game.
        """


        self.game_id = game_id
        self.hero_id = hero_id


        self.db = DatabaseManager()
        self.profile_manager = PlayerProfileManager()
        # load the advanced ML-powered bot for optimal decision-making
        self.advanced_bot = AdvancedBot(name="ReplayAdvanced",ml_manager= MLModelManager())

        # intermediate bot for multi-opponent situations
        self.intermediate_bot = IntermediateBot("ReplayIntermediate") # need to pass in chips here
        # call Load replay to get the data from database
        self.load_replay()

    def load_replay(self):

        """
        Loads all replay data for the game from the database.
        """
        data = self.db.get_replay(self.game_id)

        # Player list and action history
        self.players = data['players']
        self.actions = data['actions']

        # Map action IDs to their index in the replay
        self.action_id_to_index = {
            action[0]: idx
            for idx, action in enumerate(self.actions)
        }
        # Map each stage to its community cards
        self.community_by_stage = {
            row[2]: row[3].split(",")
            for row in data["community_cards"]
        }
        # Aggregate opponent statistics
        self.avg_opponent_profile = self.aggregate_opponent_profiles()

    def get_bot(self, state):
        """
        Chooses which bot to use depending on the number of opponents.
        """
        # goes through the state.players objects to get the total length if they are not the hero and not folded meaning other opponents in the game
        num_opponents = len([
            p for p in state.players
            if p[0] != self.hero_id and p[0] not in state.folded
        ])
        # Heads-up means using the advanced bot
        if num_opponents == 1:
            return self.advanced_bot, "advanced"

        # Multi-way means using the intermediate bot
        else:
            return self.intermediate_bot, "intermediate"

    def rebuild_state_until(self, end_index):
        """
        Rebuilds the game state up to a specific action index.
        """
        # gets the template state using the players and the board cards which we start to modify
        # by logging actions to it
        state = GameState(self.players, self.community_by_stage)

        # uses the action index as the end index and replays up to it by applying the actions
        for i in range(end_index):
            state.apply_action(self.actions[i])
        return state # returns the updated state

    def analyse_hero_action(self, action_id):

        """
        Analyses one specific hero decision in the replay.
        """
        # an error if by any chance there is an action id not in the list from the beginning to the selected action index
        if action_id not in self.action_id_to_index:
            return None

        # this gets the action in between and unpacks it into the info needed to check it before rebuilding it
        action_index = self.action_id_to_index[action_id]
        action = self.actions[action_index]

        # unpacks the info of that action
        _, _, player_id, stage, action_type, amount, _ = action

        # this checks if any action in between the beginning and the action index doesnt belong to the hero
        # in which case we dont care and return
        # none as we dont care and we dont want to compute anything for it
        if player_id != self.hero_id or action_type == "deal_hole_cards":
            return None

        # applies the rebuild state using the action index
        state = self.rebuild_state_until(action_index)

        # uses a method to query the db to get the hole cards at that index
        hero_cards = self.db.get_player_hole_cards(self.game_id, self.hero_id)
        if not hero_cards:
            return None

        # call the compute optimal action with the current rebuilt game state to get the action, bet,
        # percentage of winning and the reason
        action, bet, equity, explanation = self.compute_optimal_action(state)

        # store the snapshot for frontend usage
        snapshot = self.serialise_state(state)

        # returns a dictionary of all the info to teach the user
        return {
            "actual": (action_type, amount),
            "optimal": (action, bet),
            "equity": equity,
            "explanation": explanation,
            "state": snapshot,
        }

    def get_state_at_action(self, action_id: int):
        """
        Reconstruct the full table state at a specific action.
        Must include:
        - players: name, chips, current_bet, last_action, hole_cards
        - pot
        - community_cards
        - stage
        """
        action = next((a for a in self.actions if a[0] == action_id), None)
        if not action:
            return None
        # action[4] = state snapshot (saved when action was made)
        return action[4]
    #may need to tweak if it is against multiple opponents by using intermediate bot instead monte carlo method
    def compute_optimal_action(self, state):

        """
        Determines the optimal action for the hero at the current game state.
        This method compares the hero's real decision against an AI-recommended one.
        """

        # this retrieves hero's hole cards from the database
        hero_cards = self.db.get_player_hole_cards(self.game_id, self.hero_id)

        # Chooses which bot to use (advanced or intermediate)
        bot, bot_type = self.get_bot(state)

        # Amount required for hero to call the current bet
        to_call = state.current_bet - state.contributions[self.hero_id]

        # -------------------------
        # ADVANCED BOT PATH
        # -------------------------
        if bot_type == "advanced":
            # add full game context into the advanced bot by defining the state
            bot.set_state(
                hole_cards=hero_cards,
                community_cards=state.board,
                pot=state.pot,
                bet_to_call=to_call,
                position=self.get_player_position(self.hero_id),
                opponent_profile=self.avg_opponent_profile,
                stack=state.stacks[self.hero_id]
            )

            # Ask the bot to make a decision
            action, bet = bot.make_decision()
            #print(action, bet)

            # Estimate win equity and likely winning hand types
            top_hand_types, equity = bot.estimate_equity()

            # Determine min_raise according to BetManager logic
            big_blind = 10  # or fetch dynamically
            if state.stage == 'preflop':
                min_raise = big_blind
            else:
                min_raise = max(state.last_raise_size, big_blind)



            # Correct the bot's raise if below min_raise
            if action in ("raise", "bet"):
                big_blind = 20
                if state.stage == 'preflop':
                    min_raise = big_blind
                else:
                    min_raise = max(state.last_raise_size, big_blind)

                # If the bot gives a raise amount, add to call
                if bet < to_call + min_raise:
                    # Make sure raise meets minimum
                    bet = to_call + min_raise
                else:
                    # Use bot’s desired total
                    bet = bet


        # -------------------------
        # INTERMEDIATE BOT PATH
        # -------------------------
        else:
            # add dynamic chips
            bot.chips = state.stacks[self.hero_id]
            bot.community_cards = state.board

            # Construct  game state for intermediate bot
            game_state = {
                "stage": state.stage,
                "pot": state.pot,
                "to_call": to_call,
                "min_raise": max(1, state.current_bet),
                "big_blind": state.current_bet or 1
            }

            # Dummy player abstraction to match bot interface due to how the intermediate bot file was set up
            class DummyPlayer:
                def __init__(self, hole_cards, chips):
                    self.hole_cards = hole_cards
                    self.chips = chips

            hero = DummyPlayer(hero_cards, bot.chips)
            # Request action from intermediate bot
            result = bot.get_action(game_state, hero)
            # Handle multiple return formats depending on the state if the game
            if isinstance(result, tuple):
                action, bet = result
                equity = None
            else:
                action = result["type"]
                bet = result.get("amount", 0)
                equity = result.get("equity", None)
                top_hand_types = result.get("top_hand_types", None)

        # Generate the human-readable explanation for the decision
        explanation = self.generate_explanation(action, equity or 0, state, top_hand_types)

        return action, bet, equity, explanation

    def aggregate_opponent_profiles(self):
        """
        Aggregates opponent statistics into a single average profile.
        Used by the advanced bot to model opponent behaviour.
        """
        profiles = []

        # iterate through each player who is not the hero and use their player id/ PID and query the db to get their profile
        for p in self.players:
            pid = p[0]
            if pid != self.hero_id:
                profiles.append(self.profile_manager.get_profile(pid))
        # Default values if no profiles exist
        if not profiles:
            return {"vpip": 0.25, "pfr": 0.15, "aggression": 0.3}
        # Average VPIP, PFR, aggression
        agg = {"vpip": 0, "pfr": 0, "aggression": 0}
        for p in profiles:
            agg["vpip"] += p.get("vpip", 0.25)
            agg["pfr"] += p.get("pfr", 0.15)
            agg["aggression"] += p.get("aggression", 0.3)

        return {k: v / len(profiles) for k, v in agg.items()}

    def get_player_position(self, player_id):
        """
        Returns the seat position of a player.
        Used by the advanced bot to model positional advantage.
        """
        for p in self.players:
            if p[0] == player_id:
                return p[2]  # seat_position
        return 0
    '''
    def generate_explanation(self, action, equity, state, top_hand_types= None):
        """
        Converts numerical analysis into readable coaching feedback.
        """
        reasons = []

        to_call = state.current_bet - state.contributions[self.hero_id]
        if to_call == 0:
            pot_odds = 0
        else:
            pot_odds = to_call / max(state.pot + to_call, 1)

        if equity > pot_odds + 0.15:
            # equity exceeds pot odds by significant amounts
            reasons.append(f"Equity ({equity:.2f}) significantly exceeds pot odds ({pot_odds:.2f})")

        if action in ("bet", "raise"):
            if equity > 0.65:
                reasons.append("Maximising value with strong range advantage")
            else:
                # this indicates a bluff because equity isnt high but we are choosing to bet or raise meaning a potential bludd
                reasons.append("Applying pressure with semi-bluff")
        elif action == "call" and equity < pot_odds:
            # equity is less than pot odds so it is a tight call
            reasons.append("Marginal call due to implied odds")
        elif action == "fold":
            reasons.append("Negative expected value given opponent range")

        # Add card-based hints
        # what this does is it uses hand hints by using all the simulations for the bot and storing the most common hands which are returned as the top 3
        # tells you to help you understand that given the cards these are what you should have been considering when you made your move
        hero_cards = self.db.get_player_hole_cards(self.game_id, self.hero_id)
        hand_hints = self.hint_potential_hands(hero_cards, state.board)
        if hand_hints:
            reasons.append("Hand hints: " + hand_hints)
        if top_hand_types:
            if len(top_hand_types) == 1:
                reasons.append(
                    f"Primary winning hand: {top_hand_types[0]}"
                )
            else:
                formatted = ", ".join(top_hand_types[:3])
                reasons.append(
                    f"Most likely winning hands: {formatted}"
                )

        return "; ".join(reasons)

    '''
    def generate_explanation(self, action, equity, state, top_hand_types=None):
        """
        Converts numerical analysis into readable, friendly coaching feedback.
        Provides personalised explanations for the hero's decision.
        """
        reasons = []
        to_call = state.current_bet - state.contributions[self.hero_id]
        pot_total = state.pot + to_call if to_call > 0 else state.pot
        pot_odds = to_call / max(pot_total, 1)

        # Explain equity vs pot odds
        reasons.append(
            f"Your hand has an estimated win chance of {equity:.0%}, "
            f"compared to pot odds of {pot_odds:.0%}."
        )

        # Action-specific guidance
        if action in ("bet", "raise"):
            if equity > 0.65:
                reasons.append("This is a strong value bet — you have a good chance to win the pot.")
            elif equity > 0.4:
                reasons.append(
                    "Your hand is decent — applying pressure here might force weaker hands to fold (semi-bluff)."
                )
            else:
                reasons.append(
                    "Low equity — this is likely a bluff to steal the pot or set up future moves."
                )
        elif action == "call":
            if equity > pot_odds:
                reasons.append(
                    "Calling is profitable here — your hand is strong enough compared to the pot odds."
                )
            else:
                reasons.append(
                    "Calling is risky — your hand is weaker than the pot odds suggest, but could improve on later streets."
                )
        elif action == "fold":
            reasons.append(
                "Folding is safest — your hand likely cannot win against opponents’ ranges."
            )

        # Add hand hints
        hero_cards = self.db.get_player_hole_cards(self.game_id, self.hero_id)
        hand_hints = self.hint_potential_hands(hero_cards, state.board)
        if hand_hints:
            reasons.append(f"With your cards: {hand_hints}")

        # Top hand types or likely winning hands
        if top_hand_types:
            if len(top_hand_types) == 1:
                reasons.append(f"Most likely winning hand: {top_hand_types[0]}")
            else:
                formatted = ", ".join(top_hand_types[:3])
                reasons.append(f"Top hands to consider: {formatted}")

        # Final personalized advice
        advice = "; ".join(reasons)
        # Add some more human touch
        advice = advice.replace("Your hand", "You").replace("Calling is profitable", "You can call").replace(
            "Folding is safest", "You should fold")

        return advice

    def parse_card(self, card: str):
        """
        Returns (rank, suit) from card string.
        Examples:
            '10H' -> ('10', 'H')
            'Ah'  -> ('A', 'h')
        """
        rank = card[:-1]  # everything except last character
        suit = card[-1]  # last character
        return rank, suit

    def hint_potential_hands(self, hero_cards, board):
        """
        Returns hints about hero's potential hands
        """
        RANK_MAP = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'T': 10,
                    'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        hints = []

        ranks = []
        suits = []

        for c in hero_cards:
            r, s = self.parse_card(c)
            ranks.append(r)
            suits.append(s)

        # Pair
        if ranks[0] == ranks[1]:
            hints.append(f"Pair of {ranks[0]}s — potential trips or full house")
        # Connected cards
        elif abs(RANK_MAP[ranks[0]] - RANK_MAP[ranks[1]]) <= 2:
            hints.append("Connected cards — possible straight draws")
        # Suited
        if suits[0] == suits[1]:
            hints.append("Suited cards — potential flush draw")

        # Board-based draws
        board_ranks = []
        board_suits = []
        for c in board:
            r, s = self.parse_card(c)
            board_ranks.append(r)
            board_suits.append(s)

        for s in set(suits):
            if board_suits.count(s) >= 2:
                hints.append("Flush draw possible on board")

        return "; ".join(hints)

    def get_replay_json(self):
        """
        Returns replay data in JSON-ready format for frontend.
        Each action includes stage, action id, hero action, optimal action,
        equity, explanation, and a snapshot of the game state.
        """
        replay_list = []

        for action in self.actions:
            # unpacks actions to handle any exceptions we dont want to return
            # Underscores are used for values not needed in this method
            _, _, player_id, stage, action_type, amount, action_id = action

            # ignore the dealing hole cards action
            if action_type == "deal_hole_cards":
                continue

            if player_id == self.hero_id:
                # Analyse the hero's action against the optimal bot decision
                analysis = self.analyse_hero_action(action_id)

                # If analysis data exists, extract optimal decision details
                if analysis:
                    optimal_action, optimal_bet = analysis["optimal"]
                    equity = analysis["equity"]
                    reason = analysis["explanation"]
                    snapshot = analysis['state']
                else:
                    # Fallback values if analysis failed or was unavailable
                    optimal_action, optimal_bet = None, None
                    equity, reason = None, ""
                    snapshot = None
            else:
                # Non-hero actions do not receive analysis data
                optimal_action, optimal_bet, equity, reason = None, None, None, ""
            # Append structured replay data for this action
            replay_list.append({
                "stage": stage,   # Game stage (preflop, flop, etc.)
                "id": action_id,  # Unique action identifier
                "player": player_id, # Player who performed the action
                "hero": action_type if player_id == self.hero_id else None,
                "amount": amount if player_id == self.hero_id else None,
                "optimal": optimal_action, # Bot-recommended action
                "optAmount": optimal_bet,  # Bot-recommended bet amount
                "equity": equity, # Estimated win probability
                "reason": reason, # Human-readable explanation
                "state": snapshot, # Game state snapshot
            })

        return replay_list

    def serialise_state(self, state):
        """
        Creates a serialised snapshot of the current game state.
        This is used to reconstruct hands visually in the replay system.
        """
        hero_cards = self.db.get_player_hole_cards(self.game_id, self.hero_id)

        # List to store serialised player data
        players_snapshot = []
        for p in self.players:
            # Extract player ID and seat position
            player_id = p[0]
            seat_position = p[2]

            # Build a dictionary representing the player's current state
            player_data = {
                "id": player_id,    # Unique player ID
                "position": seat_position,  # Table position
                "stack": state.stacks.get(player_id, 0),   # Remaining chips
                "contributed": state.contributions.get(player_id, 0), # Chips in pot
                "folded": player_id in state.folded,  # Fold status
                "is_hero": player_id == self.hero_id # Hero flag

            }
            # Include hole cards only for the hero to prevent information leakage as in real games
            # you should never know opponent cards
            # so in optimal actions you shouldnt know
            if player_id == self.hero_id:
                player_data["hole_cards"] = hero_cards
            else:
                player_data["hole_cards"] = None
            players_snapshot.append(player_data)

        # Construct the full game state snapshot
        snapshot = {
            "stage": state.stage,     # Current betting round
            "pot": state.pot,         # Total pot size
            "board": state.board,     # Community cards
            "current_bet": state.current_bet, # Current bet level
            "players": players_snapshot # All player states
        }
        return snapshot

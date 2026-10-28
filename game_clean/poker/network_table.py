# Import the Deck class which manages card creation, shuffling, and drawing
from game_clean.poker.deck import Deck

# Import the BetManager which controls betting logic and turn order
from game_clean.poker.betting import BetManager

# Import the PotManager which handles main pots and side pots
from game_clean.poker.potmanager import PotManager

# Import the HandEvaluator used to score poker hands at showdown
from game_clean.poker.hand_evaluator import HandEvaluator

# Used to timestamp actions for logging and ML training
from datetime import datetime

# Asyncio is used to manage asynchronous networking and turn handling
import asyncio

# Import intermediate-level poker bot (Monte Carlo / heuristics)
from game_clean.poker.intermediate_bot import IntermediateBot


# Import advanced bot which uses machine learning and opponent profiling
from game_clean.poker.advanced_bot_v2 import AdvancedBot

# Manages long-term player statistics and behavioural profiles
from game_clean.managers.PlayerProfileManager import PlayerProfileManager

# Manages machine learning models for adaptive bot behaviour
from game_clean.ml.ml_model_manager import MLModelManager

# Handles all database reads/writes (games, actions, results)
from game_clean.managers.database_manager import DatabaseManager

# Used to generate unique table and game IDs
from uuid import uuid4

# NumPy is used for numerical arrays when preparing ML training data
import numpy as np
# handle all imports from all other files here


# Main class controlling a network-enabled poker table
# -------------------------------------------------------

class NetworkTable():
    def __init__(self, players, table_id = None, big_blind = 20, small_blind = 10, invalid_mode = 'soft', bot_level = 'beginner'):

        # Store all players seated at a table
        self.players= players

        # List of active players still active in the current hand
        self.active_players = []

        # Community cards shared by all players
        self.community_cards = []
        self.deck = Deck()
        self.pot = PotManager()
        self.hand_evaluator = HandEvaluator()
        self.betmanager = BetManager(self.pot)

        self.current_stage = None
        self.round_over  = False
        self.hand_over = False
        self.dealer_position = 0

        # Blind values/ Forced Bets
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.early_end  = True

        # Dictionary to store all the earnings
        self.winnings = {}

        self.current_player = None
        self.profile_manager = PlayerProfileManager()
        self.db_manager = DatabaseManager()

        self.host_player = players[0].name if players else None  # assign first player as host
        self.ready_to_start = False  # host confirmation flag
        self.table_id = table_id or str(uuid4())
        self.waiting_for_action = asyncio.Event() # state check to see which player we are waiting to get the action from
        self.pending_action = None  # {"player","action","amount":}
        self.bot_level = bot_level
        self.player_stats = {}
        self.hand_history = []
        self.total_hands_played = {p.name: 0 for p in self.players}
        self.ml_manager = MLModelManager()

    # HAND SETUP AND RESET
    # -------------------------------------------------------
    def reset_for_new_hand(self):
        # This resets a hand to default intial states before playing which includes resetting players, pot, betmanager, community cards, stages
        self.current_stage = None
        self.round_over = False
        self.hand_over = False
        self.community_cards = []
        self.active_players = []
        self.deck.reset_deck()
        self.pot.reset_for_new_hand()
        self.betmanager.reset()
        for p in self.players:
            p.reset_for_new_hand()
        self.active_players = [p for p in self.players if p.chips > 0] #intial set of players who are not bust
        self.winnings = {}
        self.early_end = True
        self.current_player = None
        self.hand_history = []

    def start_new_hand(self):
        # this is used to start a new hand by defning player startying stack, calling the methods needed to start a game like posting the blinds, deal intial hole cards, create the betmanager object and set the intial stage
        for p in self.players:
            p.starting_stack = p.chips
        self.reset_for_new_hand()
        self.dealer_position = (self.dealer_position + 1) % len(self.players)
        self.post_blinds()
        self.deal_hole_cards()
        self.current_stage = "preflop"
        self.start_new_round()

        # Log game start in database if not already logged
        if not hasattr(self, 'game_id'):
            self.game_id = self.db_manager.log_game_start(
                table_id=self.table_id,
                game_type="texas_holdem",
                starting_chips=1000,  # or configurable
                small_blind=self.small_blind,
                big_blind=self.big_blind,
                max_players=len(self.players)
            )
            # Log each player joining the game
            for seat, player in enumerate(self.players):
                self.db_manager.log_player_join(self.game_id, player.name, seat, player.chips)

        # Log hole cards
        for player in self.active_players:
            self.db_manager.log_player_action(
                self.game_id,
                player.name,
                "preflop",
                "deal_hole_cards",
                None
            )

            self.db_manager.log_hole_cards(self.game_id, player.name, player.hole_cards)

        return self.get_state()


    def start_new_round(self):
        # slightly different reset methgod this is a per round metod and so gets called 5 times in a full length hand if it goes through all the stages, here we want to kepp all the chips, all the pots and players as we have multiple hands in a round and we dont want to lose any of that
        for p in self.players:
            p.reset_for_new_round(self.current_stage)
        self.active_players = [p for p in self.players if not p.folded or not p.all_in]
        self.current_player = None
        self.betmanager.reset_for_new_round(self.active_players, self.current_stage, self.big_blind)


    def post_blinds(self):
        # this metod is used at the beginning of the preflop round because in the preflop we need to force some bets from the
        # first two players and so this is done here
        sb_pos = (self.dealer_position + 1) % len(self.players) # gets the position of the player who must force the small bet
        bb_pos = (self.dealer_position + 2) % len(self.players)# gets the position of the player who must force the large bet

        sb_player = self.players[sb_pos]
        bb_player = self.players[bb_pos]

        sb_amount = min(sb_player.chips, self.small_blind) #selects the amount heere just in case after a hand the chips are
        # less than the minmium reuired in which they go all in
        bb_amount = min(bb_player.chips, self.big_blind)


        self.pot.add_contribution(sb_player, sb_amount) #here we create the first main pot for the game addning it all in
        sb_player.chips -= sb_amount
        sb_player.current_bet = sb_amount # because we add the chips in we need to remove from player amount that they should have

        if sb_player.chips == 0:
            sb_player.all_in = True

        self.pot.add_contribution(bb_player, bb_amount)
        bb_player.chips -= bb_amount
        bb_player.current_bet = bb_amount
        if bb_player.chips == 0:
            bb_player.all_in = True

        self.betmanager.current_bet = self.big_blind
        #send some websocket messages here to identify the error or make it easier to see what it is doing
        print("Blinds posted successfully")
        msg_text = f"Blinds posted: {sb_player.name} -> {sb_player.current_bet}, " \
                   f"{bb_player.name} -> {bb_player.current_bet}"
        print(msg_text)


    def deal_hole_cards(self):
        # method to take the shuffled deck (list) and take the first 2 from top of array for each person
        for p in self.active_players:
            p.hole_cards += self.deck.draw_from_deck(2)

    # ---------------------
    # ROUND MANAGEMENT
    #-----------------------

    def advance_round(self):
        # method to track rounds so we have the correct stage before we pass it into the betmanager when we reset the betmanager
        if self.current_stage == None:
            self.current_stage = 'preflop'
        elif self.current_stage == 'preflop':
            self.current_stage = 'flop'
            self.community_cards += self.deck.draw_from_deck(3)
        elif self.current_stage == 'flop':
            self.current_stage = 'turn'
            self.community_cards += self.deck.draw_from_deck(1)
        elif self.current_stage == 'turn':
            self.community_cards += self.deck.draw_from_deck(1)
            self.current_stage = 'river'
        elif self.current_stage == 'river':
            self.current_stage = 'showdown'

        # log the community cards each round
        if hasattr(self, 'game_id') and self.current_stage in ['flop', 'turn', 'river']:
            self.db_manager.log_community_cards(
                self.game_id,
                self.current_stage,
                [str(c) for c in self.community_cards]
            )

    def is_hand_over(self):
        #checks if the current hand is over which is met on certain criteria

        active_players = [p for p in self.players if not p.folded]
        # only one player remaining so they win
        if len(active_players) == 1:
            return True
        # all the players have gone all in so we default to showdown
        if all(p.all_in for p in active_players):
            return True

        return False



    def check_for_one_player(self):
        return len([p for p in self.players if not p.folded]) == 1

    def is_hand_in_progress(self):
        # method to use in a loop to ensure the game keeps going until the ending conditions are met
        return self.current_stage is not None and not self.hand_over

    # ---------------------
    # SHOWDOWN AND WINNINGS
    #---------------------------

    def showdown(self):
        #this is the method useed to get the showdown functionality
        active_players = [p for p in self.players if not p.folded]

        # Finish early we draw however board cards we still need
        if len(self.community_cards) < 5:
            remaining = 5 - len(self.community_cards)
            self.community_cards += self.deck.draw_from_deck(remaining)
        for p in active_players: #gets all active players reamming in the showdown and gets their hand score
            # from their hands using the hand evaluator
            p.best_hand, p.hand_score = self.hand_evaluator.evaluate_hand(p, self.community_cards)
        ranked_players = sorted(active_players, key=lambda p: p.hand_score, reverse=True) # use the sorted function to rank hands
        # with best being first so easier for when distribute the winnings

        winnings = self.pot.distribute_showdown(ranked_players)

        for p in self.players:#update the players chips based on how much they have won
            if p.name in winnings:
                p.chips += winnings[p.name]
        return winnings

    def finalise_hand_rewards(self):
        # at the end of a hand if only one person is left they get all the winnings from the main pot and any side pots they are eligible for
        showdown_players = []

        if self.check_for_one_player():
            winner = [p for p in self.players if not p.folded][0]
            winnings = self.pot.award_all_to(winner)
        else:
            # Case 2: showdown
            winnings = self.showdown()
        for p in self.players:
            self.total_hands_played.setdefault(p.name, 0)
            self.total_hands_played[p.name] += 1

            # update profile hands played
            self.profile_manager.increment_hands_played(p.name)

            # Log results to database if game_id exists
        if hasattr(self, 'game_id'):
            player_results = {p.name: p.chips for p in self.players}
            self.db_manager.log_game_ended(self.game_id, player_results)

        return winnings
    # -----------
    # BOT ACTION
    # -----------
    def choose_bot_action(self, player):
        """
        this is the simple/ beginner version for the heuristic bot policy It uses some rule based criteria to make its decision:
        - Fold if too expensive
        - Call most of the time if affordable.
        - Occasionally raise if they have chips.
        """
        import random
        to_call = self.betmanager.current_bet - player.current_bet


        # If there's something to call
        if to_call > 0:
            if player.chips < to_call:
                action= "fold"
                amount = None  # can't afford to call
            r = random.random()
            if r < 0.1:  # 10% fold even if we can afford to call
                action= "fold"
                amount = None
            elif r < 0.8:  # 70% call
                action = "call"
                amount = to_call
            else:
                # 20% raise if they have enough chips
                raise_amount = min(player.chips, to_call + self.big_blind)
                action= "raise"
                amount = raise_amount

        # If there's nothing to call (meaning free action)
        else:
            r = random.random()
            if r < 0.7:
                action = "check"
                amount = None
            else:
                # occasional raise
                raise_amount = min(player.chips, self.big_blind)
                action = "raise"
                amount = raise_amount

        return action, amount

    def process_intermediate(self, player):
        # ADD A RANDOM MESSAGE WHICH WE CAN SEND TO THE FRONTEND TO USE FOR RANDOM DELAY

        # this is method to handle the bot logic for any bots defined as intermeidate bots, this uses the monte carlo technique with pot odds, equity and occasional bluffing
        bot = IntermediateBot(player.name, player.chips, self.community_cards)

        current_round_contributions = sum(p.current_bet for p in self.active_players)
        total_pot = self.pot.total + current_round_contributions # get all the features needed for the bot to make a decision



        to_call = self.betmanager.current_bet - player.current_bet
        call_amount = min(to_call, player.chips) # used to ensure the bot's action are valid as may want to call without enough to call so we need to add a check here


        game_state = {
            "stage": self.current_stage,
            "position": None,
            "facing_raise": player.facing_raise,
            "big_blind": self.big_blind,
            "min_raise": self.betmanager.min_raise,
            "to_call": call_amount,
            "pot": total_pot
        } # this is the dictionary of main info the bot will use in making decision

        action_dict = bot.get_action(game_state, player)

        # Unpack values here
        action = action_dict['type']
        amount = action_dict['amount']
        equity = action_dict['equity']
        pot_odds = action_dict['pot_odds']
        return action, amount, equity

    def process_advanced(self, player):
        #this is the advanced bot action method, uses the intermeidate bot setup bot also uses ml to predict the best action and best bet size to use
        bot = AdvancedBot(player.name, ml_manager=self.ml_manager)


        # get all the info needed for the bot
        current_round_contributions = sum(p.current_bet for p in self.active_players)
        total_pot = self.pot.total + current_round_contributions

        to_call = self.betmanager.current_bet - player.current_bet
        stack = player.chips
        opponent_profile = self.profile_manager.get_average_profile(exclude=player.name)


        bot.set_state(player.hole_cards, self.community_cards, opponent_profile, total_pot, to_call, stack, position= None)
        if self.current_stage == 'preflop':
            action, amount = self.choose_bot_action(player)
        else:
            action, amount = bot.make_decision()
        return action, amount



    # ---------------------------
    # NETWORKING AND ASYNC
    # ---------------------------
    async def play_hand(self, broadcast_callback):
        # MAIN CONTROL GAME LOOP
        # Any broadcast callback means sending a message to the frontend
        while not self.is_hand_over(): # Keeps going until the game is over
            next_player = self.betmanager.next_player()

            if not next_player:
                # CHECK HERE TO SEE IF GAME ENDS EARLY
                if self.betmanager.check_round_over():
                    msg_text = f"Round ended. Advancing stage from {self.current_stage}..."
                    print(msg_text)


                    await self.broadcast_state(broadcast_callback, last_action=msg_text)
                    self.advance_round()
                    if self.current_stage == "showdown": # final round finished so loop should end here
                        break
                    else:
                        self.start_new_round()
                        msg_text = f"New round started in stage {self.current_stage}"
                        await self.broadcast_state(broadcast_callback, last_action=msg_text)
                    continue
                else:
                    continue
            # Check just in case
            if next_player.folded or next_player.all_in:
                continue

            # HUMAN PLAYER
            self.current_player = next_player
            if not getattr(next_player, "is_bot", False):
                while True: # loop used to ensure actions from human input are valid
                    msg_text = f"Waiting for action from {next_player.name}..."
                    print(msg_text)
                    await self.broadcast_state(broadcast_callback, last_action=msg_text)

                    await broadcast_callback({
                        "type": "your_turn",
                        "player": next_player.name,
                        "state": self.get_state_for_player(next_player.name)
                    })
                    await self.waiting_for_action.wait()

                    print(f" Action received signal for {next_player.name}")


                    self.waiting_for_action.clear()
                    data = self.pending_action # input from the user is the data variable
                    self.pending_action = None
                    if data is None:
                        msg_text = "No action data found — possible disconnect or timing issue."
                        print(msg_text)
                        await self.broadcast_state(broadcast_callback, last_action=msg_text)
                        continue

                    if data["player"] != next_player.name: # reject action from invalid player turns
                        msg_text = f"Action ignored: from {data['player']} but expected {next_player.name}"
                        print(msg_text)
                        await self.broadcast_state(broadcast_callback, last_action=msg_text)
                        continue

                    # Unpack action and validate
                    action, amount = data["action"], data["amount"]
                    print(f" Validating action '{action}' (amount={amount}) from {next_player.name}")

                    if self.validate_player_action(next_player, action, amount):
                        print(f" Applying action: {next_player.name} -> {action} {amount}")
                        self.betmanager.apply_action(next_player, action, amount)
                        self.record_action(next_player, action, amount)
                        await self.broadcast_state(broadcast_callback, last_action=msg_text)

                        break
                    else:
                        print("INVALID ACTION!!!!!!!!!!!!!!!!!!!!!!!!!")
                        msg_text = f"Invalid action by {next_player.name}: {action} {amount}"
                        print(msg_text)
                        await broadcast_callback({
                            "type": "invalid_action",
                            "player": next_player.name,
                            "state": self.get_state_for_player(next_player.name),
                            "last_action": msg_text
                        })


            # BOT PLAYER
            else:
                import random
                thinking_msg = f"{next_player.name} is thinking..."
                print(thinking_msg)
                msg_text = thinking_msg
                await self.broadcast_state(broadcast_callback, last_action=msg_text)

                delay = random.uniform(1.0, 3.0)
                await asyncio.sleep(delay)

                # choose the correct level
                if next_player.bot_level == 'beginner':
                    action, amount = self.choose_bot_action(next_player)
                elif next_player.bot_level == 'intermediate':
                    action, amount, equity = self.process_intermediate(next_player)
                elif next_player.bot_level == 'adaptive':
                    action, amount = self.process_advanced(next_player)

                new_amount = self.betmanager.apply_action(next_player, action, amount)
                if new_amount is not None:
                    amount = new_amount

                # Ensure action is being logged for training
                self.record_action(next_player, action, amount, equity =None)
                msg_text = f"{next_player.name} -> {action} {amount}"
                print(f"next_player: {next_player.name} -> {action} {amount}")
                print(msg_text)
                await self.broadcast_state(broadcast_callback, last_action=msg_text)
                msg_text = f"{next_player.name} successfully {action}"
                await self.broadcast_state(broadcast_callback, last_action=msg_text)

            await self.broadcast_state(broadcast_callback, last_action=msg_text)

        # HAND OVER

        self.early_end = self.check_for_one_player()
        self.betmanager.check_round_over(self.early_end)
        self.winnings = self.finalise_hand_rewards()
        print(self.winnings)
        for player_name, amount in self.winnings.items():
            player_obj = next((p for p in self.players if p.name == player_name), None)
            if player_obj:
                player_obj.chips += amount  #  update chips
        msg_text = f"Hand over. Winnings: {self.winnings}"
        await self.broadcast_state(broadcast_callback, last_action=msg_text)

        # Ensure all player stats and equity across hand are fresh and updated
        self.update_player_statistics()
        self.update_profile_equity_results()

        for player in self.players:
            if getattr(player, "is_bot", False):
                continue  # train bots separately later

            X, y_actions, y_bets = self.extract_training_data_for_player(player.name)

            if len(X) >= 30:  # avoid tiny noisy datasets
                # Train when we have enough data for a player
                print("We are training")
                self.ml_manager.train_player_model(
                    player.name,
                    X,
                    y_actions,
                    y_bets
                )



        self.hand_over = True
        print("We are doing the broadcast callback")
        await broadcast_callback({
            "type": "hand_over",
            "state": self.get_state(),
            "winnings": self.winnings
        })
        print("broadcast callback finished")

        if hasattr(self, 'game_id'):
            player_results = {p.name: p.chips for p in self.players}
            self.db_manager.log_game_ended(self.game_id, player_results)

    async def broadcast_state(self, broadcast_callback, last_action = None):
        """
            Send a personalised state update to each player.
            Each player sees their own hole cards while
            opponents' cards remain hidden.

            last_action: optional text to include for each player
            """
        for player in self.players:
            message = {
                "type": "state_update",
                "state": self.get_state_for_player(player.name)
            }
            if last_action:
                message["last_action"] = last_action
            await broadcast_callback(message)

    async def receive_player_action(self, player_name, action, amount=None):
        """Called by WebSocket when a player submits a move."""


        # Regular player action
        self.pending_action = {"player": player_name, "action": action, "amount": amount}
        self.waiting_for_action.set()

    # ------------
    #STATE FOR CLIENT
    # -------------

    def get_state(self):

        # Create a global state that is baseline and generic for all players
        state = {
            "stage": self.current_stage,
            "community_cards": [str(c) for c in self.community_cards],
            "pot": self.pot.total,
            "current_bet": self.betmanager.current_bet,
            "players": []
        }

        for p in self.players:
            state["players"].append({
                "name": p.name,
                "chips": p.chips,
                "current_bet": p.current_bet,
                "folded": p.folded,
                "all_in": p.all_in,
                "hole_cards":  ["back", "back"]
            })

        return state

    def get_state_for_player(self, viewer_name):
        # Purpose is to fill in the generic state with the player hidden info
        state = self.get_state()  # get the generic state first
        state["players"] = []
        for p in self.players:
            if p.name == viewer_name:
                cards = p.hole_cards  # show real cards
            else:
                cards = ["back", "back"]  # hide opponent cards
            state["players"].append({
                "name": p.name,
                "chips": p.chips,
                "current_bet": p.current_bet,
                "folded": p.folded,
                "all_in": p.all_in,
                "hole_cards": cards
            })
        return state

    def record_action(self, player, action, amount=None, equity = None):
        # Calculate the derived metrics needed for the opponent adaptive modelling
        board_wetness = self.calculate_board_wetness()
        entry = {
            "player": player.name,
            "action": action,
            "amount": amount,
            "phase": self.current_stage,
            "pot": self.pot.total,
            "to_call": self.betmanager.current_bet - player.current_bet,
            "stack": player.chips,
            "equity": equity,
            "showdown_participation": False,
            "timestamp": datetime.now()
        }
        self.hand_history.append(entry)
        profile = self.profile_manager.get_profile(player.name)
        # Log the action and the corresponding info
        self.profile_manager.log_action(
            name=player.name,
            stage=self.current_stage,
            vpip=profile["vpip"],
            pfr=profile["pfr"],
            aggression=profile["aggression"],
            board_wetness=board_wetness,
            pot_size=self.pot.total,
            to_call=entry["to_call"],
            stack_size=player.chips,
            equity=equity,
            action=action,
            result="pending"
        )

        if hasattr(self, 'game_id'):
            self.db_manager.log_player_action(
                self.game_id,
                player.name,
                self.current_stage,
                action,
                amount
            )
    def update_player_statistics(self):
        for player in self.players:
            name = player.name
            actions = [a for a in self.hand_history if a["player"] == name]

            if not actions:
                continue

            vpip = any(
                a["action"] in ["call", "raise"] and a["phase"] == "preflop"
                for a in actions
            )

            pfr = any(
                a["action"] == "raise" and a["phase"] == "preflop"
                for a in actions
            )

            aggressive_actions = sum(
                1 for a in actions if a["action"] in ["raise", "bet"]
            )
            passive_actions = sum(
                1 for a in actions if a["action"] == "call"
            )

            aggression = aggressive_actions / max(1, passive_actions)

            avg_bet_size = sum(
                a["amount"] for a in actions if a["amount"]
            ) / max(1, len(actions))

            stats = {
                "vpip": int(vpip),
                "pfr": int(pfr),
                "aggression": aggression,
                "avg_bet_size": avg_bet_size
            }

            self.profile_manager.update_profile(name, **stats)

    def calculate_stats(self, player_name):
        # Use the equations to get the required stats
        player_actions = [a for a in self.hand_history if a["player"] == player_name]

        total_hands = self.total_hands_played.get(player_name, 1)
        vpip = sum(1 for a in player_actions if a["action"] in ["call", "raise", "bet"]) / total_hands
        pfr = sum(1 for a in player_actions if a["action"] == "raise") / total_hands
        aggression = (sum(1 for a in player_actions if a["action"] in ["raise", "bet"]) /
                      max(1, sum(1 for a in player_actions if a["action"] == "call")))

        return {"vpip": round(vpip, 2), "pfr": round(pfr, 2), "aggression": round(aggression, 2)}

    def validate_player_action(self, player, action, amount = None):
        """
        Validate the bot's action using BetManager's helper functions.
        """


        valid_actions = ["fold", "check", "call", "raise"]
        if action not in valid_actions:
            return False
        if action == "fold":
            return True
        if action == "check":
            return self.betmanager.can_check(player)
        if action == "call":
            return self.betmanager.can_call(player)
        if action == "raise":
            return self.betmanager.can_raise(player) and amount is not None
        return False

    def calculate_board_wetness(self):
        """
            Calculates a simple board wetness metric:
            - Higher if there are connected cards or multiple suits (possible straights/flushes)
            - Returns a float between 0 (dry) and 1 (very wet)
            """
        if not self.community_cards:
            return 0.0

            # Extract ranks and suits
        ranks = []
        suits = []
        for c in self.community_cards:
            rank = c[:-1]  # all except last character
            suit = c[-1]  # last character
            ranks.append(rank)
            suits.append(suit)

        # Convert ranks to numeric values
        rank_order = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6,
                      '7': 7, '8': 8, '9': 9, '10': 10,
                      'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        rank_values = sorted([rank_order[r] for r in ranks])

        # 1. Suitedness factor
        suit_counts = {s: suits.count(s) for s in set(suits)}
        max_suit_count = max(suit_counts.values())
        suited_factor = min(1.0, (max_suit_count - 1) / (len(self.community_cards) - 1))

        # 2. Connectedness factor (straight potential)
        connected_pairs = 0
        for i in range(len(rank_values) - 1):
            if rank_values[i + 1] - rank_values[i] <= 4:  # connected within 4
                connected_pairs += 1
        connected_factor = connected_pairs / max(1, len(rank_values) - 1)

        # 3. Combine factors into a wetness score
        wetness = (suited_factor + connected_factor) / 2
        return round(wetness, 2)

    def extract_training_data_for_player(self, player_name):
        X = []
        y_actions = []
        y_bets = []

        action_map = {"fold": 0, "call": 1, "raise": 2}

        profile = self.profile_manager.get_profile(player_name)

        for entry in self.hand_history:
            if entry["player"] != player_name:
                continue

            if entry["equity"] is None:  # skip actions with null equity
                continue
            if entry["action"] not in action_map:
                continue
            features = [
                entry["equity"],
                entry["pot"],
                entry["to_call"],
                entry["stack"],
                profile["vpip"],
                profile["pfr"],
                profile["aggression"],
                self.calculate_board_wetness()
            ]

            X.append(features)
            y_actions.append(action_map[entry["action"]])
            y_bets.append(entry["amount"] or 0.0)

        return np.array(X), np.array(y_actions), np.array(y_bets)

    def update_profile_equity_results(self):
        showdown_players  = [p for p in self.players if not p.folded or p.all_in]

        for entry in self.hand_history:
            entry["showdown_participation"] = entry["player"] in showdown_players and self.current_stage == "showdown"
            self.profile_manager.update_action_result(
                name=entry["player"],
                stage=entry["phase"],
                action=entry["action"],
                equity=entry["equity"],
                result="complete",
                showdown_participation = entry.get("showdown_participation", False)  # NEW

            )

        # Update showdown frequency for all players at the end of the hand
        for player in self.players:
            freq = self.profile_manager.calculate_showdown_frequency(player.name)
            profile = self.profile_manager.get_profile(player.name)
            profile["showdown_freq"] = freq  # overwrite directly
            self.profile_manager.update_profile(player.name, showdown_frequency=freq)

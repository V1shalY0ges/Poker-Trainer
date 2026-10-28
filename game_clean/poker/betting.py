# COMMENTS ARE DONE

class BetManager:
    """
    Controls all betting logic for a single betting round
    Responsible for validating actions, tracking raises, enforcing minimum raises,
    managing turn order and triggering pot construction
    """
    def __init__(self, pot):
        # instance of the PotManager used to track chip contributions
        self.pot = pot

        # Players who are active (not folded or all-in) in the current betting round
        self.active_round_players = []

        # Circular/ Priority queue determining whose turn it is to act
        self.action_queue = []

        # Highest bet currently on the table
        self.current_bet = 0

        # Minimum legal raise size
        self.min_raise = 0

        # Stores the final bet amount from the previous betting round
        self.last_round_bet = 0

        # Tracks the size of the most recent raise
        self.last_raise_size = 0

    def reset(self):
        """
        Fully resets the betting manager
        Used when starting a new hand
        """

        self.active_round_players = []
        self.action_queue = []
        self.current_bet = 0
        self.min_raise = 0
        self.last_round_bet = 0
        self.last_raise_size = 0

    def reset_for_new_round(self, players, stage, big_blind):
        """
        Resets betting state for a new betting round (preflop, flop, turn, river)
        """
        # Preflop has forced betting (big blind)
        if stage == 'preflop':
            self.min_raise = big_blind
            self.current_bet = big_blind
            self.last_raise_size = big_blind
        else:
            # Postflop betting starts at zero but the min raise is either between the the highest raise amount or the big blind
            self.min_raise = max(self.last_raise_size, big_blind)
            self.current_bet = 0

        # Track only players who can still act
        self.active_round_players = [p for p in players if not p.folded and not p.all_in]

        # Reset raise-facing flags
        for p in self.active_round_players:
            p.facing_raise = False

        # Initial action order includes all active players
        self.action_queue = self.active_round_players.copy() # Start of the round should be all the active round players

    # --------------------------------------------------
    # Action validation helper methods
    # --------------------------------------------------

    def can_call(self, player):
        # Player must not be folded or all-in
        if player.folded or player.all_in:
            return False

        # Call only valid if player has bet less than the current bet
        return player.current_bet < self.current_bet

    def can_check(self, player):
        # Player must not be folded or all-in
        if player.folded or player.all_in:
            return False

        # Check allowed only if player has matched the current bet
        return player.current_bet == self.current_bet

    def can_raise(self, player, raise_amount=None):
        # Player must not be folded or all-in
        if player.folded or player.all_in:
            return False

        # Default raise is minimum raise in case of errors in amount not being passed in
        if raise_amount is None:
            raise_amount = self.min_raise

        # Total chips required = call amount + raise amount
        total_needed = (self.current_bet - player.current_bet) + raise_amount
        return player.chips >= total_needed

    # --------------------------------------------------
    # Apply betting actions to game
    # --------------------------------------------------

    def apply_action(self, player, action, amount = None):
        """
        Applies a validated betting action for a player
        Updates chips, pot, betting state and action queue
        """

        print(f"{player.name}, action: {action}, amount: {amount}")
        # CALL
        # -----------
        if action == 'call':
            if self.can_call(player): # Checks if a player can call
                # Gets the call amount required
                to_call = self.current_bet - player.current_bet

                # Checks if the player has less chips than the call amount in which they go all in
                amount = min(to_call, player.chips)

                # Handle adding the bet and modifying the player bet, chips and pot
                player.current_bet += amount
                player.chips -= amount
                self.pot.add_contribution(player, amount)
                player.total_contributed += amount

                # Handles all in if player chips are 0
                if player.chips == 0:
                    player.all_in = True
                    print(f"{player.name} is now all-in with {amount} chips")

                # Debugging check
                print(f"{player.name} has successfully called ")

                # Remove the player from the queue as they have completed a valid action
                self.remove_player_from_queue(player)

        # CHECK
        # ------------------
        elif action == 'check':
            if self.can_check(player): # Check if a player is able to check

                # If they check they match the current bet which is typically 0
                player.current_bet = self.current_bet

                # Debugging check
                print(f"{player.name} has successfully checked ")

                # Remove the player from the queue as they have completed a valid action
                self.remove_player_from_queue(player)

        # FOLD
        # -------------------------------------
        elif action == 'fold':
            # No validation needed here as action can be done whenever
            player.folded = True # Set the flag to ensure they can't do anything for any other rounds

            # Debugging check
            print(f"{player.name} has successfully folded ")

            # Remove the player from the queue as they have completed a valid action
            self.remove_player_from_queue(player)

        # RAISE
        # --------------------------------
        elif action == 'raise':
            # Check in case no amount passed in set to default minimum raise
            if amount is None:
                amount = self.min_raise

            # Check if a player can raise
            if self.can_raise(player):

                # Get the call amount
                to_call = max(0, self.current_bet - player.current_bet)

                # Get the raise amount
                raise_amount = max(amount, self.min_raise)

                # Add together to get the total no. of chips they will contribute
                total_contribution = to_call + raise_amount


                # Handle all-in if player cannot cover full raise
                if total_contribution >= player.chips + player.current_bet:
                    total_contribution = player.chips

                    # Do not have enough chips to raise so goes all-in
                    player.all_in = True
                    print(f"{player.name} goes all-in with {player.chips} chips!")

                previous_bet = self.current_bet

                chips_to_pay = min(total_contribution, player.chips)
                player.chips -= chips_to_pay
                player.current_bet += chips_to_pay

                # Update the table bet
                self.current_bet = max(self.current_bet, player.current_bet)

                # Track contribution
                self.pot.add_contribution(player, chips_to_pay)
                player.total_contributed += chips_to_pay

                # Compute actual raise size
                actual_raise_size = self.current_bet - previous_bet

                # Full raise resets minimum raise
                if actual_raise_size >= self.last_raise_size:
                    self.last_raise_size = actual_raise_size
                    self.min_raise = self.last_raise_size
                    self.update_queue_on_raise(player)
                    print(f"Full raise detected. New min raise: {self.min_raise}")
                    actual_raise_size = self.min_raise
                else:
                    print(f"Partial raise detected (size {actual_raise_size}). Min raise remains {self.min_raise}")

                print(f"NEW CURRENT BET {self.current_bet}")
                print(f"{player.name} successfully raised")


                print(f"NEW CURRENT BET {self.current_bet}")
                print(f"MIN RAISE NOW SET TO {self.min_raise}")
                print(f"{player.name} successfully raised")

                # This is used to build a priority queue for every player who has not matched the new raise in a new order
                self.update_queue_on_raise(player)

                if player.chips == 0:
                    player.all_in = True
                return actual_raise_size
        return None






    def update_queue_on_raise(self, raiser):
        """
            After a raise, all players who have not matched the new bet
            must act again
            """
        n = len(self.active_round_players)
        start = self.active_round_players.index(raiser) # The queue order should be rebuilt after the raiser
        new_queue = [] # Temporary priority queue

        for i in range(1, n):  # Start after raiser
            idx = (start + i) % n # Used to wrap around to the indexes after the raiser
            p = self.active_round_players[idx]
            if p.folded or p.all_in: # Ignore folded or all in players
                continue
            if p.current_bet >= self.current_bet: # Ignore players who have matched or exceeded the raise
                continue
            new_queue.append(p) # Add players to the new priority queue and mark them as facing raise
            p.facing_raise = True

        self.action_queue = new_queue

    def remove_player_from_queue(self, player):
        # Removes a player once they have completed their action
        if player in self.action_queue:
            self.action_queue.remove(player)


    def next_player(self):
        """
        Returns the next valid player who must act.
        """
        while self.action_queue:

            # Get the next player at start of list
            player = self.action_queue.pop(0)

            # Ignore players who have folded or all in
            if player.folded or player.all_in:
                continue

            if self.current_bet != 0 and player.current_bet >= self.current_bet:
                continue

            return player

        # If None indicates betting round has ended
        return None

    # End of round detection
    # --------------------------------------------------
    def check_round_over(self, early_end = False):
        """
        Determines whether the betting round has finished.
        """
        # early_end is passed in to skip needing to build pots and go straight to either showdown or distributing the pot
        if not early_end:
            if self.action_queue:
                return False

            for p in self.active_round_players:
                if not p.folded and not p.all_in and p.current_bet != self.current_bet:
                    return False

        # Round over call this function to track player contributions and build pots

        self.pot.build_pots()
        print("Pots are being built")

        # Save the last round bet to be used later for future tracking
        self.last_round_bet = self.current_bet
        print(f"Last round bet: {self.last_round_bet}")
        return True

#COMMENTS ARE DONE
from collections import defaultdict
# defaultdict is used so that missing/disconnected players automatically start with 0 contribution


class Pot:
    """
    Represents a single poker pot.
    A pot has a chip amount and a set of players who are eligible to win it.
    """
    def __init__(self, amount=0, eligible_players=None):
        # total number of chips in this pot
        self.amount = amount

        # Set of players eligible to win this pot
        # Folded players are excluded, but their chips remain in the pot
        self.eligible_players = set(eligible_players) if eligible_players else set()

    def __repr__(self):
        """
        Returns a readable string representation of the pot.
        Useful for debugging and logging.
        """
        # gets the names of people who are eligible for the pot
        names = [p.name for p in self.eligible_players]
        return f"Pot(amount={self.amount}, eligible={names})"


class PotManager:
    """
    Manages all pot-related logic for a single hand:
    - Tracks player contributions
    - Handles folded players
    - Builds main and side pots
    - Distributes winnings fairly at showdown
    """
    def __init__(self, seat_order=None):
        """
        this is used to manage whenever pots are created and track who has contributed to each pot
        seat_order: list of players in a deterministic seat order for remainder distribution
                    (e.g. left-of-button -> ...). If None, list order of tied winners is used.
        """

        # Tracks how many chips each player has contributed this hand
        self.contributions = defaultdict(int) # initialise it as a default dictionary for contributions

        # Set of players who have folded during the hand
        self.folded = set()

        # List of Pot objects (main pot + side pots)
        self.pots = []

        # Seat order used for fair remainder chip distribution
        self.seat_order = seat_order or []

    def reset_for_new_hand(self):
        """
       Clears all pot-related states ready for the new next hand
       """
        self.contributions.clear()
        self.folded.clear()
        self.pots.clear()
        self.seat_order.clear()

    def add_contribution(self, player, amount):
        """
        Adds chips contributed by a player to the pot system
        """
        # Ignore invalid or zero contributions
        if amount <= 0:
            return

        # Track total contribution for pot construction
        self.contributions[player] += amount

        # Track contribution for the player object for external use
        player.total_contributed = getattr(self, "total_contributed", 0) + amount


    def mark_folded(self, player):
        """
        Marks a player as folded
        Folded players remain contributors but are not eligible to win pots
        """
        self.folded.add(player)


    def build_pots(self):
        """
        Builds the main pot and any side pots based on player contributions.
        Folded players' chips remain in pots but they are removed from eligibility.
        """

        # Copy only those players who contributed chips
        rem = {p: amt for p, amt in self.contributions.items() if amt > 0}
        pots = []
        # Track total contributed chips for validation
        total_contributed = sum(rem.values())

        # Build pots layer by layer (side pot algorithm)
        while rem:
            # Find the smallest remaining contribution
            min_c = min(rem.values())

            # Number of players still involved at this layer
            count = len(rem)

            # Chips added to this pot layer
            pot_amount = min_c * count

            # eligible = players who contributed to this layer and are not folded
            eligible = {p for p in rem.keys() if p not in self.folded}

            # Create a new pot
            pots.append(Pot(amount=pot_amount, eligible_players=eligible))

            # Subtract the layer from all remaining players
            for p in list(rem.keys()):
                rem[p] -= min_c
                if rem[p] == 0:
                    del rem[p]

        # Store built pots
        self.pots = pots

        # Validate pot
        total_built = sum(pot.amount for pot in self.pots)
        if abs(total_built - total_contributed) > 1e-6:
            print(f" Pot mismatch: contributed={total_contributed}, built={total_built}")
        else:
            print(f"Pots built correctly: {len(pots)} pots, total={total_built}")

        return pots

    def award_all_to(self, player):
        """
        Awards all chips in all pots to a single player
        Used when all other players fold
        """
        total = sum(pot.amount for pot in self.pots)

        return {player.name: total}

    def _order_for_remainder(self, winners):
        """
        Determines deterministic order for distributing leftover chips.
        Uses seat order if available.
        """
        if self.seat_order:
            ordered = []
            for seat in self.seat_order:
                for p in winners:
                    if p.name == seat:
                        ordered.append(p)
            return ordered

    def distribute_showdown(self, ranked_players):
        """
        Distributes chips at showdown

        ranked_players:
            List of players ordered by hand strength (best first)
        Returns:
            Dictionary mapping player name -> chips won
        """

        # Initialise winnings dictionary for all players
        winnings = {p.name: 0 for p in ranked_players}

        # iterate through each pot and see if players are eligible
        # distribute those pots independently
        for pot in self.pots:
            # Only players eligible for this pot can win it
            eligible = [p for p in ranked_players if p in pot.eligible_players]
            if not eligible:
                continue
            # Find the best hand score among eligible players
            best_score = max(p.hand_score for p in eligible)

            # All players tied for best score share the pot
            winners = [p for p in eligible if p.hand_score == best_score]

            # Integer division of pot among winners
            share = pot.amount // len(winners)
            remainder = pot.amount % len(winners)
            # Distribute the equal shares

            for p in winners:
                winnings[p.name] += share

            # Distribute any leftover chips using seat order or list order
            order = self._order_for_remainder(winners) or winners
            for i in range(remainder):
                winnings[order[i % len(order)].name] += 1

        return winnings

    @property
    def total(self):
        """
        Returns the total number of chips across all pots.
        """

        return sum(pot.amount for pot in self.pots)

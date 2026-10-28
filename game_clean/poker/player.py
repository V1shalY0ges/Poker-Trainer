# COMMENTS ARE DONE

class Player:
    def __init__(self, name, chips, is_agent=False, is_intermediate=False, is_bot=False, bot_level = None):
        '''
        initialise both the players and bots because they both have the same features like the cards, chips and if they are playing
        only difference is the bot feature so there is a boolean is_bot and a bot level which is used to distinguish between 2 when applying actions

        '''


        self.name = name
        self.chips = chips
        self.hole_cards = []
        self.folded = False
        self.all_in = False
        self.current_bet = 0
        self.total_bet = 0
        self.total_contributed = 0 # how much they have put into the pot
        self.starting_stack = 0 # starting number of chips typically 1000

        self.facing_raise = False # used as a boolean to re-build a priority queue if they are facing a raise

        self.hand_score = [] # a numerical representation of their best 5 cards for comparison
        self.best_hand = None # the actual best hand they have
        self.in_hand = True

        self.is_dealer = False
        self.position = None


        self.is_intermediate = is_intermediate
        self.is_agent = is_agent
        self.is_bot = is_bot
        self.last_chips = None # used to add onto when displaying the final chips when added to the winnings
        self.bot_level = bot_level # whatever is passed in


    def reset_for_new_hand(self):
        """
        Resets per-hand state (excluding chips)
        Called at the beginning of each new hand
        """
        self.hole_cards = []
        self.folded = False
        self.all_in = False
        self.current_bet = 0
        self.total_bet = 0

        self.hand_score = []
        self.in_hand = self.chips > 0
        self.best_hand = None

        self.is_dealer = False

        self.last_chips = self.chips

        self.total_contributed = 0

        self.facing_raise = False

    def reset_for_new_round(self, stage):
        """
        Resets per-round state
        this is not a full game reset so we only reset a player bet for that round to 0 and the table bet to 0
        """

        if stage != 'preflop':
            self.current_bet = 0
        self.total_bet = 0







    def __repr__(self):
        return f"<Player {self.name} | Chips: {self.chips} | Bet: {self.current_bet} | Folded: {self.folded}>"

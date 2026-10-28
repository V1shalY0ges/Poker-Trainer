# COMMENTS ARE DONE

class Player:
    def __init__(self, name, chips):
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


    def reset_for_new_hand(self):

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


        if stage != 'preflop':
            self.current_bet = 0
        self.total_bet = 0
    def __repr__(self):
        return f"<Player {self.name} | Chips: {self.chips} | Bet: {self.current_bet} | Folded: {self.folded}>"

class Bot(Player):
    def __init__(self, name, chips, is_agent=False, is_intermediate=False, is_bot=False, bot_level = None):
        super().__init__(name, chips)
        self.is_agent = is_agent
        self.is_intermediate = is_intermediate
        self.is_bot = is_bot
        self._bot_level = bot_level

    def return_bot_level(self):
        return self._bot_level

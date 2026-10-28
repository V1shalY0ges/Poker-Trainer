# COMMENTS ARE DONE HERE
import random # used to shuffle the deck randomnly
class Deck():
    '''
    used to mimic an actual playing deck by creating the cards in random order
    Handles shuffling, drawing, burning card and resetting between hands

    '''
    def __init__(self):
        # Total number of cards in a standard deck
        self.total_No = 52

        # Tracks how many cards remain (reset each hand)
        self.current = 52
        #here we create the dictionary using combinations for all the 52 cards
        # Dictionary mapping numbers 1–52 to card strings (e.g. "10H", "AS")
        # Cards are generated using all combinations of ranks and suits
        self.cards_ref = {
            i+1: rank + suit
            for i, (rank, suit) in enumerate(
                [(r, s) for s in 'HDCS' for r in ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']]
            )
        }
        # List storing the current order of cards in the deck
        self.deck_position = []
        # Initialise the deck in a shuffled state
        self.reset_deck()

    def shuffle(self):
        """
        Shuffles the deck into a new random order
        Called at the start of each hand or if the deck becomes empty
        """

        # Reset deck_position using all card values
        self.deck_position = list(self.cards_ref.values())

        # Randomly shuffle the deck order
        random.shuffle(self.deck_position)


    def draw_from_deck(self, count = 1):
        """
        Draws one or more cards from the top of the deck

        count:
            Number of cards to draw (e.g. 2 for hole cards, 1 for turn/river)
        """
        # If the deck is empty, reshuffle before drawing
        if len(self.deck_position) == 0:
            self.shuffle()



        cards = []
        # Remove cards from the top of the deck
        for _ in range(count):
            card = self.deck_position.pop(0)
            cards.append(card)
        return cards
        #the returned cards go to the player object
        #this depends on the count parameter passed in as certain rounds may need different number of cards to draw



    def burn_deck(self):
        """
        Burns (discards) the top card of the deck
        Used in Texas Hold’em before dealing community cards
        """
        if self.deck_position:
            self.deck_position.pop(0)



    def reset_deck(self):
        """
        Resets the deck to a full 52 cards and shuffles it
        Called at the start of every new hand
        """
        self.current = 52
        self.shuffle()


class Card:
    """
    Represents a single playing card
    Used mainly for visualisation and frontend communication
    """

    def __init__(self, card_str, hole_card=False, face_down=False, community_card=False):
        # Full card representation (e.g. "10H", "AS")
        self.card_str = card_str

        # Rank portion of the card (e.g. "10", "A")
        self.card_num = card_str[:-1]

        # Suit of the card (H, D, C, S)
        self.suit = card_str[-1]

        # Whether the card is hidden (e.g. opponents' hole cards)
        self.face_down = face_down

        # Whether the card is a player's hole card
        self.hole = hole_card

        # Whether the card is a community card
        self.community = community_card

    def __repr__(self):
        """
        Returns a readable string version of the card
        Helpful for debugging and logging
        """
        return f"{self.card_str}{' (Face Down)' if self.face_down else ''}"

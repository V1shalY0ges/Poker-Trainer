# this is a light tester for the bot

from game_clean.poker.intermediate_bot import IntermediateBot
import random


# Mock Player classes
class MockPlayer:
    def __init__(self, name, hole_cards=None, chips=1000):
        self.name = name
        self.hole_cards = hole_cards or []
        self.chips = chips


class RandomBot(MockPlayer):
    def get_action(self, game_state):
        """Randomly decides fold, call, or raise pre-flop or post-flop"""
        choices = ["fold", "call", "raise"]
        action_type = random.choice(choices)
        if action_type == "fold":
            return {"type": "fold", "amount": 0}
        elif action_type == "call":
            return {"type": "call", "amount": game_state.get("to_call", 20)}
        else:
            return {"type": "raise", "amount": int(game_state.get("big_blind", 20) * random.uniform(2, 3))}


# Deck helper
def generate_deck():
    ranks = "23456789TJQKA"
    suits = "CDHS"
    return [r + s for r in ranks for s in suits]


def deal_hand(deck):
    return [deck.pop(), deck.pop()]


# Simple showdown evaluation (highest card wins for simplicity)
def evaluate_winner(players, community_cards):
    # Very basic: highest single card wins
    rank_order = "23456789TJQKA"
    best_rank = -1
    winner = None
    for p in players:
        all_cards = p.hole_cards + community_cards
        top_card_rank = max([rank_order.index(c[0]) for c in all_cards])
        if top_card_rank > best_rank:
            best_rank = top_card_rank
            winner = p
    return winner


# Simulation
def simulate_hands(num_hands=50, starting_chips=1000, blind=20):
    bot = IntermediateBot(name="IntermediateBot", chips=starting_chips)
    opponent = RandomBot(name="RandomBot", chips=starting_chips)

    for hand_num in range(1, num_hands + 1):
        # Prepare deck and deal
        deck = generate_deck()
        random.shuffle(deck)
        bot.hole_cards = deal_hand(deck)
        opponent.hole_cards = deal_hand(deck)
        community_cards = [deck.pop() for _ in range(3)]  # flop

        # Pre-flop game_state
        game_state = {
            "stage": "preflop",
            "position": "BTN",
            "facing_raise": False,
            "big_blind": blind,
            "min_raise": blind * 2.5,
            "to_call": blind
        }

        # Pre-flop actions
        bot_action = bot.preflop_strategy(game_state, bot)
        opp_action = opponent.get_action(game_state)

        # Post-flop actions
        bot_post_action = bot.postflop_strategy(bot.hole_cards, community_cards, stage="flop", pot=40, to_call=blind)
        opp_post_action = opponent.get_action({"stage": "flop", "to_call": blind, "big_blind": blind})

        # Simple pot and chip tracking
        pot = 0
        for action in [bot_post_action, opp_post_action]:
            if action["type"] in ["call", "raise"]:
                pot += action["amount"]

        winner = evaluate_winner([bot, opponent], community_cards)
        winner.chips += pot
        print(f"Hand {hand_num}:")
        print(f"  Bot: {bot.hole_cards}, Opponent: {opponent.hole_cards}, Community: {community_cards}")
        print(f"  Bot Post-flop: {bot_post_action}, Opponent Post-flop: {opp_post_action}")
        print(f"  Winner: {winner.name}, Pot: {pot}")
        print(f"  Chip counts -> Bot: {bot.chips}, Opponent: {opponent.chips}\n")


# Run simulation
simulate_hands(num_hands=10)

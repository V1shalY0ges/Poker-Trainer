# COMMENTS ARE DONE
import csv
import random
from game_clean.poker.intermediate_bot import IntermediateBot

'''
We are testing the monte carlo feature for the intermediate bot and analsying the results

'''

def random_deck(exclude_cards=[]):
    '''

    Used to generate a random deck of cards
    '''
    suits = ['H', 'D', 'C', 'S']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    deck = [r+s for r in ranks for s in suits if r+s not in exclude_cards]
    return deck

def random_hand(exclude=[]):

    # Generate 2 private hole cards
    deck = random_deck(exclude)
    return random.sample(deck, 2)

def random_board(num_cards=3, exclude=[]):

    # Generate the board coards according to what stage we are at
    deck = random_deck(exclude)
    return random.sample(deck, num_cards)

# Create the bot instance
bot = IntermediateBot(name="TestBot", community_cards=[], chips=1000)

num_tests = 50


# --- Run simulations ---
results = []
for i in range(num_tests):

    # Create random scenarios to test the bot with
    hole = random_hand()
    board = random_board(num_cards=5, exclude=hole)
    pot = random.randint(50, 300)
    to_call = random.randint(10, 50)
    game_state ={}
    game_state['pot'] = pot
    game_state['stage'] = 'river'
    game_state['to_call'] = to_call
    game_state['min_raise'] = 20


    bot.community_cards = board
    # Get the action
    action = bot.postflop_strategy(hole, board, game_state, num_opponents=3)

    # Print out all the feed for that test
    print(f"Hand {hole} | Board {board} | Pot {pot} | ToCall {to_call} | "
          f"Equity={bot.last_equity:.2f} | Action={action['type']} {action['amount']}")
    result = {}
    result["Hand"] = hole
    result["Board"] = board
    result["Pot"] = pot
    result["ToCall"] = to_call
    result["Equity"] = bot.last_equity
    result["type"] = action['type']
    result["amount"] = action['amount']
    results.append(result)


filename = "monte_carlo_test.csv"
with open(filename, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)

print(f"[Simulation] Saved decisions to {filename}")

#the purpose of this testing file is to test the partial hand evaluator for postflop strategy
# Comments are done

from game_clean.poker.intermediate_bot import IntermediateBot
from game_clean.poker.partial_hand_evaluator import PartialHandEvaluator

# Create bot and evaluator
bot = IntermediateBot(name="IntermediateBot_Test", chips=1000)
evaluator = PartialHandEvaluator()

# Test hands
test_hands = [
    (['AS', 'KS'], ['2H', '7D', 'JC']),
    (['10H', '10D'], ['10S', '2C', '7H']),
    (['2S', '3S'], ['4S', '5S', '9D']),
    (['9C', '7D'], ['8H', '6S', '5D']),
    (['QD', 'JS'], ['10C', '9H', '2D'])
]

# Simulate conditions
stage = "flop"
pot = 100
to_call = 20

# Go through each test hand get the action, equity and show the result
for hole, community in test_hands:
    result = bot.postflop_strategy(hole, community, stage=stage, pot=pot, to_call=to_call)
    equity = bot.last_equity
    print(f"Hole: {hole}, Community: {community}, Equity: {equity:.2f}, Action: {result}")

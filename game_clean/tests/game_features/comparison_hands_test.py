from game_clean.poker.hand_evaluator_no_p import HandEvaluator
# COMMENTS ARE DONE
ev = HandEvaluator()
# TWO different hands testing that the comparison method works
my_hand = ['AH', 'KH']
board = ['QH', 'JH', '3C', '2H', '10H']  # royal flush
opp_hand = ['AD', 'AC']

# Generate the scores
my_score = ev.evaluate_hand(my_hand, board)
opp_score = ev.evaluate_hand(opp_hand, board)


# Debugging
print("MY:", my_score)
print("OPP:", opp_score)
print("Comparison (my>opp?):", my_score > opp_score)

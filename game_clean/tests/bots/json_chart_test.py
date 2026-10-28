import json


with open("preflop_chart.json", "r") as file:
    preflop_table = json.load(file)

def get_preflop_action(hand: str, position: str, players: int):

    try:
        decision = preflop_table[str(players)][position][hand]
        action = decision["action"]
        size = decision.get("size", None)
        return action, size
    except KeyError:
        # If hand or position not found, default to fold
        return "fold", None


hand = "AQs"
position = "BTN"
players = 2

action, size = get_preflop_action(hand, position, players)
print(f"Hand: {hand}, Action: {action}, Size: {size}")

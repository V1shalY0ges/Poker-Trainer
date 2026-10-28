# COMMENTS ARE DONE

from game_clean.database.database import Database
from game_clean.managers.PlayerProfileManager import PlayerProfileManager
from game_clean.managers.database_manager import DatabaseManager

'''
Testing that we can use the single combined database

'''

db = Database.get_instance()  # make sure the single db is used

# Get the 2 managers that have the methods to add to the single db
ppm = PlayerProfileManager()
dm = DatabaseManager()

# Add a player profile
ppm.update_profile("TestPlayer", vpip=0.3, pfr=0.2, aggression=0.5)
profile = ppm.get_profile("TestPlayer")
print("Player profile:", profile)

# Test we can log a random game
game_id = dm.log_game_start("Table1", "NLHE", 1000, 5, 10, 6)
dm.log_player_join(game_id, "TestPlayer", 1, 1000)
dm.log_player_action(game_id, "TestPlayer", "preflop", "call", 10)

# Fetch the game data and print
replay = dm.get_replay(game_id)
print("Replay data:", replay)


# Get player stats from PlayerProfileManager
print("Average profile (excluding TestPlayer):", ppm.get_average_profile(exclude="TestPlayer"))

# Get hole cards / actions from DatabaseManager
dm.log_hole_cards(game_id, "TestPlayer", ["AS", "KD"])
print("Hole cards:", dm.get_player_hole_cards(game_id, "TestPlayer"))

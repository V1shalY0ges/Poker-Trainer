#COMMENTS PARTIALLY COMPLETED


import sqlite3
import os
from datetime import datetime
from game_clean.database.database import Database


class PlayerProfileManager:
    def __init__(self, db_path=None):
        # Force database path to be based on project root to avoid errors from creating a databse in the directory
        # where the object from this class is created

        self.db = Database.get_instance() #use the merged database and get the db from there
        self.create_table()
        self.create_action_table()

    def create_table(self):
        # purpose is to create the table storing the profile for each player and this is updated with every move that the
        # person makes to keep a dynamic and better model
        # sql create command to create the player profiles which by default has set the intial values to default values
        # primary ley is the name which is the player name
        self.db.execute("""
                CREATE TABLE IF NOT EXISTS player_profiles (
                    name TEXT PRIMARY KEY,
                    hands_played INTEGER DEFAULT 0,
                    vpip REAL DEFAULT 0.0,
                    pfr REAL DEFAULT 0.0,
                    aggression REAL DEFAULT 0.0,
                    showdown_freq REAL DEFAULT 0.0,
                    bluff_rate REAL DEFAULT 0.0,
                    avg_bet_size REAL DEFAULT 0.0,
                    last_updated TEXT
                );
            """)


    def create_action_table(self):
        # creates  table storing the info about each action and the info surroudning the board when the action was done
        # the sql create command to create the action history
        # the id for the action is the primary key and then we store all the stats at that action into the db
        self.db.execute("""
                CREATE TABLE IF NOT EXISTS action_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    stage TEXT,
                    vpip REAL,
                    pfr REAL,
                    aggression REAL,
                    board_wetness REAL,
                    pot_size REAL,
                    to_call REAL,
                    stack_size REAL,
                    equity REAL,
                    action TEXT,
                    result TEXT
                );
            """)


    def get_profile(self, name):
        #method to use an sql query to query the db to get info about a player
        #to get the player profile we do it using the unique player username as the parameter to look up into the db
        row = self.db.fetchone(
            "SELECT * FROM player_profiles WHERE name = ?",
            (name,)
        )

        if row:
            return dict(row)

        #a check to ensure the last updated field is done properly in case we modify the returned row
        self.db.execute(
            "INSERT INTO player_profiles (name, last_updated) VALUES (?, ?)",
            (name, datetime.now().isoformat())
        )
        # recursively gets the new profile which is returned
        return self.get_profile(name)


    def update_profile(self, name,increment_hands =True, **stats):
        # method to constantly keep updating a profile that we retrueve with each action in the game
        profile = self.get_profile(name) #gets the profile we want to update
        for key, val in stats.items():
            if key in profile and isinstance(val, (int, float)):
                # simple smoothing for continuous learning
                profile[key] = 0.9 * profile[key] + 0.1 * val

        if increment_hands:
            profile["hands_played"] += 1  # only increment if allowed
        profile["last_updated"] = datetime.now().isoformat() #update the datetime to now


        # the sql insert command to re insert the new info into the player name and use on conflict to remove anything we updated as not everything is being updated here
        self.db.execute("""
            INSERT INTO player_profiles
            (name, hands_played, vpip, pfr, aggression, showdown_freq, bluff_rate, avg_bet_size, last_updated)
            VALUES (:name, :hands_played, :vpip, :pfr, :aggression, :showdown_freq, :bluff_rate, :avg_bet_size, :last_updated)
            ON CONFLICT(name) DO UPDATE SET
                hands_played=:hands_played,
                vpip=:vpip,
                pfr=:pfr,
                aggression=:aggression,
                showdown_freq=:showdown_freq,
                bluff_rate=:bluff_rate,
                avg_bet_size=:avg_bet_size,
                last_updated=:last_updated
        """, profile)


        #his is the insert query to get the player profile

    def get_average_profile(self, exclude=None):


        # the sql select command to retrieve the vpip, pfr and aggression
        row = self.db.fetchone("""
            SELECT AVG(vpip), AVG(pfr), AVG(aggression)
            FROM player_profiles
            WHERE name != ?
        """, (exclude,)) if exclude else self.db.fetchone("""
            SELECT AVG(vpip), AVG(pfr), AVG(aggression)
            FROM player_profiles
        """)

        if not row or all(v is None for v in row):
            # default baseline if  we dont have any data yet
            return {"vpip": 0.25, "pfr": 0.15, "aggression": 0.4}

        vpip, pfr, aggression = [v if v is not None else 0 for v in row]
        return {"vpip": vpip, "pfr": pfr, "aggression": aggression}

    def log_action(self, name, stage, vpip, pfr, aggression, board_wetness, pot_size, to_call, stack_size, equity,
                   action, result):
        # log the player action into the database using the sql insert command with the passed in parameters
        self.db.execute("""
            INSERT INTO action_history
            (name, stage, vpip, pfr, aggression, board_wetness, pot_size, to_call, stack_size, equity, action, result)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, stage, vpip, pfr, aggression,
            board_wetness, pot_size, to_call,
            stack_size, equity, action, result
        ))

    def update_action_result(self, name, stage, action, equity, result, showdown_participation= False):
        """
        Updates equity + result for previously logged actions
        """
        # Get the profile first
        profile = self.get_profile(name)

        if showdown_participation:
            profile["showdown_count"] = profile.get("showdown_count", 0) + 1 # if the player reached the showdown phase incremented it by one


        hands_played = profile.get("hands_played", 1)
        profile["showdown_freq"] = profile.get("showdown_count", 0) / hands_played # calculate the showdown frequency by dividing it by no of total hands

        # Save profile back
        self.update_profile(
            name,
            increment_hands=False,
            showdown_freq=profile["showdown_freq"],
            showdown_count=profile.get("showdown_count", 0)
        )

        self.db.execute("""
            UPDATE action_history
            SET equity = ?, result = ?
            WHERE name = ? AND stage = ? AND action = ? AND result = 'pending'
        """, (equity, result, name, stage, action))

    def increment_hands_played(self, player_name):
        profile = self.get_profile(player_name)
        profile["hands_played"] = profile.get("hands_played", 0) + 1
        self.update_profile(player_name, hands_played=profile["hands_played"])

    def calculate_showdown_frequency(self, player_name):
        """
        Calculates the fraction of hands where the player reached showdown
        based on actions logged in action_history.
        """

        row = self.db.fetchone("""
            SELECT COUNT(*) FROM action_history
            WHERE name = ? AND result = 'complete'
        """, (player_name,))

        showdown_actions = row[0] if row else 0

        profile = self.get_profile(player_name)
        hands_played = profile.get("hands_played", 1)
        return showdown_actions / hands_played

    def get_profile_with_actions(self, name):
        return self.db.fetchall("""
                    SELECT p.name, p.vpip, p.pfr, a.stage,
                    a.action, a.result
                    FROM player_profiles p
                    JOIN action_history a ON p.name = a.name
                    WHERE p.name = ?
                """, (name,))

    '''
    def close(self):
        self.conn.close()
    '''

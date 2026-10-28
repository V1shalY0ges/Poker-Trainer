# COMMENTS ARE DONE
import sqlite3




from datetime import datetime
from game_clean.database.database import Database


class DatabaseManager:
    def __init__(self):
        # pass in the default data base path location that we created the db in
        self.db = Database.get_instance()

        self.create_tables()  # Ensure tables exist when initialised
    def create_tables(self):
        '''
        this creates tables for the games, players, actions and community cards filling in all the attributes
        and the primary keys and foreign keys
        '''
        # HERE we use the db.execute with the sql to create the games table with the attributes like
        # game id which is the primary key
        self.db.execute("""
                    CREATE TABLE IF NOT EXISTS games (
                        game_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        table_id TEXT,
                        game_type TEXT,
                        starting_chips INTEGER,
                        small_blind INTEGER,
                        big_blind INTEGER,
                        max_players INTEGER,
                        timestamp DATETIME
                    );
                """)
        # Here we create the players attribute with the primary key being a composite key of the player id
        # and game id and a forein key being the game id
        self.db.execute("""
                    CREATE TABLE IF NOT EXISTS players (
                        player_id TEXT,
                        game_id INTEGER,
                        seat_position INTEGER,
                        chips_start INTEGER,
                        chips_end INTEGER,
                        PRIMARY KEY (player_id, game_id),
                        FOREIGN KEY (game_id) REFERENCES games(game_id)
                    );
                """)


        # here we create the actions table with a global unique action key as the primary key
        # that keeps getting incremented
        # we create a foregin key using the game id as it is alwaus a UUID so unique
        # we also create another foreign key that is composite using the player id and game id
        self.db.execute("""
                    CREATE TABLE IF NOT EXISTS actions (
                        action_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        game_id INTEGER,
                        player_id TEXT,
                        stage TEXT,
                        action_type TEXT,
                        amount INTEGER,
                        timestamp DATETIME,
                        FOREIGN KEY (game_id) REFERENCES games(game_id),
                        FOREIGN KEY (player_id, game_id) REFERENCES players(player_id, game_id)
                    );
                """)

        # here we create the table for the community cards
        # the cards are always unique so serve as the primary key and the foreign key is the game id
        self.db.execute("""
                    CREATE TABLE IF NOT EXISTS community_cards (
                        card_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        game_id INTEGER,
                        stage TEXT,
                        cards TEXT,
                        FOREIGN KEY (game_id) REFERENCES games(game_id)
                    );
                """)

        # this is to create the hole cards and we need to link them to the player they belong to
        # so we use player id as the primary key combined with the game id making it composite
        # the foreign key is the game id
        self.db.execute("""
                    CREATE TABLE IF NOT EXISTS hole_cards (
                        game_id INTEGER,
                        player_id TEXT,
                        card1 TEXT,
                        card2 TEXT,
                        PRIMARY KEY (game_id, player_id),
                        FOREIGN KEY (game_id) REFERENCES games(game_id)
                    );
                """)




    def log_game_start(self, table_id, game_type, starting_chips, small_blind, big_blind, max_players):
        '''
        this method is used to add to the games column the info about the new game when it starts
        in the preflop stage
        '''

        timestamp = datetime.now() #when a game starts we get the current time and add the game
        # into the table


        # now that the game starts we insert the starting info into the games table
        cursor = self.db.execute("""
            INSERT INTO games
            (table_id, game_type, starting_chips, small_blind, big_blind, max_players, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (table_id, game_type, starting_chips, small_blind, big_blind, max_players, timestamp))


        return cursor.lastrowid

    def log_player_join(self, game_id, player_id, seat_position, chips_start):
        '''
        this is used to add into the players table the info about any player and their corresponding table
        '''



        # this is the sql statement to insert the players into the table when they connect into a game
        self.db.execute("""
                    INSERT OR IGNORE INTO players
                    (player_id, game_id, seat_position, chips_start, chips_end)
                    VALUES (?, ?, ?, ?, ?)
                """, (player_id, game_id, seat_position, chips_start, chips_start))

    def log_community_cards(self, game_id, stage, cards):
        '''
        this is used to add the community cards to the game table for each individual game
        at each individual stage
        '''
        cards_str = ",".join(cards) # this is used to link the community card sinto a string
        # to be added into the db like 'AS, 5D, 7H'

        self.db.execute("""
                    INSERT INTO community_cards (game_id, stage, cards)
                    VALUES (?, ?, ?)
                """, (game_id, stage, cards_str))


    def log_player_action(self, game_id, player_id, stage, action_type, amount):
        '''
        this is used to add the player actions to the game table for each individual game at each individual stage
        '''
        timestamp = datetime.now()


        # this is the sql statement to insert the players current action and all info about that action into the database
        self.db.execute("""
                    INSERT INTO actions
                    (game_id, player_id, stage, action_type, amount, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (game_id, player_id, stage, action_type, amount, timestamp))

    def log_game_ended(self, game_id, player_results):
        '''
        this is used record the final chips after a game has ended using the player results dictionary
        '''

        # the game has eneded so we need to log the results
        # to do that we go through each player and their resulting end chips and use the update sql command to update them in the db
        for player_id, chips_end in player_results.items():
            self.db.execute("""
                            UPDATE players
                            SET chips_end = ?
                            WHERE player_id = ? AND game_id = ?
                        """, (chips_end, player_id, game_id))


    def log_hole_cards(self, game_id, player_id, cards):
        """
        Logs the two hole cards dealt to a player at the start of a hand.
        """
        if len(cards) != 2:
            raise ValueError("Must provide exactly 2 cards") #exceptions incase we
            # dont get both the hole cards we need

        # the insert command to add the hole cards to the correct game and to the correct player
        self.db.execute("""
                    INSERT OR REPLACE INTO hole_cards
                    (game_id, player_id, card1, card2)
                    VALUES (?, ?, ?, ?)
                """, (game_id, player_id, cards[0], cards[1]))


    def get_replay(self, game_id):


        # Fetch players
        # we fetch all the necessary info for every replay so the players in that replay game
        # we need all the actions of that game
        # we need all the cards of that game

        players = self.db.fetchall(
            "SELECT * FROM players WHERE game_id = ?", (game_id,) # all the searching is done using
            # the unique game id allowing for fast lookup
        )

        actions = self.db.fetchall(
            "SELECT * FROM actions WHERE game_id = ? ORDER BY action_id ASC", (game_id,)
        )

        community_cards = self.db.fetchall(
            "SELECT * FROM community_cards WHERE game_id = ?", (game_id,)
        )


        return {
            "players": players,
            "actions": actions,
            "community_cards": community_cards
        }
    # create a dictionary that we return to the replay manager

    def get_replay_full_join(self, game_id):
        """
        Retrieves full replay information
        using a single cross-table
        parameterised SQL query.
        """
        return self.db.fetchall("""
            SELECT
                g.game_id,
                g.game_type,
                g.timestamp,
                p.player_id,
                p.seat_position,
                a.stage,
                a.action_type,
                a.amount,
                a.timestamp AS action_time,
                c.cards AS community_cards
            FROM games g
            JOIN players p ON g.game_id = p.game_id
            JOIN actions a ON p.player_id =
            a.player_id AND p.game_id = a.game_id
            LEFT JOIN community_cards c ON g.game_id = c.game_id
            WHERE g.game_id = ?
            ORDER BY a.action_id ASC
        """, (game_id,))

    def get_player_hole_cards(self, game_id, player_id):
        # sql method to query the database to get the hole cards for each player given the player name and the table name


        # to get the hole cards we use the composite key of the game id and player id to look up the game and the player and from there get the 2 cards and put them in a list and return it
        result = self.db.fetchone("""
                    SELECT card1, card2 FROM hole_cards
                    WHERE game_id = ? AND player_id = ?
                """, (game_id, player_id))
        if result:
            return list(result)
        return []
    '''
    def close(self):
        self.connection.close()
    '''

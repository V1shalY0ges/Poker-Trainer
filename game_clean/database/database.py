#COMMENTS ARE DONE

import sqlite3
import os
class Database:
    """
    single class for handling SQLite database connections
    Ensures that only one connection exists per application instance
    """
    # Class-level variable to store the single instance
    _instance = None
    def __init__(self):
        # Determine the directory where this file is
        base_dir = os.path.dirname(os.path.abspath(__file__))

        # Construct full path to the SQLite database file
        db_path = os.path.join(base_dir, "poker.db")

        # Connect to SQLite database
        # check_same_thread=False allows multiple threads to share the same connection
        self.connection = sqlite3.connect(db_path, check_same_thread=False)

        # Return rows as sqlite3.Row objects (dictionary-like access: row["column_name"])
        self.connection.row_factory = sqlite3.Row

    @classmethod
    def get_instance(cls):
        """
        Returns the singleton instance of the Database class.
        Creates it if it does not exist yet.
        """
        if cls._instance is None:
            # Create a new instance if none exists
            cls._instance = Database()

        return cls._instance

    def execute(self, query, params=()):
        """
        Executes a SQL query (INSERT, UPDATE, DELETE, SELECT.) with optional parameters.
        Commits the transaction automatically.
        Returns the cursor object.
        """
        # Create a cursor to execute SQL commands
        cursor = self.connection.cursor()

        # Execute the SQL query with parameters
        cursor.execute(query, params)

        # Commit changes to the database
        self.connection.commit()

        # Return the cursor for further use if needed
        return cursor

    def fetchone(self, query, params=()):
        """
        Executes a SQL query and returns a single row as sqlite3.Row.
        Useful for SELECT queries where only one row is expected.
        """

        # Execute and fetch first row
        return self.execute(query, params).fetchone()

    def fetchall(self, query, params=()):
        """
        Executes a SQL query and returns all rows as a list of sqlite3.Row objects.
        Useful for SELECT queries returning multiple rows.
        """
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

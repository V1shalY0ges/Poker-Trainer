#COMMENTS ARE DONE

from game_clean.poker.network_table import NetworkTable
from game_clean.poker.player import Player
from fastapi import WebSocket, WebSocketDisconnect
from game_clean.managers.connection_manager import ConnectionManager
import asyncio

class TableManager:
    def __init__(self, connection_manager: ConnectionManager):
        #this stores a connection manager which adds the incoming connection to their respective tables
        self.connection_manager = connection_manager

        # Dictionary mapping table_id -> NetworkTable instance
        self.tables: dict[str, NetworkTable] = {}

        # Tracks waiting rooms (lobbies) with host info and readiness
        self.lobbies: dict[str, dict] = {}
    async def handle_player_session(self, websocket, table_id, player_id):

        """
        Main handler for a player WebSocket session.
        Manages joining a table, lobby state, validating moves, and broadcasting updates.
        """

        # If table doesn't exist yet, create a new NetworkTable with empty players
        if table_id not in self.tables:
            self.tables[table_id] = NetworkTable(players=[])

        table = self.tables[table_id]

        # Check if this player is already in the table
        existing_player = next((p for p in table.players if p.name == player_id), None)

        # If not, create a new Player with default chips and add to table
        if not existing_player:
            player = Player(name=player_id, chips=1000)
            table.players.append(player)
        else:
            player = existing_player


        # --- Setup lobby tracking for host to start game by grabbing the ID for the host
        # and the boolean to check if they are ready to start
        if table_id not in self.lobbies:
            self.lobbies[table_id] = {"host": player_id, "ready": False}
        lobby = self.lobbies[table_id]


        #this handles the alert to all players when a player has joined with all their info
        await self.connection_manager.broadcast(
            table_id,
            {"type": "player_joined", "player": player_id, "state": table.get_state()}
        ) # send a message to everyone in the table saying a new player has joined

        # --- Notify everyone about host prompt
        await self.connection_manager.broadcast(
            table_id,
            {"type": "host_prompt", "host": lobby["host"], "state": table.get_state()}
        )
        try:
            '''
            MAIN game loop to control how the sockets communicate with the game by repeatedly waiting for an action
            and amount ensuring it comes from the right person by validating against the table to check whose turn it is
            it then checks if the action is valid if not the loop reprompts them for an action
            the action is stored in a json dictionary with the action and amount which is deault to 0
            if no actions need an amount like calling checking or folding
            '''
            while True:
                data = await websocket.receive_json()
                action = data.get("action")
                amount = data.get("amount")

                # --- Handle host pressing "Start Game" ---
                if action == "start_game" and player_id == lobby["host"]:
                    # Mark host as ready
                    lobby["ready"] = True

                    # Notify all players that host has started the game
                    await self.connection_manager.broadcast(table_id, {
                        "type": "game_starting",
                        "message": f"Host {player_id} started the game!"
                    })
                    # Start the game after host confirms
                    async def broadcast_callback(msg):

                        table_players = self.connection_manager.connections_for_table(table_id)

                        for ws, pid in table_players:

                            # If message already contains state → personalise it
                            if msg.get("type") == "state_update":
                                personalised = msg.copy()
                                personalised["state"] = table.get_state_for_player(pid)

                                await self.connection_manager.send_personal_message(
                                    ws,
                                    personalised
                                )

                            else:
                                # Public messages broadcast normally
                                await self.connection_manager.send_personal_message(ws, msg)

                    # Begin new hand and start async task to play hand
                    table.start_new_hand()
                    asyncio.create_task(table.play_hand(broadcast_callback))
                    continue  # skip rest of loop, wait for next messages

                # Get the current player's turn
                current_player = table.current_player.name if table.current_player else None
                current_bet = table.betmanager.current_bet
                min_raise = table.betmanager.min_raise


                # current error handling to reject any player who tries to submit when it is not their turn
                # might chnage this to grey out buttons when it is not their turn and then re colour when it is their turn
                if player_id != current_player:
                    # Reject the move and notify this player only
                    await self.connection_manager.send_personal_message(websocket, {
                        "type": "error",
                        "message": f"Not your turn! It’s currently {current_player}’s turn."
                    })
                    continue  # Do not process, just skip to next received message

                # If it is their turn, process the move as normal
                await table.receive_player_action(
                    player_name=player_id,
                    action=action,
                    amount=amount
                )
        # an exception in case refresh of page or player leaves mid game
        except Exception as e:
            print(f"Error with player {player_id}: {e}")
        finally:
            # safely clean up when a player disconnects
            print(f"Player {player_id} disconnected from table {table_id}")
            await self.connection_manager.disconnect(websocket, table_id, player_id)

            # Identify disconnected player object
            if player_id in [p.name for p in table.players]:
                disconnected_player = next(p for p in table.players if p.name == player_id)

            # Auto-fold if hand is in progress
            if table.is_hand_in_progress() and not disconnected_player.folded:
                print(f"Auto-folding {player_id} due to disconnect.")
                await table.receive_player_action(player_name=player_id, action="fold", amount=0)

            # Remove player from table
            table.players = [p for p in table.players if p.name != player_id]
            await self.connection_manager.broadcast(table_id, {
                "type": "player_left",
                "player": player_id,
                "state": table.get_state()
            })
    '''
    some methods here to validate the user input and ensure it is valid
    '''
    def can_call(self, player, current_bet):
        # Player can call if not folded or all-in and current bet < table's current bet
        if player.folded or player.all_in:
            return False
        return player.current_bet < current_bet

    def can_check(self, player, current_bet):
        # Player can check if not folded or all-in and current bet equals table's current bet
        if player.folded or player.all_in:
            return False
        return player.current_bet == current_bet
        #NEED CHECK if current bet == 0

    def can_raise(self, player, current_bet, min_raise, raise_amount=None):
        # Player can raise if not folded or all-in and has enough chips
        if player.folded or player.all_in:
            return False
        if raise_amount is None:
            raise_amount = min_raise
        total_needed = (current_bet - player.current_bet) + raise_amount
        return player.chips >= total_needed

    #  Add bots to a table
    def add_bots(self, table_id: str, bot_list: list[dict]):
        # If table does not exist, create it first
        if table_id not in self.tables:
            self.tables[table_id] = NetworkTable(players=[])

        table = self.tables[table_id]

        # Add bot objects to the table's players list as both are lists so extend

        table.players += bot_list

# COMMENTS ARE DONE HERE


from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect
'''
the connection manager is used to handle incoming websockets and connect them to a table
'''
class ConnectionManager:
    def __init__(self):
        # this is a dictionary storing a table id and player id of all clients connected to that table
        # Dict[table_id, List[Tuple[WebSocket, player_id]]]
        self.tables: Dict[str, List[tuple[WebSocket, str]]] = {}

    async def connect(self, websocket: WebSocket, table_id :str, player_id: str):
        '''
        this is uses to manage an incoming websocket connection i.e a plaer connection
        if there is no availale table_id we create a new game assigning it a custom table id and then we add the websocket
        player object to that table
        it is asynchronous to allow other processes to occur whilst we are connecting to the table
        '''

        await websocket.accept() #allow any incoming websocket connection
        if table_id not in self.tables:
            self.tables[table_id] = [] #uses the unique table id to see if a table has been created and if not make one
        self.tables[table_id].append((websocket, player_id)) #then we add the entire websocket and the player id/ username
        # they registered with to the table
        print(f"Player {player_id} joined table {table_id}")

    async def disconnect(self, websocket: WebSocket, table_id: str, player_id: str):
        # remove players from the table object when the websocket has disconnected and terminate the connection
        if table_id in self.tables:
            self.tables[table_id] = [
                (ws, pid) for ws, pid in self.tables[table_id] # we store a tuple when we add a player to a table so we need to
                # delete and remove the entire websocket connection and the table id
                if ws != websocket
            ]
            if not self.tables[table_id]:
                del self.tables[table_id]
            print(f"Player {player_id} disconnected from table {table_id}")


    async def broadcast(self, table_id :str, message: dict):
        '''
        this is used to send a json dict message to all players on the same table id
        '''
        if table_id not in self.tables:
            return
        for ws, pid in self.tables[table_id]:  # unpack tuple
            try:
                await ws.send_json(message)  #  ws is websocket object
            except Exception as e:
                print(f"Error broadcasting to table {table_id}: {e}") #handle any exceptions if we cant send
                # a broadcast to everyone


    async def send_personal_message(self, websocket: WebSocket, message: dict):
        #this will send a personal message to a websocket
        await websocket.send_json(message) # the websocket is the player connection

    def connections_for_table(self, table_id: str):
        """
        Returns a list of (websocket, player_id) tuples for a table
        """
        return self.tables.get(table_id, [])

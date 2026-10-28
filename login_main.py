# COMMENTS ARE DONE



# ---------------- FastAPI core imports ----------------
# FastAPI is the main web framework
# Request is used to access incoming HTTP request data
# Depends is used for dependency injection (e.g. authentication)
# WebSocket and WebSocketDisconnect are used for real-time game communication
# HTTPException allows returning proper HTTP error responses
from fastapi import FastAPI, Request, Depends, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import RedirectResponse
# Used to serve static files such as CSS, JS, images
from fastapi.staticfiles import StaticFiles

# Used to render HTML templates with dynamic data
from fastapi.templating import Jinja2Templates

# Used to generate unique table IDs
from uuid import uuid4

# Import authentication routes and dependency to get the logged-in user
from auth.routes import router as auth_router, get_current_user

# Manages active WebSocket connections
from game_clean.managers.connection_manager import ConnectionManager

# Handles replay analysis and logic
from game_clean.managers.replay_manager import ReplayManager

# Manages poker tables and game state
from game_clean.managers.table_manager import TableManager

# Used to decode JWT authentication tokens
from auth.jwt_auth import decode_access_token

# Used when returning raw HTML responses
from fastapi.responses import HTMLResponse

# Used for request body validation
from pydantic import BaseModel

# Poker player class
from game_clean.poker.player import Player

# Network-enabled poker table class
from game_clean.poker.network_table import NetworkTable

# Used for direct SQLite database access
import sqlite3

# Used for filesystem path handling
import os
from datetime import datetime

# SQLAlchemy database dependency

from auth.database import get_db
from sqlalchemy.orm import Session

from auth.database import Base, engine
import auth.models

# ---------------- Database Path Setup ---------------
# Get the directory of this file (login_main.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Construct absolute path to the poker database
DB_PATH = os.path.join(BASE_DIR, "game_clean", "database", "poker.db")

# ---------------- Bot Settings Model ----------------
# Defines the expected JSON structure when creating bot

class BotSettings(BaseModel):
    num_bots: int
    difficulty: str

# ---------------- FastAPI App ----------------
# Create the FastAPI application instance
app = FastAPI()

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/login", status_code=302)

Base.metadata.create_all(bind=engine)

# Managers
# Manage incoming websocket connections per table
connection_manager = ConnectionManager()

# Manages tables and game logic
table_manager = TableManager(connection_manager)

# Active games
# Stores current active games
active_tables = {}  # Format: table_id : host_username

# Static + Templates
# Mount static folder (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Load HTML templates from templates directory
templates = Jinja2Templates(directory="templates")

# Include auth routes
app.include_router(auth_router)

# ---------------- HTML Pages ----------------

# Login page
@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

# Logout page
@app.get("/logout")
def logout(request: Request):
    return templates.TemplateResponse(request=request, name="logout.html")

# Register Page
@app.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html")


# Forgot Password Page
@app.get("/forgot_password")
def forgot_password_page(request: Request):
    return templates.TemplateResponse(request=request, name="forgot_password.html")

# Reset Password Page
@app.get("/reset-password")
def reset_password_page(request: Request):
    return templates.TemplateResponse(request=request, name="reset_password.html")



# Home Page
@app.get("/home")
def home_page(request: Request):
    return templates.TemplateResponse(
    request=request,
    name="dummy_home.html"
)


# Dummy home page for testing/ offline mode
@app.get("/dummy_home")
def home_page(request: Request):
    return templates.TemplateResponse(
    request=request,
    name="dummy_home.html"
)

# Game page for real multiplayer games
@app.get("/game/{table_id}")
def game_page(request: Request, table_id: str):
    return templates.TemplateResponse(
    request=request,
    name="game.html",
    context={"table_id": table_id}
)

# Dummy game page with optional bots
@app.get("/dummy_game/{table_id}", response_class=HTMLResponse)
async def dummy_game(request: Request, table_id: str):
    # Read query parameter like bot=adaptive
    bot_mode = request.query_params.get("bot")
    if bot_mode == 'adaptive':
        # Create table if it does not exist
        if table_id not in table_manager.tables:
            table_manager.tables[table_id] = NetworkTable(players= [])

        players = table_manager.tables[table_id].players

        # Only add adaptive bot if none already exists
        if not any(p.is_bot for p in players):
            adaptive_bot = Player(
                name="ADAPTIVE_BOT",
                chips=1000,
                is_bot=True,
                bot_level="adaptive"
            )
            # Add bot to the table
            bot_list = [adaptive_bot]
            table_manager.add_bots(table_id, bot_list)

    return templates.TemplateResponse(
    request=request,
    name="dummy_game.html",
    context={"table_id": table_id}
)

# Win screen page
@app.get("/win_screen.html", response_class=HTMLResponse)
async def win_screen(request: Request):
    return templates.TemplateResponse(request=request, name="win_screen.html")

# Settings page for bot selection
@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """
    Display the game settings page where the user can choose
    number of bots and difficulty level.
    """
    return templates.TemplateResponse(request=request, name="settings.html")


def verify_replay_access(game_id: int, username: str):
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("""
            SELECT 1
            FROM players
            WHERE game_id = ?
              AND player_id = ?
            LIMIT 1
        """, (game_id, username)).fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Replay not found"
        )

# Replays list page
@app.get("/replays", response_class=HTMLResponse)
def replays_page(request: Request):
    return templates.TemplateResponse(
    request=request,
    name="replays.html"
)

# Return list of available replays
@app.get("/api/replays")
def list_replays(current_user = Depends(get_current_user)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all table ID's and timestamps
    cursor.execute("""
    SELECT DISTINCT g.table_id, g.timestamp
    FROM games AS g
    JOIN players AS p
        ON g.game_id = p.game_id
    WHERE p.player_id = ?
    ORDER BY g.timestamp DESC
""", (current_user.username,))
    rows = cursor.fetchall()
    conn.close()

    replays = []

    # Format timestamps for display
    for table_id, timestamp in rows:
        dt = datetime.fromisoformat(timestamp)
        pretty_time = dt.strftime("%A %d %B • %H:%M")

        replays.append({
            "table_id": table_id,
            "timestamp": timestamp,
            "pretty_time": pretty_time
        })

    return {"replays": replays}

# Replay analysis page for a specific action
@app.get("/replay/action/{game_id}/{action_id}", response_class=HTMLResponse)
def replay_action_page(request: Request, game_id: str, action_id: int):
    return templates.TemplateResponse(
    request=request,
    name="replay_action.html",
    context={
        "game_id": game_id,
        "action_id": action_id
    }
)


# Replay action analysis data
@app.get("/api/replay/action/{table_id}/{action_id}")
def replay_action_data(
    table_id: str,
    action_id: int,
    current_user=Depends(get_current_user)
):
    # Hero is the logged-in user
    hero_id = current_user.username

    # Convert the table ID to the game ID
    game_id = get_game_id_from_table(table_id)

    # Actually analyse the replay
    rm = ReplayManager(game_id, hero_id)

    analysis = rm.analyse_hero_action(action_id)

    if not analysis:
        raise HTTPException(status_code=404, detail="Action not found")

    snapshot = analysis.get("state", {})
    # Generate the snapshot for the frontend
    snapshot = analysis.get("state", {})
    snapshot["community_cards"] = snapshot.pop("board", [])
    if not analysis:
        raise HTTPException(status_code=404, detail="Action not found")

    return {
        "state": snapshot,
        "stage": snapshot.get("stage", "-"),
        "hero": analysis["actual"][0],
        "amount": analysis["actual"][1] or 0,
        "optimal": analysis["optimal"][0],
        "optAmount": analysis["optimal"][1] or 0,
        "equity": analysis["equity"] or 0,
        "reason": analysis["explanation"]
    }

# Replay overview page
@app.get("/replay/{table_id}", response_class=HTMLResponse)
def replay_page(request: Request, table_id: str):
    return templates.TemplateResponse(request=request, name="replay.html")
# Full replay data
@app.get("/api/replay/{table_id}")
def get_replay(table_id:str, current_user=Depends(get_current_user)):
    hero_id = current_user.username  # Use username as hero ID
    game_id = get_game_id_from_table(table_id)  # map table_id -> game_id
    if game_id is None:
        raise HTTPException(status_code=404, detail="Replay not found")

    verify_replay_access(game_id, current_user.username)

    rm = ReplayManager(game_id = game_id, hero_id = hero_id)
    actions_json = []
    for action in rm.actions:
        # Analyse the hero action at each stage
        result = rm.analyse_hero_action(action[0])
        if result:
            actions_json.append({
                "stage": action[3],  # e.g., PREFLOP, FLOP
                "id": action[0],  # action ID
                "hero": result["actual"][0],  # hero's real action
                "amount": result["actual"][1] or 0,  # hero's amount
                "optimal": result["optimal"][0],  # optimal action
                "optAmount": result["optimal"][1] or 0,  # optimal amount
                "equity": result["equity"] or 0,  # equity
                "reason": result["explanation"]  # explanation
            })

    return {"table_id": table_id, "actions": actions_json}

# Convert table_id to game_id
def get_game_id_from_table(table_id:str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # SQL select query to query the DB to find the game where we pass in any table ID
    cursor.execute(
        "SELECT game_id FROM games WHERE table_id = ?",(table_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Replay not found")

    return row[0]  # this is the game_id from the passed in table id

# ---------------- Game APIs ----------------
from fastapi import APIRouter

# Router for game-related endpoints
game_router = APIRouter(prefix="/games", tags=["Games"])


# Create a new game
@game_router.post("/create")
def create_custom_game(current_user=Depends(get_current_user)):
    # Generate a random table ID
    table_id = str(uuid4())[:8]

    # Host username is assigned to the table ID
    active_tables[table_id] = current_user.username
    return {"table_id": table_id, "host": current_user.username}


# Add bots before game starts
@game_router.post("/{table_id}/initialise_bots")
async def initialise_bots(table_id: str, settings: BotSettings, current_user=Depends(get_current_user)):
    """
    Adds bots to a table BEFORE the game starts.
    """

    # Exceptions in case we are unable to find a table
    if table_id not in active_tables:
        raise HTTPException(status_code=404, detail="Table not found")

    # Exception in case number of bots is not satisfied
    if settings.num_bots < 0 or settings.num_bots > 2:
        raise HTTPException(status_code=400, detail="Number of bots must be 0, 1, or 2")

    # Ensure the table exists in TableManager
    if table_id not in table_manager.tables:
        table_manager.tables[table_id] = NetworkTable(players=[], table_id = table_id)

    bot_list = []
    # Create the required number of bots needed using player object and add it into the Network Table
    for i in range(settings.num_bots):
        bot_player = Player(
            name=f"BOT_{i + 1}",
            chips=1000,
            is_bot=True,
            bot_level=settings.difficulty.lower()
        )
        bot_list.append(bot_player)

    table_manager.add_bots(table_id, bot_list)
    return {"message": f"{settings.num_bots} bot(s) added to table {table_id}"}

# Register game router
app.include_router(game_router)
# ---------------- WebSocket ----------------
@app.websocket("/ws/{table_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, table_id: str, player_id: str, token: str = None):
    # Validate token first
    # Reject connection if no token provided
    if not token:
        await websocket.close(code=1008)  # Policy violation
        return

    # decode JWT token
    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=1008)
        return
    # Extract user ID
    user_id = payload.get("sub")

    await connection_manager.connect(websocket, table_id, player_id)
    try:
        await table_manager.handle_player_session(websocket, table_id, player_id)
    except WebSocketDisconnect:
        print(f"Connection closed: {player_id}")
    finally:
        await connection_manager.disconnect(websocket, table_id, player_id)

from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from auth.database import get_db
from auth import crud, models
from auth.jwt_auth import create_access_token, decode_access_token
import re
from auth.security import generate_reset_token, verify_reset_token
from auth.email_utils import send_reset_email
from auth.config import FRONTEND_URL
from auth.crud import get_user_by_email, update_user_password

from datetime import timedelta
from fastapi import BackgroundTasks


router = APIRouter(prefix="/auth", tags=["Auth"])

# ---------------- Register ----------------
'''
here the frontend html page for register calls this backend route
this is a post route because it contains private info that we dont want to send publicly
when we register we need to verify against certain duplicates in the db where
if the username or email exists already
if it is all brand new we create the user using the crud file method
'''
@router.post("/register")
def register(
        username: str = Form(...),
        email: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):
    if not username.strip() or not email.strip() or not password.strip():
        raise HTTPException(status_code=400, detail="All fields are required")

    validate_email(email)
    validate_password(password, username, email)

    if crud.get_user_by_email(db, email):
        raise HTTPException(status_code=400, detail="Email already registered") #raise notices if email
        # is already used
    if crud.get_user_by_username(db, username):
        raise HTTPException(status_code=400, detail="Username already taken") #raise notices is
        # username has already been used
    user = crud.create_user(db, username, email, password) #call the create user method to
    # add them to the db that we created
    return {"id": user.id, "username": user.username, "email": user.email}


def validate_email(email: str):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(pattern, email):
        raise HTTPException(status_code=400, detail="Invalid email format")

def validate_password(password: str, username: str = "", email: str = ""):
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
    if password.isdigit():
        raise HTTPException(status_code=400, detail="Password cannot be entirely numeric")
    common_passwords = ["password", "12345678", "qwerty", "password123"]
    if password.lower() in common_passwords:
        raise HTTPException(status_code=400, detail="Password is too common")
    if username.lower() in password.lower() or email.lower() in password.lower():
        raise HTTPException(status_code=400, detail="Password cannot contain username or email")

# ---------------- Login ----------------
'''
here the frontend html page for login calls this backend route
the crud file authenticates the user by checking the input password and checking if when hashed it matches
the users stored hashed password that they registered with
'''
@router.post("/login")
def login(
    identifier: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = crud.authenticate_user(db, identifier, password) #method to authenticate the user
    # from input password and identifier
    if not user:
        raise HTTPException(status_code=400, detail="Invalid login credentials")
        # exception to handle when the authentication fails with an error message

    # create JWT
    access_token = create_access_token(subject=user.id) #call the create token message with
    # the user id being the unique payload info
    return {
        "access_token": access_token,
        "token_type": "bearer", # this is the predefined token type which we set as being
        # bearer as the user holds the token in sessions
        "username": user.username  # send username back to frontend
    }
# ---------------- Forgot Password / Reset ----------------#




@router.post("/forgot-password")
def forgot_password(
    email: str = Form(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_email(db, email)
    if not user:
        # Security: don’t reveal if email exists
        return {"message": "If the email exists, a reset link has been sent."}

    # Generate secure token
    token = generate_reset_token(user.email)

    # Build reset link
    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"

    # Send email in background
    if background_tasks:
        background_tasks.add_task(
            send_reset_email,
            to_email=email,
            token=reset_link
        )

    return {"message": "If the email exists, a reset link has been sent."}

@router.post("/reset-password-token")
def reset_password(
    token: str = Form(...),
    new_password: str = Form(...),
    db: Session = Depends(get_db)
):
    print("Token received:", token)
    email = verify_reset_token(token)
    print("Decoded email:", email)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate new password
    validate_password(new_password, username=user.username, email=user.email)

    # Update password
    crud.update_user_password(db, user.id, new_password)

    return {"message": "Password has been reset successfully."}
# ---------------- OAuth2 / current user ----------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
'''
method used to get the current user and all their info to be used for verification by the frontend for any action
to do this we need to use the jwt token and decode it first
if we dont have a decoded token or even a token it raises an error as the
user is not authenticated so a new token needs to be created
we get the user id from the token as it is unique so can be used to query
our database to get the entire user object
this user object is returned
'''
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token) # call the jwt auth decode function
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials") #raise an exception
        # if the token does not exist because we have no payload
    user_id = payload.get("sub")
    user = db.query(models.User).filter(models.User.id == int(user_id)).first() #db query to get the user from the database
    if not user:
        raise HTTPException(status_code=401, detail="User not found")# exception in case the user does not exist in the database
    return user
'''
get request to return the user info
'''
@router.get("/me")
def get_me(current_user: models.User = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username, "email": current_user.email}

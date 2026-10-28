from sqlalchemy.orm import Session
from auth import models
from auth.jwt_auth import get_password_hash, verify_password

#retrieve users by email to check if emails have already been used, same logic for id and useranem
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

'''
to create a user all that is done is a hashed password is created and we create a data entry for the user using the models class for the data structure
'''
def create_user(db: Session, username: str, email: str, password: str):
    hashed = get_password_hash(password)
    user = models.User(username=username, email=email, hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
'''
to authenticate a user we retrieve them from the email or username passed in and call the verify password method on their input password and the hashed password
'''
def authenticate_user(db: Session, identifier: str, password: str):
    user = get_user_by_email(db, identifier) or get_user_by_username(db, identifier)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def update_user_password(db: Session, user_id: int, new_password: str):
    """Update a user's password in the database"""
    user = get_user_by_id(db, user_id)
    if not user:
        return None  # Or raise exception if you prefer
    hashed = get_password_hash(new_password)
    user.hashed_password = hashed
    db.commit()
    db.refresh(user)
    return user

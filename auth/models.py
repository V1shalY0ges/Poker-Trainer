from sqlalchemy import Column, Integer, String
from auth.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    '''
    This is the data model we will use inherited from the auth library to store the user id, username, email and password
    when we get a http response we ensure it is of this data model as part of our verification so it is a custom defined data structure
    '''

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

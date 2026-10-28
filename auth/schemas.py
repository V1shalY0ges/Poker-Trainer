from pydantic import BaseModel, EmailStr
'''
we have more models for users when the registers we have a data model to define the http response
when the user logs in we have a data model to define the http response
when a token is requested we use this data model for the token itself as it is a json dict and it has a defined token type as

'''
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    identifier: str  # username OR email
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

    class Config:
        orm_mode = True

class LoginRequest(BaseModel):
    identifier: str
    password: str

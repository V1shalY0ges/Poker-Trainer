from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
import string
import secrets

from auth.config import SECRET_KEY

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


ALGORITHM = "HS256" #encryption algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password) #applies the algorithm to the password to get a hashed password

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password) #checks if the password the user entered when
    # hashed matches the verified password

def generate_password(length=12):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"

    return "".join(
        secrets.choice(alphabet)
        for _ in range(length)
    )

def create_access_token(subject: str, expires_delta: timedelta | None = None):
    '''
    to create a JWT token all we do is record the time that it is created, create the expiry date which is set as 1 day,
    store the payload which is the ID of the
    user it is created for
    the data now and the expiry time
    it is then encoded using the algorithm and secret key and stored in local session storage
    '''
    now = datetime.utcnow()

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = { #create the token using a user ID, time now and the expiry time
        "sub": str(subject),
        "iat": now,
        "exp": expire
    }

    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM) #apply the encryption algorithm
    return encoded_jwt

def decode_access_token(token: str):
    '''
    take in the encrypted token and decode the token and return the contents to use for verification
    '''
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError: # add verification if token does not exist or unable to be decoded
        return None

# security.py
from itsdangerous import URLSafeTimedSerializer
from auth.config import SECRET_KEY

serialiser = URLSafeTimedSerializer(SECRET_KEY)

def generate_reset_token(email: str):
    return serialiser.dumps(email, salt="password-reset-salt")

def verify_reset_token(token: str, max_age=1800):  # 30 mins expiry
    try:
        email = serialiser.loads(
            token,
            salt="password-reset-salt",
            max_age=max_age
        )
        return email
    except Exception:
        return None

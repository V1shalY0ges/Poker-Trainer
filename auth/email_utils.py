# email_utils.py
import smtplib
from auth.config import EMAIL_ADDRESS, EMAIL_PASSWORD, FRONTEND_URL # from .env

def send_reset_email(to_email: str, token: str):
    """
    Sends a password reset email.
    """
    # token is just the token string
    reset_link = token

    subject = "Poker NEA Password Reset"
    body = f"Click the link below to reset your password:\n\n{reset_link}\n\nThis link expires in 15 minutes."

    # Create the raw email string manually
    message = f"""From: {EMAIL_ADDRESS}
To: {to_email}
Subject: {subject}

{body}
"""

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.sendmail(EMAIL_ADDRESS, [to_email], message)

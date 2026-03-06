"""
Email sending utility for LitePolis.
Supports sending emails via SMTP (e.g., maildev for testing).
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional


def get_smtp_config():
    """Get SMTP configuration from environment."""
    return {
        "host": os.getenv("SMTP_HOST", "maildev"),
        "port": int(os.getenv("SMTP_PORT", "25")),
        "user": os.getenv("SMTP_USER", ""),
        "password": os.getenv("SMTP_PASSWORD", ""),
        "from_email": os.getenv("SMTP_FROM_EMAIL", "noreply@polis.test"),
    }


def send_email(
    to_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None
) -> bool:
    """Send an email via SMTP.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Plain text body
        html_body: Optional HTML body
        
    Returns:
        True if sent successfully, False otherwise
    """
    config = get_smtp_config()
    
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = config["from_email"]
        msg["To"] = to_email
        msg["Subject"] = subject
        
        msg.attach(MIMEText(body, "plain"))
        if html_body:
            msg.attach(MIMEText(html_body, "html"))
        
        with smtplib.SMTP(config["host"], config["port"]) as server:
            if config["user"] and config["password"]:
                server.starttls()
                server.login(config["user"], config["password"])
            server.sendmail(config["from_email"], to_email, msg.as_string())
        
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def send_password_reset_email(email: str, reset_url: str) -> bool:
    """Send a password reset email.
    
    Args:
        email: Recipient email address
        reset_url: Full URL for password reset
        
    Returns:
        True if sent successfully, False otherwise
    """
    subject = "Reset your password"
    body = f"""Someone requested to reset your password.

To reset your password, visit the following link:

{reset_url}

If you did not request this reset, you can ignore this email.
"""
    return send_email(email, subject, body)

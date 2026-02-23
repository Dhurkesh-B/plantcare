import smtplib
from email.message import EmailMessage
from app.config import settings
import logging

logger = logging.getLogger(__name__)

def send_otp_email(to_email: str, otp_code: str):
    msg = EmailMessage()
    msg.set_content(f"Your login OTP for PlantCare AI is: {otp_code}\n\nThis code will expire in 5 minutes.")
    msg['Subject'] = 'PlantCare AI - Login OTP'
    msg['From'] = settings.SMTP_USERNAME
    msg['To'] = to_email

    try:
        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False

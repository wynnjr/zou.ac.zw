import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from datetime import datetime
from config import (
    EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD, EMAIL_USE_TLS,
    IT_SUPPORT_EMAIL, EMAIL_FROM_NAME
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.host = EMAIL_HOST
        self.port = EMAIL_PORT
        self.use_tls = EMAIL_USE_TLS
        self.user = EMAIL_USER
        self.password = EMAIL_PASSWORD
        self.from_name = EMAIL_FROM_NAME

    def _create_connection(self):
        """Create and return an authenticated SMTP connection."""
        try:
            server = smtplib.SMTP(self.host, self.port, timeout=30)
            server.ehlo()
            
            if self.use_tls:
                server.starttls()
                server.ehlo()
            
            server.login(self.user, self.password)
            return server
        except Exception as e:
            logger.error(f"Failed to create email connection: {e}")
            raise

    def send_escalation_email(self, user_name, user_phone, user_email, escalation_id, 
                            original_message, escalation_reason):
        """Send escalation email to IT support."""
        try:
            msg = MIMEMultipart()
            msg['From'] = formataddr((self.from_name, self.user))
            msg['To'] = IT_SUPPORT_EMAIL
            msg['Subject'] = f"Chatbot Escalation - {user_name} (ID: {escalation_id})"
            
            if user_email:
                msg['Reply-To'] = user_email

            # Create detailed email body
            body = f"""
CHATBOT ESCALATION ALERT
========================

User Details:
- Name: {user_name}
- Phone: {user_phone}
- Email: {user_email or 'Not provided'}
- Escalation ID: {escalation_id}

Escalation Reason:
{escalation_reason}

Original User Message:
{original_message}

Action Required:
Please review the conversation history and contact the user promptly.

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
System: ZOU IT Support Chatbot
"""

            msg.attach(MIMEText(body, 'plain'))
            
            with self._create_connection() as server:
                server.sendmail(self.user, IT_SUPPORT_EMAIL, msg.as_string())
            
            logger.info(f"Escalation email sent for user {user_name} (ID: {escalation_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send escalation email: {e}")
            return False

    def send_confirmation_email(self, to_email, user_name, escalation_id):
        """Send confirmation email to user."""
        try:
            msg = MIMEMultipart()
            msg['From'] = formataddr((self.from_name, self.user))
            msg['To'] = to_email
            msg['Subject'] = "Your Support Request Has Been Received - ZOU IT"

            body = f"""
Hello {user_name},

Your support request has been successfully submitted to our IT team.

Reference ID: {escalation_id}
Submitted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

What happens next:
1. Our IT team has been notified
2. Someone will review your conversation history
3. You'll be contacted shortly for assistance

If you need immediate assistance, you can also contact:
{IT_SUPPORT_EMAIL}

Thank you for your patience.

Best regards,
ZOU IT Support Team
"""

            msg.attach(MIMEText(body, 'plain'))
            
            with self._create_connection() as server:
                server.sendmail(self.user, to_email, msg.as_string())
            
            logger.info(f"Confirmation email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send confirmation email to {to_email}: {e}")
            return False

# Legacy functions for backward compatibility
def send_support_ticket(to_email, from_email, subject, body):
    """Legacy function - maintained for compatibility."""
    email_service = EmailService()
    try:
        msg = MIMEMultipart()
        msg['From'] = formataddr((email_service.from_name, email_service.user))
        msg['To'] = to_email
        msg['Subject'] = subject
        if from_email:
            msg['Reply-To'] = from_email
        
        msg.attach(MIMEText(body, 'plain'))
        
        with email_service._create_connection() as server:
            server.sendmail(email_service.user, to_email, msg.as_string())
        
        return True
    except Exception as e:
        logger.error(f"Legacy send_support_ticket failed: {e}")
        return False

def send_confirmation_email(to_email, subject, body):
    """Legacy function - maintained for compatibility."""
    email_service = EmailService()
    try:
        msg = MIMEMultipart()
        msg['From'] = formataddr((email_service.from_name, email_service.user))
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        with email_service._create_connection() as server:
            server.sendmail(email_service.user, to_email, msg.as_string())
        
        return True
    except Exception as e:
        logger.error(f"Legacy send_confirmation_email failed: {e}")
        return False

# Test function
def test_email_configuration():
    """Test the email configuration."""
    email_service = EmailService()
    try:
        with email_service._create_connection() as server:
            logger.info("Email configuration test successful!")
            return True
    except Exception as e:
        logger.error(f"Email configuration test failed: {e}")
        return False

if __name__ == "__main__":
    # Test the configuration
    if test_email_configuration():
        print("Email configuration is working!")
    else:
        print("Email configuration needs fixing!")
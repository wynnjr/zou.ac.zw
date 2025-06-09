import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from datetime import datetime
from contextlib import contextmanager
from config import (
    EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD, EMAIL_USE_TLS,
    IT_SUPPORT_EMAIL, EMAIL_FROM_NAME, EMAIL_TIMEOUT
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
        self.timeout = EMAIL_TIMEOUT

    @contextmanager
    def _create_connection(self):
        """Create and return an authenticated SMTP connection with proper cleanup."""
        server = None
        try:
            server = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
            server.ehlo()
            
            if self.use_tls:
                server.starttls()
                server.ehlo()
            
            server.login(self.user, self.password)
            logger.debug("SMTP connection established successfully")
            yield server
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication failed: {e}")
            raise
        except smtplib.SMTPConnectError as e:
            logger.error(f"SMTP Connection failed: {e}")
            raise
        except smtplib.SMTPException as e:
            logger.error(f"SMTP Error: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to create email connection: {e}")
            raise
        finally:
            if server:
                try:
                    server.quit()
                    logger.debug("SMTP connection closed properly")
                except Exception as e:
                    logger.warning(f"Error closing SMTP connection: {e}")

    def _create_base_message(self, to_email, subject, reply_to=None):
        """Create base email message with standard headers."""
        msg = MIMEMultipart()
        msg['From'] = formataddr((self.from_name, self.user))
        msg['To'] = to_email
        msg['Subject'] = subject
        msg['Date'] = formataddr((None, datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')))
        
        if reply_to:
            msg['Reply-To'] = reply_to
            
        return msg

    def send_escalation_email(self, user_name, user_phone, user_email, escalation_id, 
                            original_message, escalation_reason):
        """Send escalation email to IT support."""
        try:
            subject = f"🚨 Chatbot Escalation - {user_name} (ID: {escalation_id})"
            msg = self._create_base_message(IT_SUPPORT_EMAIL, subject, user_email)

            # Create detailed email body with better formatting
            body = f"""
CHATBOT ESCALATION ALERT
========================

📞 User Details:
   • Name: {user_name}
   • Phone: {user_phone}
   • Email: {user_email or 'Not provided'}
   • Escalation ID: {escalation_id}

⚠️  Escalation Reason:
   {escalation_reason}

💬 Original User Message:
   "{original_message}"

🔧 Action Required:
   Please review the conversation history and contact the user promptly.
   If user provided email, you can reply directly to this message.

⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🤖 System: ZOU IT Support Chatbot

---
This is an automated message from the ZOU IT Support Chatbot System.
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
            subject = "✅ Your Support Request Has Been Received - ZOU IT"
            msg = self._create_base_message(to_email, subject)

            body = f"""
Hello {user_name},

✅ Your support request has been successfully submitted to our IT team.

📋 Request Details:
   • Reference ID: {escalation_id}
   • Submitted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
   • Status: Pending Review

🔄 What happens next:
   1. Our IT team has been notified immediately
   2. Someone will review your conversation history
   3. You'll be contacted shortly for assistance
   4. Keep this reference ID for future inquiries

📞 Need immediate assistance?
   Contact us directly: {IT_SUPPORT_EMAIL}

⏱️  Expected Response Time: Within 2-4 business hours

Thank you for your patience. We're committed to resolving your issue quickly.

Best regards,
ZOU IT Support Team

---
Please do not reply to this email. If you need to provide additional information, 
please contact {IT_SUPPORT_EMAIL} directly with your reference ID: {escalation_id}
"""

            msg.attach(MIMEText(body, 'plain'))
            
            with self._create_connection() as server:
                server.sendmail(self.user, to_email, msg.as_string())
            
            logger.info(f"Confirmation email sent to {to_email} for escalation {escalation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send confirmation email to {to_email}: {e}")
            return False

    def send_resolution_notification(self, to_email, user_name, escalation_id, resolution_summary):
        """Send resolution notification to user when issue is resolved."""
        try:
            subject = f"✅ Issue Resolved - Reference ID: {escalation_id}"
            msg = self._create_base_message(to_email, subject)

            body = f"""
Hello {user_name},

✅ Great news! Your support request has been resolved.

📋 Resolution Details:
   • Reference ID: {escalation_id}
   • Status: Resolved
   • Resolved Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📝 Resolution Summary:
   {resolution_summary}

📞 Need further assistance?
   If you have any questions about this resolution or need additional help, 
   please contact us at {IT_SUPPORT_EMAIL} with your reference ID.

💬 Feedback:
   We'd love to hear about your experience! Please let us know how we did.

Thank you for using ZOU IT Support.

Best regards,
ZOU IT Support Team
"""

            msg.attach(MIMEText(body, 'plain'))
            
            with self._create_connection() as server:
                server.sendmail(self.user, to_email, msg.as_string())
            
            logger.info(f"Resolution notification sent to {to_email} for escalation {escalation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send resolution notification to {to_email}: {e}")
            return False

    def send_system_alert(self, alert_type, message, details=None):
        """Send system alerts to IT support."""
        try:
            subject = f"System Alert: {alert_type}"
            msg = self._create_base_message(IT_SUPPORT_EMAIL, subject)

            body = f"""
SYSTEM ALERT - ZOU IT CHATBOT
============================

🚨 Alert Type: {alert_type}
⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📝 Message:
   {message}
"""

            if details:
                body += f"""
Additional Details:
   {details}
"""

            body += """
---
This is an automated system alert from the ZOU IT Support Chatbot.
Please investigate and take appropriate action if necessary.
"""

            msg.attach(MIMEText(body, 'plain'))
            
            with self._create_connection() as server:
                server.sendmail(self.user, IT_SUPPORT_EMAIL, msg.as_string())
            
            logger.info(f"System alert sent: {alert_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send system alert: {e}")
            return False

    def test_connection(self):
        """Test the email configuration without sending a message."""
        try:
            with self._create_connection() as server:
                logger.info("Email configuration test successful!")
                return True
        except Exception as e:
            logger.error(f"Email configuration test failed: {e}")
            return False

# Legacy functions for backward compatibility
def send_support_ticket(to_email, from_email, subject, body):
    """Legacy function - maintained for compatibility."""
    email_service = EmailService()
    try:
        msg = email_service._create_base_message(to_email, subject, from_email)
        msg.attach(MIMEText(body, 'plain'))
        
        with email_service._create_connection() as server:
            server.sendmail(email_service.user, to_email, msg.as_string())
        
        logger.info(f"Legacy support ticket sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Legacy send_support_ticket failed: {e}")
        return False

def send_confirmation_email(to_email, subject, body):
    """Legacy function - maintained for compatibility."""
    email_service = EmailService()
    try:
        msg = email_service._create_base_message(to_email, subject)
        msg.attach(MIMEText(body, 'plain'))
        
        with email_service._create_connection() as server:
            server.sendmail(email_service.user, to_email, msg.as_string())
        
        logger.info(f"Legacy confirmation email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Legacy send_confirmation_email failed: {e}")
        return False

# Utility functions
def validate_email(email):
    """Basic email validation."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def format_phone_number(phone):
    """Format phone number for display."""
    if not phone:
        return "N/A"
    
    # Remove non-digits
    clean_phone = ''.join(filter(str.isdigit, str(phone)))
    
    # Format Zimbabwe numbers
    if len(clean_phone) == 12 and clean_phone.startswith('263'):
        return f"+{clean_phone[:3]} {clean_phone[3:5]} {clean_phone[5:8]} {clean_phone[8:]}"
    elif len(clean_phone) == 9:
        return f"+263 {clean_phone[:2]} {clean_phone[2:5]} {clean_phone[5:]}"
    
    return phone

# Test function
def test_email_configuration():
    """Test the email configuration."""
    email_service = EmailService()
    return email_service.test_connection()

def send_test_email(test_email=None):
    """Send a test email to verify configuration."""
    email_service = EmailService()
    test_recipient = test_email or IT_SUPPORT_EMAIL
    
    try:
        subject = "Email Configuration Test - ZOU IT Chatbot"
        msg = email_service._create_base_message(test_recipient, subject)
        
        body = f"""
EMAIL CONFIGURATION TEST
========================

✅ This is a test email from the ZOU IT Support Chatbot system.

📧 Configuration Details:
   • SMTP Host: {EMAIL_HOST}
   • SMTP Port: {EMAIL_PORT}
   • TLS Enabled: {EMAIL_USE_TLS}
   • From: {EMAIL_FROM_NAME} <{EMAIL_USER}>
   
⏰ Test Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

If you received this email, the configuration is working correctly!

---
ZOU IT Support Chatbot System
"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        with email_service._create_connection() as server:
            server.sendmail(email_service.user, test_recipient, msg.as_string())
        
        logger.info(f"Test email sent successfully to {test_recipient}")
        return True
        
    except Exception as e:
        logger.error(f"Test email failed: {e}")
        return False

if __name__ == "__main__":
    # Test the configuration
    print("Testing email configuration...")
    
    if test_email_configuration():
        print("✅ Email configuration is working!")
        
        # Optionally send a test email
        send_test = input("Send a test email? (y/n): ").lower().strip()
        if send_test == 'y':
            test_addr = input(f"Enter test email address (default: {IT_SUPPORT_EMAIL}): ").strip()
            if not test_addr:
                test_addr = IT_SUPPORT_EMAIL
            
            if send_test_email(test_addr):
                print(f"✅ Test email sent to {test_addr}")
            else:
                print("❌ Test email failed")
    else:
        print("❌ Email configuration needs fixing!")
        print("\nTroubleshooting:")
        print("1. Check your email credentials in config.py")
        print("2. Ensure 2-factor authentication is enabled and you're using an App Password")
        print("3. Verify SMTP settings for your email provider")
        print("4. Check network connectivity")
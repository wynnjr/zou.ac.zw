import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD, EMAIL_USE_TLS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_email_connection():
    """Test email server connection and authentication."""
    server = None
    try:
        logger.info(f"Testing connection to {EMAIL_HOST}:{EMAIL_PORT}")
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.set_debuglevel(1)  # Enable debug output
        
        # Send EHLO first
        logger.info("Sending EHLO...")
        server.ehlo()
        
        if EMAIL_USE_TLS:
            logger.info("Starting TLS...")
            server.starttls()
            # Send EHLO again after TLS
            logger.info("Sending EHLO after TLS...")
            server.ehlo()
        
        logger.info(f"Attempting login with user: {EMAIL_USER}")
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        
        logger.info("Email connection test successful!")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        logger.error("Check your email credentials and app password")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}")
        return False
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False
    finally:
        if server:
            try:
                server.quit()
            except:
                pass

def send_support_ticket(to_email, from_email, subject, body):
    """Send a support ticket email to IT support."""
    server = None
    try:
        logger.info(f"Preparing to send support ticket to {to_email}")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        msg['Reply-To'] = from_email
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to server
        logger.info(f"Connecting to {EMAIL_HOST}:{EMAIL_PORT}")
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.set_debuglevel(1)  # Enable debug output
        
        # Send EHLO first
        server.ehlo()
        
        if EMAIL_USE_TLS:
            logger.info("Starting TLS...")
            server.starttls()
            # Send EHLO again after TLS
            server.ehlo()
        
        # Login
        logger.info(f"Logging in as {EMAIL_USER}")
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        
        # Send message
        logger.info("Sending message...")
        text = msg.as_string()
        server.sendmail(EMAIL_USER, to_email, text)
        
        logger.info(f"Support ticket email sent successfully to {to_email}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        logger.error("Check your Gmail app password or enable 2FA")
        return False
    except smtplib.SMTPRecipientsRefused as e:
        logger.error(f"Recipient refused: {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to send support ticket email: {e}")
        return False
    finally:
        if server:
            try:
                server.quit()
            except:
                pass

def send_confirmation_email(to_email, subject, body):
    """Send a confirmation email to the user."""
    server = None
    try:
        logger.info(f"Preparing to send confirmation email to {to_email}")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to server
        logger.info(f"Connecting to {EMAIL_HOST}:{EMAIL_PORT}")
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.set_debuglevel(1)  # Enable debug output
        
        # Send EHLO first
        server.ehlo()
        
        if EMAIL_USE_TLS:
            logger.info("Starting TLS...")
            server.starttls()
            # Send EHLO again after TLS
            server.ehlo()
        
        # Login
        logger.info(f"Logging in as {EMAIL_USER}")
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        
        # Send message
        logger.info("Sending message...")
        text = msg.as_string()
        server.sendmail(EMAIL_USER, to_email, text)
        
        logger.info(f"Confirmation email sent successfully to {to_email}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        logger.error("Check your Gmail app password or enable 2FA")
        return False
    except smtplib.SMTPRecipientsRefused as e:
        logger.error(f"Recipient refused: {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to send confirmation email: {e}")
        return False
    finally:
        if server:
            try:
                server.quit()
            except:
                pass

# Test function you can run to debug
if __name__ == "__main__":
    print("Testing email configuration...")
    if test_email_connection():
        print("Connection test passed!")
        
        # Test sending an email
        test_result = send_confirmation_email(
            "wchimapaka@gmail.com",  # Replace with your email
            "Test Email",
            "This is a test email from your chatbot."
        )
        
        if test_result:
            print("Test email sent successfully!")
        else:
            print("Failed to send test email")
    else:
        print("Connection test failed!")
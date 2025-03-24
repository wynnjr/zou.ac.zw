from sqlalchemy import text
from models import SessionLocal, ChatMessage, ChatbotLog, User
import logging

class DatabaseHandler:
    """Handles all database interactions"""

    @staticmethod
    def add_user(phone, name=None, email=None):
        session = SessionLocal()
        try:
            user = User(phone=phone, name=name, email=email)
            session.add(user)
            session.commit()
            print(f"User {phone} added successfully.")
        except Exception as e:
            session.rollback()
            print(f"Database error (add_user): {e}")
        finally:
            session.close()

    @staticmethod
    def save_message(sender, message, is_response=False):
        session = SessionLocal()
        try:
            new_message = ChatMessage(sender=sender, message=message, is_response=is_response)
            session.add(new_message)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Database error (save_message): {e}")
        finally:
            session.close()

    @staticmethod
    def log_event(log_type, message):
        """Stores chatbot logs (errors, warnings, etc.)"""
        session = SessionLocal()
        try:
            log_entry = ChatbotLog(log_type=log_type, message=message)
            session.add(log_entry)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Database error (log_event): {e}")
        finally:
            session.close()

    @staticmethod
    def get_last_messages(limit=10):
        """Retrieve last N messages"""
        session = SessionLocal()
        messages = session.query(ChatMessage).order_by(ChatMessage.timestamp.desc()).limit(limit).all()
        session.close()
        return messages

    @staticmethod
    def get_support_assistants():
        """Fetch all users who are support assistants."""
        session = SessionLocal()
        try:
            query = text("SELECT id, phone_number, name FROM users WHERE is_assistant = TRUE;")
            assistants = session.execute(query).fetchall()  # Execute query

            logging.info(f"Raw Assistants Data: {assistants}")  # Debugging output

            return [{"id": a[0], "name": a[2], "phone_number": a[1]} for a in assistants]  # Correct indexing
        except Exception as e:
            logging.error(f"Database error: {e}")
            return []
        finally:
            session.close()
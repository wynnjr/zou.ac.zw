from models import SessionLocal, ChatMessage, ChatbotLog, User

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
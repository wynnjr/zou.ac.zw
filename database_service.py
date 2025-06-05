import logging
import psycopg2
from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, and_
from models import User, ChatMessage, Escalation, FAQ, UserState, ChatbotLog, Base
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://postgres:wynn@localhost/chatbot?options=-c search_path=public"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def create_tables():
    """Create all database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        return False

class DatabaseService:
    def __init__(self):
        # Ensure tables exist
        create_tables()
        # Database connection parameters
        self.db_params = {
            'host': 'localhost',
            'database': 'chatbot',
            'user': 'postgres',
            'password': 'wynn',
            'options': '-c search_path=public'
        }
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_params)
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def clean_phone_number(self, phone_number):
        """Convert phone numbers from scientific notation to standard format"""
        if phone_number is None:
            return None
            
        if isinstance(phone_number, float):
            phone_number = str(int(phone_number))
        elif isinstance(phone_number, str):
            if 'E+' in phone_number:
                phone_number = str(int(float(phone_number)))
            if '@c.us' in phone_number:
                phone_number = phone_number.split('@')[0]
        
        phone_number = ''.join(filter(str.isdigit, str(phone_number)))
        
        if len(phone_number) == 9 and not phone_number.startswith('263'):
            phone_number = '263' + phone_number
            
        return phone_number
    
    def get_user(self, phone_number):
        """Fetch user by phone number."""
        session = SessionLocal()
        try:
            clean_phone = self.clean_phone_number(phone_number)
            return session.query(User).filter_by(phone_number=clean_phone).first()
        finally:
            session.close()
    
    def create_user(self, phone_number):
        """Create a new user with session=True (awaiting name input)."""
        session = SessionLocal()
        try:
            clean_phone = self.clean_phone_number(phone_number)
            
            if session.query(User).filter_by(phone_number=clean_phone).first():
                raise ValueError(f"User {clean_phone} already exists")
                
            new_user = User(phone_number=clean_phone, session=True)
            session.add(new_user)
            session.commit()
            logger.info(f"Created user: {new_user.id} {clean_phone}")
            return new_user.id
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating user: {e}")
            raise
        finally:
            session.close()
    
    def update_user_name(self, user_id, name):
        """Update user name and disable session."""
        session = SessionLocal()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                logger.error(f"User {user_id} not found")
                return False
            user.name = name
            user.session = False
            session.commit()
            logger.info(f"Updated user {user_id}: name='{name}'")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating user name: {e}")
            return False
        finally:
            session.close()
    
    def update_user_email(self, user_id, email):
        """Update user email address."""
        session = SessionLocal()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                logger.error(f"User {user_id} not found")
                return False
            user.email = email
            session.commit()
            logger.info(f"Updated user {user_id}: email='{email}'")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating user email: {e}")
            return False
        finally:
            session.close()
    
    def get_user_state(self, user_id):
        """Get the current state of a user."""
        session = SessionLocal()
        try:
            return session.query(UserState).filter_by(user_id=user_id).first()
        except Exception as e:
            logger.error(f"Error getting user state: {e}")
            return None
        finally:
            session.close()
    
    def update_user_state(self, user_id, state, data=None):
        """Update or create a user state."""
        session = SessionLocal()
        try:
            user_state = session.query(UserState).filter_by(user_id=user_id).first()
            
            if state is None:
                if user_state:
                    session.delete(user_state)
                    session.commit()
                    logger.info(f"Deleted state for user {user_id}")
                return True
            
            if user_state:
                user_state.state = state
                user_state.data = data
                user_state.updated_at = datetime.utcnow()
            else:
                user_state = UserState(user_id=user_id, state=state, data=data)
                session.add(user_state)
                
            session.commit()
            logger.info(f"Updated state for user {user_id}: {state}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating user state: {e}")
            return False
        finally:
            session.close()
    
    def save_chat_message(self, user_id, message, is_response=False):
        """Save chat messages to the database and return the message ID."""
        session = SessionLocal()
        try:
            new_message = ChatMessage(user_id=user_id, message=message, is_response=is_response)
            session.add(new_message)
            session.commit()
            session.refresh(new_message)
            return new_message.id
        finally:
            session.close()
    
    def get_last_messages(self, user_id, limit=10):
        """Get the last X messages for a specific user."""
        session = SessionLocal()
        try:
            messages = (session.query(ChatMessage)
                        .filter_by(user_id=user_id)
                        .order_by(ChatMessage.timestamp.desc())
                        .limit(limit)
                        .all())
            return list(reversed(messages))
        finally:
            session.close()
    
    def get_user_message_count(self, user_id):
        """Get total message count for a user."""
        session = SessionLocal()
        try:
            count = session.query(ChatMessage).filter_by(user_id=user_id).count()
            return count
        except Exception as e:
            logger.error(f"Error getting user message count: {e}")
            return 0
        finally:
            session.close()
    
    def create_escalation(self, user_id, message):
        """Create a new escalation record with the message content."""
        session = SessionLocal()
        try:
            message_id = self.save_chat_message(user_id, message)
            escalation = Escalation(user_id=user_id, message_id=message_id)
            session.add(escalation)
            session.commit()
            session.refresh(escalation)
            return escalation.id
        finally:
            session.close()
    
    def get_escalation_message(self, escalation_id):
        """Get the original message content for an escalation."""
        session = SessionLocal()
        try:
            escalation = session.query(Escalation).filter_by(id=escalation_id).first()
            if not escalation:
                return "No message available for this escalation."
                
            message = session.query(ChatMessage).filter_by(id=escalation.message_id).first()
            if not message:
                return "Original message not found."
                
            return message.message
        except Exception as e:
            logger.error(f"Error retrieving escalation message: {e}")
            return "Error retrieving original message."
        finally:
            session.close()
    
    def update_escalation_status(self, escalation_id, status):
        """Update the status of an escalation."""
        session = SessionLocal()
        try:
            escalation = session.query(Escalation).filter_by(id=escalation_id).first()
            if escalation:
                escalation.status = status
                if status == 'resolved':
                    escalation.resolved_at = datetime.utcnow()
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    def get_support_assistants(self):
        """Fetch all support assistants."""
        session = SessionLocal()
        try:
            assistants = session.query(User).filter_by(is_assistant=True).all()
            return [
                {
                    "id": a.id,
                    "phone_number": self.clean_phone_number(a.phone_number),
                    "name": a.name,
                    "is_assistant": a.is_assistant
                }
                for a in assistants
            ]
        finally:
            session.close()
    
    def cleanup_completed_conversation(self, user_id):
        """Clean up completed conversation data."""
        session = SessionLocal()
        try:
            message_count = session.query(ChatMessage).filter_by(user_id=user_id).delete()
            escalation_count = session.query(Escalation).filter_by(user_id=user_id).delete()
            session.query(UserState).filter_by(user_id=user_id).delete()
            session.commit()
            logger.info(f"Cleaned up user {user_id}: {message_count} messages, {escalation_count} escalations")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error cleaning up conversation: {e}")
            return False
        finally:
            session.close()
    
    def cleanup_old_conversations(self, days_old=7):
        """Clean up old conversations."""
        session = SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            msg_count = session.query(ChatMessage).filter(ChatMessage.timestamp < cutoff_date).delete()
            esc_count = session.query(Escalation).filter(Escalation.created_at < cutoff_date).delete()
            session.commit()
            return msg_count, esc_count
        except Exception as e:
            session.rollback()
            logger.error(f"Error in cleanup_old_conversations: {e}")
            return 0, 0
        finally:
            session.close()
    
    def cleanup_resolved_escalations(self):
        """Clean up resolved escalations."""
        session = SessionLocal()
        try:
            count = session.query(Escalation).filter_by(status='resolved').delete()
            session.commit()
            return count
        except Exception as e:
            session.rollback()
            logger.error(f"Error cleaning up resolved escalations: {e}")
            return 0
        finally:
            session.close()
    
    def log_event(self, log_type, message):
        """Log an event to the database."""
        session = SessionLocal()
        try:
            new_log = ChatbotLog(
                log_type=log_type,
                message=message,
                timestamp=datetime.utcnow()
            )
            session.add(new_log)
            session.commit()
            session.refresh(new_log)
            return new_log.id
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to log event to database: {e}")
            return None
        finally:
            session.close()
    
    def get_last_user_messages(self, user_id, limit=3):
        """Get the last N messages from a specific user (not bot responses)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, user_id, message, is_response, timestamp 
                    FROM chat_messages 
                    WHERE user_id = %s AND is_response = FALSE
                    ORDER BY timestamp DESC 
                    LIMIT %s
                """, (user_id, limit))
                
                rows = cursor.fetchall()
                messages = []
                for row in rows:
                    msg = type('Message', (), {
                        'id': row[0],
                        'user_id': row[1], 
                        'message': row[2],
                        'is_response': row[3],
                        'timestamp': row[4]
                    })()
                    messages.append(msg)
                
                return messages
        except Exception as e:
            logging.error(f"Error getting last user messages: {e}")
            return []

    def get_user_failure_count(self, user_id):
        """Get the current failure count for a user."""
        session = SessionLocal()
        try:
            user_state = session.query(UserState).filter_by(user_id=user_id).first()
            if user_state and user_state.failure_count is not None:
                return user_state.failure_count
            return 0
        except Exception as e:
            logging.warning(f"Error getting user failure count: {e}")
            return 0
        finally:
            session.close()

    def set_user_failure_count(self, user_id, count):
        """Set the failure count for a user using SQLAlchemy consistently."""
        session = SessionLocal()
        try:
            user_state = session.query(UserState).filter_by(user_id=user_id).first()
            
            if user_state:
                user_state.failure_count = count
                user_state.updated_at = datetime.utcnow()
            else:
                # Create new user state with default state value
                user_state = UserState(
                    user_id=user_id,
                    state='default',  # Provide default state to avoid null constraint
                    failure_count=count
                )
                session.add(user_state)
                
            session.commit()
            logger.info(f"Set failure count for user {user_id}: {count}")
        except Exception as e:
            session.rollback()
            logging.warning(f"Error setting user failure count: {e}")
        finally:
            session.close()

    def cleanup_inactive_user_states(self):
        """Clean up user states for inactive users (older than 7 days)."""
        session = SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            deleted_count = session.query(UserState).filter(
                UserState.updated_at < cutoff_date
            ).delete()
            session.commit()
            logger.info(f"Cleaned up {deleted_count} inactive user states")
            return deleted_count
        except Exception as e:
            session.rollback()
            logging.error(f"Error cleaning up inactive user states: {e}")
            return 0
        finally:
            session.close()
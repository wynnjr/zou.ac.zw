# database_service.py
import logging
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, and_
from models import User, ChatMessage, Escalation, FAQ, Base
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = "postgresql://postgres:wynn@localhost/chatbot?options=-c search_path=public"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class DatabaseService:
    def get_or_create_user(self, phone_number):
        """Fetch user by phone number or create a new user if not found."""
        session = SessionLocal()
        try:
            # Clean the phone number before using it
            clean_phone = self.clean_phone_number(phone_number)
            user = session.query(User).filter_by(phone_number=clean_phone).first()
            if not user:
                user = User(phone_number=clean_phone, session=True)
                session.add(user)
                session.commit()
                session.refresh(user)
            return user.id, user.name
        finally:
            session.close()
    
    def get_user(self, phone_number):
        """Fetch user by phone number."""
        session = SessionLocal()
        try:
            # Clean the phone number before using it
            clean_phone = self.clean_phone_number(phone_number)
            return session.query(User).filter_by(phone_number=clean_phone).first()
        finally:
            session.close()
    
    def create_user(self, phone_number):
        """Create a new user with session=True (awaiting name input)."""
        session = SessionLocal()
        try:
            # Clean the phone number before using it
            clean_phone = self.clean_phone_number(phone_number)
            
            # Check if user exists first
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
            return list(reversed(messages))  # Return in chronological order
        finally:
            session.close()
    
    def find_faq_match(self, query):
        """Find a matching FAQ for the given query."""
        session = SessionLocal()
        try:
            return session.query(FAQ).filter(FAQ.question.ilike(f"%{query}%")).first()
        finally:
            session.close()
    
    def create_escalation(self, user_id, message):
        """Create a new escalation record with the message content."""
        session = SessionLocal()
        try:
            # First save the message and get its ID
            message_id = self.save_chat_message(user_id, message)
            
            # Create the escalation with the integer message_id
            escalation = Escalation(user_id=user_id, message_id=message_id)
            session.add(escalation)
            session.commit()
            session.refresh(escalation)
            return escalation.id
        finally:
            session.close()
    
    def create_escalation_with_id(self, user_id, message_id):
        """Create a new escalation record using an existing message ID."""
        session = SessionLocal()
        try:
            escalation = Escalation(user_id=user_id, message_id=message_id)
            session.add(escalation)
            session.commit()
            session.refresh(escalation)
            return escalation.id
        finally:
            session.close()
    
    def get_pending_escalations(self):
        """Get all pending escalations."""
        session = SessionLocal()
        try:
            return session.query(Escalation).filter_by(status="pending").all()
        finally:
            session.close()
    
    def update_escalation_status(self, escalation_id, status):
        """Update the status of an escalation."""
        session = SessionLocal()
        try:
            escalation = session.query(Escalation).filter_by(id=escalation_id).first()
            if escalation:
                escalation.status = status
                session.commit()
                return True
            return False
        finally:
            session.close()
            
    def clean_phone_number(self, phone_number):
        """Convert phone numbers from scientific notation (2.63E+11) to standard format"""
        if phone_number is None:
            return None
            
        # Convert scientific notation (2.63E+11) to standard format
        if isinstance(phone_number, float):
            phone_number = str(int(phone_number))
        elif isinstance(phone_number, str):
            if 'E+' in phone_number:  # Scientific notation
                phone_number = str(int(float(phone_number)))
            # Remove @c.us suffix if present
            if '@c.us' in phone_number:
                phone_number = phone_number.split('@')[0]
        
        # Ensure string type and remove non-digits
        phone_number = ''.join(filter(str.isdigit, str(phone_number)))
        
        # Add country code if missing (assuming Zimbabwe +263)
        if len(phone_number) == 9 and not phone_number.startswith('263'):
            phone_number = '263' + phone_number
            
        return phone_number
        
    def mark_as_assistant(self, user_id, is_assistant=True):
        """Mark/unmark a user as support assistant"""
        session = SessionLocal()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                user.is_assistant = is_assistant
                session.commit()
                logger.info(f"User {user_id} assistant status set to {is_assistant}")
                return True
            logger.warning(f"User {user_id} not found")
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating assistant status: {e}")
            return False
        finally:
            session.close()
            
    def get_support_assistants(self):
        """Fetch ALL assistants with proper data alignment"""
        session = SessionLocal()
        try:
            # Explicitly select only existing columns
            assistants = session.query(
                User.id,
                User.phone_number,
                User.name,
                User.is_assistant
            ).filter_by(is_assistant=True).all()

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

    def get_users_with_phone_numbers(self):
        """Fetch all users with their phone numbers."""
        session = SessionLocal()
        try:
            users = session.query(User).all()
            return [
                {
                    "id": u.id,
                    "name": u.name or "Unnamed User",
                    "phone_number": self.clean_phone_number(u.phone_number)
                }
                for u in users
            ]
        except Exception as e:
            logger.error(f"Database error: {e}")
            return []
        finally:
            session.close()
            
    def get_all_users(self):
        """Get all users from the database"""
        session = SessionLocal()
        try:
            return session.query(User).all()
        except Exception as e:
            logger.error(f"Error fetching all users: {e}")
            return []
        finally:
            session.close()

    def get_user_by_name(self, name):
        """Get a user by their name (case insensitive)"""
        session = SessionLocal()
        try:
            return session.query(User).filter(User.name.ilike(f"%{name}%")).first()
        except Exception as e:
            logger.error(f"Error fetching user by name: {e}")
            return None
        finally:
            session.close()

    def display_support_assistants(self):
        """Display that matches your SQL query exactly"""
        assistants = self.get_support_assistants()
        if not assistants:
            print("No assistants found!")
            return

        print("\n=== DATABASE VERIFIED ASSISTANTS ===")
        print(f"Found {len(assistants)} assistants:")
        print("-" * 60)
        for idx, a in enumerate(assistants, 1):
            print(f"{idx}. ID: {a['id']}")
            print(f"   Name: {a['name']}")
            print(f"   Phone: {a['phone_number']}")
            print(f"   Is Assistant: {'Yes' if a['is_assistant'] else 'No'}")
            print("-" * 60)
            
    def _clear_session_cache(self):
        engine.dispose()  # Reset connection pool

    def delete_all_users(self):
        """Delete ALL users and their related data (cascading delete)"""
        session = SessionLocal()
        try:
            user_count = session.query(User).count()
            session.query(User).delete()
            session.commit()
            logger.info(f"Deleted {user_count} users and their related data")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting users: {e}")
            return False
        finally:
            session.close()
            
    # ===== NEW CLEANUP METHODS =====
    
    def clear_user_chat_history(self, user_id):
        """Delete all chat messages for a specific user."""
        session = SessionLocal()
        try:
            deleted_count = session.query(ChatMessage).filter_by(user_id=user_id).delete()
            session.commit()
            logger.info(f"Cleared {deleted_count} chat messages for user {user_id}")
            return deleted_count
        except Exception as e:
            session.rollback()
            logger.error(f"Error clearing user chat history: {e}")
            return 0
        finally:
            session.close()
    
    def cleanup_user_data(self, user_id, preserve_user=True):
        """
        Clean up all user data including chat messages and escalations.
        If preserve_user is True, keep the user record but reset session state.
        """
        session = SessionLocal()
        try:
            # Delete all chat messages for this user
            message_count = session.query(ChatMessage).filter_by(user_id=user_id).delete()
            
            # Delete all escalations for this user
            escalation_count = session.query(Escalation).filter_by(user_id=user_id).delete()
            
            if not preserve_user:
                # Delete the user completely
                session.query(User).filter_by(id=user_id).delete()
            else:
                # Reset the user session but keep their record
                user = session.query(User).filter_by(id=user_id).first()
                if user:
                    user.session = True  # Reset to session mode
            
            session.commit()
            logger.info(f"Cleaned up user {user_id}: {message_count} messages, {escalation_count} escalations removed")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error cleaning up user data: {e}")
            return False
        finally:
            session.close()
    
    def cleanup_old_conversations(self, days_old=7):
        """Delete chat messages and escalations older than the specified number of days."""
        session = SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Delete old messages
            old_messages = session.query(ChatMessage).filter(ChatMessage.timestamp < cutoff_date).delete()
            
            # Delete old escalations
            old_escalations = session.query(Escalation).filter(Escalation.created_at < cutoff_date).delete()
            
            # Get inactive users (no messages for the past days_old days)
            inactive_users = session.query(User).filter(
                ~User.id.in_(
                    session.query(ChatMessage.user_id).filter(
                        ChatMessage.timestamp >= cutoff_date
                    ).distinct()
                )
            ).all()
            
            inactive_user_count = len(inactive_users)
            logger.info(f"Found {inactive_user_count} inactive users")
            
            session.commit()
            logger.info(f"Cleaned up {old_messages} old messages and {old_escalations} old escalations")
            return old_messages, old_escalations
        except Exception as e:
            session.rollback()
            logger.error(f"Error cleaning up old conversations: {e}")
            return 0, 0
        finally:
            session.close()
            
    def cleanup_resolved_escalations(self):
        """Delete escalations that have been resolved."""
        session = SessionLocal()
        try:
            resolved_count = session.query(Escalation).filter_by(status="resolved").delete()
            session.commit()
            logger.info(f"Cleaned up {resolved_count} resolved escalations")
            return resolved_count
        except Exception as e:
            session.rollback()
            logger.error(f"Error cleaning up resolved escalations: {e}")
            return 0
        finally:
            session.close()
            
    def cleanup_completed_conversation(self, user_id):
        """
        Cleanup after conversation completion - reset user to initial state
        but preserve the user record with their name and phone number.
        """
        session = SessionLocal()
        try:
            # Delete chat messages
            msg_count = session.query(ChatMessage).filter_by(user_id=user_id).delete()
            
            # Mark any escalations as resolved
            esc_count = session.query(Escalation).filter(
                and_(Escalation.user_id == user_id, Escalation.status == "pending")
            ).update({"status": "resolved"})
            
            session.commit()
            logger.info(f"Completed conversation cleanup for user {user_id}: {msg_count} messages cleared, {esc_count} escalations resolved")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error during conversation cleanup: {e}")
            return False
        finally:
            session.close()
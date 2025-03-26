import datetime
import logging
from sqlalchemy.orm import sessionmaker, joinedload
from sqlalchemy import create_engine
from models import User, ChatMessage, Escalation, FAQ
from sqlalchemy.sql import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = "postgresql://postgres:wynn@localhost/chatbot"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class DatabaseService:
    def get_or_create_user(self, phone_number):
        """Fetch user by phone number or create a new user if not found."""
        session = SessionLocal()
        try:
            user = session.query(User).filter_by(phone_number=phone_number).first()
            if not user:
                user = User(phone_number=phone_number, session=True)
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
            return session.query(User).filter_by(phone_number=phone_number).first()
        finally:
            session.close()
    
    def create_user(self, phone_number):
        """Create a new user with session=True (awaiting name input)."""
        session = SessionLocal()
        try:
            # Check if user exists first
            if session.query(User).filter_by(phone_number=phone_number).first():
                raise ValueError(f"User {phone_number} already exists")
                
            new_user = User(phone_number=phone_number, session=True)
            session.add(new_user)
            session.commit()
            logger.info(f"Created user: {new_user.id} {phone_number}")
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
    
    def get_last_messages(self, user_id, limit=5):
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
            
    @staticmethod
    def clean_phone_number(phone_number):
        """Remove @c.us suffix from WhatsApp numbers"""
        if phone_number and '@c.us' in phone_number:
            return phone_number.split('@c.us')[0]
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
        """Fetch support assistants directly from escalations table with all available data"""
        session = SessionLocal()
        try:
            # Get all escalations with their associated message and user data
            escalations = session.query(Escalation).options(
                joinedload(Escalation.user),
                joinedload(Escalation.message)
            ).all()
            
            assistants = []
            
            for esc in escalations:
                if esc.user:
                    # Get name from escalation (user_text) or user table
                    name = getattr(esc, 'user_text', None) or esc.user.name or "Unnamed Assistant"
                    
                    # Get phone number from user table
                    phone = self.clean_phone_number(esc.user.phone_number)
                    
                    # Get message text if available
                    message_text = esc.message.message if esc.message else "No message content"
                    
                    assistants.append({
                        "user_id": esc.user.id,
                        "name": name,
                        "phone_number": phone,
                        "escalation_id": esc.id,
                        "status": esc.status,
                        "created_at": esc.created_at,
                        "message_text": message_text
                    })
            
            return assistants
        except Exception as e:
            logger.error(f"Error fetching assistants from escalations: {e}")
            return []
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

    def display_support_assistants(self):
        """Display all support assistants found in escalations with detailed info"""
        assistants = self.get_support_assistants()
        if assistants:
            print("\n=== Support Assistants from Escalations ===")
            print(f"Found {len(assistants)} assistants in escalations:")
            print("-" * 80)
            for idx, assistant in enumerate(assistants, 1):
                print(f"{idx}. User ID: {assistant['user_id']}")
                print(f"   Name: {assistant['name']}")
                print(f"   Phone: {assistant['phone_number']}")
                print(f"   Escalation ID: {assistant['escalation_id']}")
                print(f"   Status: {assistant['status']}")
                print(f"   Created: {assistant['created_at']}")
                print(f"   Last Message: {assistant['message_text'][:50]}...")
                print("-" * 80)
        else:
            print("\nNo support assistants found in escalations table.")
            
            # Debugging output to help diagnose why no assistants are found
            session = SessionLocal()
            try:
                escalation_count = session.query(Escalation).count()
                user_count = session.query(User).count()
                print(f"\nDebug Info:")
                print(f"Total escalations in database: {escalation_count}")
                print(f"Total users in database: {user_count}")
                
                if escalation_count > 0:
                    print("\nSample escalation data:")
                    sample = session.query(Escalation).first()
                    print(f"Escalation ID: {sample.id}")
                    print(f"User ID: {sample.user_id}")
                    print(f"Status: {sample.status}")
            finally:
                session.close()


    def display_users_with_phone_numbers(self):
        """Fetch and display all users with phone numbers."""
        users = self.get_users_with_phone_numbers()
        if users:
            print("Here are all users:")
            for user in users:
                print(f"ID: {user['id']}, Name: {user['name']}, Phone: {user['phone_number']}")
        else:
            print("No users found in database.")

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

# Test the code
if __name__ == "__main__":
    db_service = DatabaseService()
    db_service.display_support_assistants()
    
    # Display assistants from escalations
    print("=== Support Assistants from Escalations ===")
    db_service.display_support_assistants()
    
    # Display all users
    print("\n=== All Users ===")
    db_service.display_users_with_phone_numbers()
    
    # Example: Delete all users (uncomment to use)
    # print("\nWARNING: This will delete ALL users!")
    # if input("Are you sure? (yes/no): ").lower() == 'yes':
    #     db_service.delete_all_users()
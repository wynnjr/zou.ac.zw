import logging
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import User, ChatMessage, Escalation, FAQ

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
            new_user = User(phone_number=phone_number, session=True)
            session.add(new_user)
            session.commit()
            return new_user.id
        finally:
            session.close()
    
    def update_user_name(self, user_id, name):
        """Update user name and disable session."""
        session = SessionLocal()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                user.name = name
                user.session = False
                session.commit()
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
        """Create a new escalation record with the message content.
        
        First saves the message to the database and then creates an escalation
        record using the message ID.
        """
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
    
    # Alternative implementation that expects an existing message_id
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
            
    def get_support_assistants(self):
        """Fetch all support assistants from the users table."""
        try:
            self.cursor.execute("SELECT name, phone_number FROM users WHERE is_assistant = TRUE;")
            results = self.cursor.fetchall()
            logging.info(f"Raw assistant query results: {results}")  # Debug log
            return [{"name": row[0], "phone_number": row[1]} for row in results] if results else []
        except Exception as e:
            logging.error(f"Database error: {e}")
            return []



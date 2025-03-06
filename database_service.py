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
        """Save chat messages to the database."""
        session = SessionLocal()
        try:
            new_message = ChatMessage(user_id=user_id, message=message, is_response=is_response)
            session.add(new_message)
            session.commit()
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
    
    def create_escalation(self, user_text, message_text):
        """Create an escalation using the actual message ID instead of message text."""
        session = SessionLocal()
        try:
            # Fetch the latest message ID for this user
            last_message = (session.query(ChatMessage)
                            .filter_by(user_text=user_text)
                            .order_by(ChatMessage.timestamp.desc())
                            .first())

            if not last_message:
                raise ValueError("No previous messages found for user.")

            escalation = Escalation(user_text=user_text, message_text=last_message.text, status="pending")
            session.add(escalation)
            session.commit()
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

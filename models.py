from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, UTC
import logging
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Database Configuration
DATABASE_URL = "postgresql://postgres:wynn@localhost/chatbot"
Base = declarative_base()

# Models
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    phone_number = Column(String, unique=True, nullable=False)
    name = Column(String)
    session = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_assistant = Column(Boolean, default=False)

class ChatMessage(Base):
    """Stores WhatsApp messages and AI responses"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC))  # FIXED
    is_response = Column(Boolean, default=False)
    user = relationship("User", backref="messages", cascade="all, delete")

class FAQ(Base):
    """Stores frequently asked questions and their answers"""
    __tablename__ = "faqs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(Text, unique=True, nullable=False)
    answer = Column(Text, nullable=False)

class Escalation(Base):
    """Tracks unresolved issues for human intervention"""
    __tablename__ = "escalations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    message_id = Column(Integer, ForeignKey('chat_messages.id', ondelete='CASCADE'), nullable=False)
    status = Column(String, default="pending")  # "pending", "resolved"
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))  # FIXED
    
    user = relationship("User", backref="escalations", cascade="all, delete")
    message = relationship("ChatMessage", backref="escalations", cascade="all, delete")

class ChatbotLog(Base):
    """Logs chatbot events and errors"""
    __tablename__ = "chatbot_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_type = Column(String, nullable=False)  # "error", "info", "warning"
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC))  # FIXED

# Database Connection
try:
    engine = create_engine(DATABASE_URL, echo=True)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    
    # Ensure all tables are created
    Base.metadata.create_all(engine)
    logging.info("Database tables created successfully.")
except Exception as e:
    logging.error(f"Error initializing the database: {e}")

# Session Handling Functions
def get_db():
    """Yield a new database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_user(phone_number, name=None):
    """Create a new user with an active session."""
    db = SessionLocal()
    try:
        new_user = User(phone_number=phone_number, name=name)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logging.info(f"User {phone_number} added successfully.")
        return new_user
    except Exception as e:
        db.rollback()
        logging.error(f"Error adding user {phone_number}: {e}")
    finally:
        db.close()

def update_user_session(phone_number, session_status):
    """Update the session status of a user."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.phone_number == phone_number).first()
        if user:
            user.session = session_status
            db.commit()
            logging.info(f"User {phone_number} session updated to {session_status}.")
        else:
            logging.warning(f"User {phone_number} not found.")
    except Exception as e:
        db.rollback()
        logging.error(f"Error updating user session: {e}")
    finally:
        db.close()

# Testing (Optional)
if __name__ == "__main__":
    create_user("1234567890", "wynn")
    update_user_session("1234567890", False)  # Set session to False

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, UTC

# Database Configuration
Base = declarative_base()

# Models
class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'public'}
    
    id = Column(Integer, primary_key=True)
    phone_number = Column(String, unique=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    session = Column(Boolean)
    is_assistant = Column(Boolean)

class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    __table_args__ = {'schema': 'public'}  # Explicit schema
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('public.users.id'))  # Fully qualified FK
    message = Column(String)
    is_response = Column(Boolean)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Add relationship to the User model
    user = relationship("User", backref="messages")

class FAQ(Base):
    """Stores frequently asked questions and their answers"""
    __tablename__ = "faqs"
    __table_args__ = {'schema': 'public'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(Text, unique=True, nullable=False)
    answer = Column(Text, nullable=False)

class Escalation(Base):
    __tablename__ = 'escalations'
    __table_args__ = {'schema': 'public'}  # Explicit schema
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('public.users.id'))  # Fully qualified FK
    message_id = Column(Integer, ForeignKey('public.chat_messages.id'))
    status = Column(String, default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", backref="escalations", cascade="all, delete")
    message = relationship("ChatMessage", backref="escalations", cascade="all, delete")

class ChatbotLog(Base):
    """Logs chatbot events and errors"""
    __tablename__ = "chatbot_logs"
    __table_args__ = {'schema': 'public'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_type = Column(String, nullable=False)  # "error", "info", "warning"
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC))
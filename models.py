from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime, Index
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'public'}
    
    id = Column(Integer, primary_key=True)
    phone_number = Column(String(50), unique=True, nullable=False)
    name = Column(String(100))
    email = Column(String(100))
    is_assistant = Column(Boolean, default=False)
    session = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    escalations = relationship("Escalation", back_populates="user", cascade="all, delete-orphan")
    state = relationship("UserState", back_populates="user", uselist=False, cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    __table_args__ = (
        Index('idx_chat_messages_user_id', 'user_id'),
        Index('idx_chat_messages_timestamp', 'timestamp'),
        {'schema': 'public'}
    )
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('public.users.id', ondelete='CASCADE'), nullable=False)
    message = Column(Text, nullable=False)
    is_response = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="messages")

class Escalation(Base):
    __tablename__ = 'escalations'
    __table_args__ = (
        Index('idx_escalations_user_id', 'user_id'),
        Index('idx_escalations_status', 'status'),
        {'schema': 'public'}
    )
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('public.users.id', ondelete='CASCADE'), nullable=False)
    message_id = Column(Integer, ForeignKey('public.chat_messages.id', ondelete='SET NULL'))
    status = Column(String(20), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    
    user = relationship("User", back_populates="escalations")
    message = relationship("ChatMessage", backref="escalations")

class FAQ(Base):
    __tablename__ = 'faqs'
    __table_args__ = (
        Index('idx_faqs_question', 'question'),
        Index('idx_faqs_category', 'category'),
        {'schema': 'public'}
    )
    
    id = Column(Integer, primary_key=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserState(Base):
    __tablename__ = 'user_states'
    __table_args__ = (
        Index('idx_user_states_user_id', 'user_id'),
        Index('idx_user_states_state', 'state'),
        {'schema': 'public'}
    )
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('public.users.id', ondelete='CASCADE'), unique=True, nullable=False)
    state = Column(String(50), nullable=True)  # Made nullable to fix the constraint issue
    data = Column(Text)
    failure_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="state")

class ChatbotLog(Base):
    __tablename__ = "chatbot_logs"
    __table_args__ = {'schema': 'public'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_type = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
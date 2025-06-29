"""
Learning session models for the Smart Learning with Personalized AI Tutor application
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import json
from app.models.base import Base

class LearningSession(Base):
    """Learning session model"""
    __tablename__ = 'learning_sessions'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    subject = Column(String(64), nullable=False)
    topic = Column(String(128), nullable=False)
    difficulty_level = Column(String(32))  # beginner, intermediate, advanced
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    duration = Column(Integer)  # in seconds
    status = Column(String(32), default='active')  # active, completed, paused
    
    # Relationships
    user = relationship("User", back_populates="learning_sessions")
    conversations = relationship("Conversation", back_populates="learning_session", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="learning_session", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert session to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subject': self.subject,
            'topic': self.topic,
            'difficulty_level': self.difficulty_level,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'status': self.status
        }

class Conversation(Base):
    """Conversation model for learning sessions"""
    __tablename__ = 'conversations'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    learning_session_id = Column(Integer, ForeignKey('learning_sessions.id'), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    learning_session = relationship("LearningSession", back_populates="conversations")
    
    def to_dict(self):
        """Convert conversation to dictionary"""
        return {
            'id': self.id,
            'learning_session_id': self.learning_session_id,
            'message': self.message,
            'response': self.response,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class Assessment(Base):
    """Assessment model for learning sessions"""
    __tablename__ = 'assessments'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    learning_session_id = Column(Integer, ForeignKey('learning_sessions.id'), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text)
    is_correct = Column(Integer)  # -1: not answered, 0: incorrect, 1: correct
    score = Column(Float)
    feedback = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    learning_session = relationship("LearningSession", back_populates="assessments")
    
    def to_dict(self):
        """Convert assessment to dictionary"""
        return {
            'id': self.id,
            'learning_session_id': self.learning_session_id,
            'question': self.question,
            'answer': self.answer,
            'is_correct': self.is_correct,
            'score': self.score,
            'feedback': self.feedback,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        } 
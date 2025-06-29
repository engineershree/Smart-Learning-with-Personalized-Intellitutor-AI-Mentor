"""
Learning models for the Smart Learning with Personalized AI Tutor application
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum as SQLEnum, Text, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import json

Base = declarative_base()

class CommunicationType(Enum):
    """Enum for communication types"""
    TEXT = "text"
    VOICE = "voice"
    VIDEO = "video"

class LearningSession(Base):
    """Learning session model"""
    __tablename__ = 'learning_sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    subject = Column(String(128), nullable=False)
    topic = Column(String(128), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Session metadata
    difficulty_level = Column(Integer, default=1)  # 1-10 scale
    learning_objectives = Column(Text)  # Stored as JSON string
    session_summary = Column(Text)
    
    # Blockchain transaction hash for session verification
    blockchain_tx_hash = Column(String(66))
    
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
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'is_active': self.is_active,
            'difficulty_level': self.difficulty_level,
            'learning_objectives': json.loads(self.learning_objectives) if self.learning_objectives else None,
            'session_summary': self.session_summary,
            'blockchain_tx_hash': self.blockchain_tx_hash
        }

class Conversation(Base):
    """Conversation model for tracking interactions"""
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True)
    learning_session_id = Column(Integer, ForeignKey('learning_sessions.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    communication_type = Column(SQLEnum(CommunicationType), default=CommunicationType.TEXT)
    
    # For text conversations
    user_message = Column(Text)
    ai_response = Column(Text)
    
    # For voice/video conversations
    media_url = Column(String(255))
    duration = Column(Integer)  # in seconds
    
    # Metadata for personalization
    sentiment_score = Column(Float)  # -1.0 to 1.0
    topics_covered = Column(Text)  # Stored as JSON string
    user_engagement_score = Column(Float)  # 0.0 to 1.0
    
    # Blockchain hash for verification
    content_hash = Column(String(64))
    
    # Relationships
    learning_session = relationship("LearningSession", back_populates="conversations")
    
    def to_dict(self):
        """Convert conversation to dictionary"""
        return {
            'id': self.id,
            'learning_session_id': self.learning_session_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'communication_type': self.communication_type.value,
            'user_message': self.user_message,
            'ai_response': self.ai_response,
            'media_url': self.media_url,
            'duration': self.duration,
            'sentiment_score': self.sentiment_score,
            'topics_covered': json.loads(self.topics_covered) if self.topics_covered else None,
            'user_engagement_score': self.user_engagement_score,
            'content_hash': self.content_hash
        }

class Assessment(Base):
    """Assessment model for tracking learning progress"""
    __tablename__ = 'assessments'
    
    id = Column(Integer, primary_key=True)
    learning_session_id = Column(Integer, ForeignKey('learning_sessions.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    assessment_type = Column(String(64))  # quiz, test, project, etc.
    title = Column(String(128))
    description = Column(Text)
    
    # Assessment data
    questions = Column(Text)  # Stored as JSON string
    answers = Column(Text)  # Stored as JSON string
    score = Column(Float)
    max_score = Column(Float)
    
    # Feedback and analysis
    feedback = Column(Text)
    strengths = Column(Text)  # Stored as JSON string
    areas_for_improvement = Column(Text)  # Stored as JSON string
    
    # Relationships
    learning_session = relationship("LearningSession", back_populates="assessments")
    
    def to_dict(self):
        """Convert assessment to dictionary"""
        return {
            'id': self.id,
            'learning_session_id': self.learning_session_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'assessment_type': self.assessment_type,
            'title': self.title,
            'description': self.description,
            'questions': json.loads(self.questions) if self.questions else None,
            'answers': json.loads(self.answers) if self.answers else None,
            'score': self.score,
            'max_score': self.max_score,
            'feedback': self.feedback,
            'strengths': json.loads(self.strengths) if self.strengths else None,
            'areas_for_improvement': json.loads(self.areas_for_improvement) if self.areas_for_improvement else None
        } 
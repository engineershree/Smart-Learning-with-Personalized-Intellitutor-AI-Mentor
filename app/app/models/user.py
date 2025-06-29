"""
User model for the Smart Learning with Personalized AI Tutor application
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import json
from app.models.base import Base
from werkzeug.security import generate_password_hash, check_password_hash

class User(Base):
    """User model for authentication and profile management"""
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256))
    first_name = Column(String(64))
    last_name = Column(String(64))
    learning_style = Column(String(32))  # visual, auditory, reading/writing, kinesthetic
    preferred_subjects = Column(Text)  # JSON array of subjects
    difficulty_preference = Column(String(32))  # beginner, intermediate, advanced, adaptive
    preferred_ai_model_id = Column(Integer, ForeignKey('ai_models.id'))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    preferences = Column(Text)  # Store JSON string of user preferences
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    learning_sessions = relationship("LearningSession", back_populates="user")
    preferred_ai_model = relationship("AIModel")
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'learning_style': self.learning_style,
            'preferred_subjects': json.loads(self.preferred_subjects) if self.preferred_subjects else [],
            'difficulty_preference': self.difficulty_preference,
            'preferred_ai_model_id': self.preferred_ai_model_id,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'preferences': self.preferences,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

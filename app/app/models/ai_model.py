"""
AI Model definitions for the Smart Learning with Personalized AI Tutor application
"""

from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum as SQLEnum, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import json
from app.models.base import Base

class AIModelType(Enum):
    """Enum for AI model types"""
    GPT = "gpt"
    BERT = "bert"
    CUSTOM = "custom"
    LLAMA = "llama"
    CLAUDE = "claude"

class AIModel(Base):
    """AI Model for personalized tutoring"""
    __tablename__ = 'ai_models'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    model_type = Column(SQLEnum(AIModelType), nullable=False)
    description = Column(Text)
    capabilities = Column(Text)  # Stored as JSON string
    parameters = Column(Text)  # Stored as JSON string
    api_endpoint = Column(String(255))
    api_key_required = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'model_type': self.model_type.value,
            'description': self.description,
            'capabilities': json.loads(self.capabilities) if self.capabilities else None,
            'parameters': json.loads(self.parameters) if self.parameters else None,
            'api_endpoint': self.api_endpoint,
            'api_key_required': self.api_key_required,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class UserAIModelPreference(Base):
    """User's AI Model preferences"""
    __tablename__ = 'user_ai_model_preferences'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    ai_model_id = Column(Integer, nullable=False)
    is_default = Column(Boolean, default=False)
    api_key = Column(String(256))  # Encrypted API key if user provides their own
    custom_parameters = Column(Text)  # User's custom parameters as JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert preference to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'ai_model_id': self.ai_model_id,
            'is_default': self.is_default,
            'has_api_key': bool(self.api_key),
            'custom_parameters': json.loads(self.custom_parameters) if self.custom_parameters else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 
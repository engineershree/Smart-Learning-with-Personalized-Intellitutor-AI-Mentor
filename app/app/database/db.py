"""
Database configuration for the Smart Learning with Personalized AI Tutor application
"""

from flask import current_app
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from app.models.base import Base
from app.models.user import User
from app.models.ai_model import AIModel, AIModelType
from app.models.learning_session import LearningSession
from werkzeug.security import generate_password_hash
import json

# Create database engine
def get_engine():
    return create_engine(current_app.config['DATABASE_URI'])

# Create database session
def get_db_session():
    engine = get_engine()
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return scoped_session(session_factory)

# Initialize database
def init_db():
    """Initialize the database with tables"""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    current_app.logger.info("Database tables created")

# Add sample data for development
def add_sample_data():
    """Add sample data for development"""
    # Skip if not in development or data already exists
    if not current_app.config.get('DEBUG', False):
        return
    
    db_session = get_db_session()
    
    # Check if data already exists
    if db_session.query(User).first():
        db_session.remove()
        return
    
    try:
        # Add sample AI models
        ai_models = [
            AIModel(
                name="GPT-4 Turbo",
                model_type=AIModelType.GPT,
                description="Advanced language model with strong reasoning capabilities",
                api_endpoint="https://api.openai.com/v1/chat/completions",
                api_key_required=True,
                is_active=True
            ),
            AIModel(
                name="Claude 3",
                model_type=AIModelType.CLAUDE,
                description="Anthropic's flagship AI assistant with advanced reasoning",
                api_endpoint="https://api.anthropic.com/v1/complete",
                api_key_required=True,
                is_active=True
            )
        ]
        
        for model in ai_models:
            db_session.add(model)
        db_session.flush()  # Flush to get model IDs
        
        # Add sample users
        users = [
            User(
                username="student1",
                email="student1@example.com",
                password_hash=generate_password_hash("password123"),
                first_name="Student",
                last_name="One",
                learning_style="visual",
                preferred_subjects=json.dumps(["Math", "Science", "Computer Science"]),
                difficulty_preference="adaptive",
                preferred_ai_model_id=1,
                is_active=True,
                is_admin=False
            ),
            User(
                username="admin",
                email="admin@example.com",
                password_hash=generate_password_hash("admin123"),
                first_name="Admin",
                last_name="User",
                is_active=True,
                is_admin=True,
                preferred_ai_model_id=1
            )
        ]
        
        for user in users:
            db_session.add(user)
        
        # Commit changes
        db_session.commit()
        current_app.logger.info("Sample data added successfully")
    except Exception as e:
        db_session.rollback()
        current_app.logger.error(f"Error adding sample data: {str(e)}")
    finally:
        db_session.remove() 
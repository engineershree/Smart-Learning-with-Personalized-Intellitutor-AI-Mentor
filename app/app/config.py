"""
Configuration settings for the Smart Learning with Personalized AI Tutor application
"""

import os
from dotenv import load_dotenv
from datetime import timedelta

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration"""
    # Application
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-do-not-use-in-production'
    DEBUG = False
    TESTING = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-dev-key-do-not-use-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES = 30 * 24 * 60 * 60  # 30 days
    
    # Blockchain (disabled for development)
    MOCK_BLOCKCHAIN = True
    WEB3_PROVIDER_URI = None
    CONTRACT_ADDRESS = None
    
    # File upload
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    
    # AI Models
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_API_ENDPOINT = os.environ.get('OPENAI_API_ENDPOINT') or 'https://api.openai.com/v1/chat/completions'
    
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
    ANTHROPIC_API_ENDPOINT = os.environ.get('ANTHROPIC_API_ENDPOINT') or 'https://api.anthropic.com/v1/complete'
    
    LLAMA_API_KEY = os.environ.get('LLAMA_API_KEY')
    LLAMA_API_ENDPOINT = os.environ.get('LLAMA_API_ENDPOINT')
    
    # Default AI model (can be overridden by user preferences)
    DEFAULT_AI_MODEL = 'gpt'
    
    # Voice and speech settings
    VOICE_RECOGNITION_SERVICE = os.environ.get('VOICE_RECOGNITION_SERVICE') or 'google'
    TEXT_TO_SPEECH_SERVICE = os.environ.get('TEXT_TO_SPEECH_SERVICE') or 'gtts'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    MOCK_BLOCKCHAIN = True

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    MOCK_BLOCKCHAIN = True
    JWT_ACCESS_TOKEN_EXPIRES = 60  # 1 minute
    JWT_REFRESH_TOKEN_EXPIRES = 60 * 60  # 1 hour

class ProductionConfig(Config):
    """Production configuration"""
    MOCK_BLOCKCHAIN = True  # Disable blockchain for now
    
    @classmethod
    def init_app(cls, app):
        assert cls.SECRET_KEY, 'SECRET_KEY environment variable is not set'
        assert cls.JWT_SECRET_KEY, 'JWT_SECRET_KEY environment variable is not set'
        
        # SSL/TLS settings for production
        if os.environ.get('ENABLE_HTTPS'):
            app.config['PREFERRED_URL_SCHEME'] = 'https'

    # In production, use stronger security settings
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_CSRF_PROTECT = True
    
    # Database configuration
    DATABASE_URI = SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI or 'sqlite:///app.db'
    
    # AI model configuration
    NLP_MODEL_PATH = 'models/nlp_model'
    PERSONALIZATION_MODEL_PATH = 'models/personalization_model'
    
    # File upload configuration
    UPLOAD_FOLDER = UPLOAD_FOLDER or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
    MAX_CONTENT_LENGTH = MAX_CONTENT_LENGTH or 16 * 1024 * 1024  # 16 MB max upload size

    # AI model configuration
    OPENAI_API_KEY = OPENAI_API_KEY
    OPENAI_API_ENDPOINT = OPENAI_API_ENDPOINT
    
    ANTHROPIC_API_KEY = ANTHROPIC_API_KEY
    ANTHROPIC_API_ENDPOINT = ANTHROPIC_API_ENDPOINT
    
    LLAMA_API_KEY = LLAMA_API_KEY
    LLAMA_API_ENDPOINT = LLAMA_API_ENDPOINT
    
    # Default AI model (can be overridden by user preferences)
    DEFAULT_AI_MODEL = DEFAULT_AI_MODEL
    
    # Voice and speech settings
    VOICE_RECOGNITION_SERVICE = VOICE_RECOGNITION_SERVICE
    TEXT_TO_SPEECH_SERVICE = TEXT_TO_SPEECH_SERVICE 
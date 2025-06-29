"""
App initialization module for the Smart Learning with Personalized AI Tutor
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

def create_app(config_name=None):
    """
    Flask application factory
    
    Args:
        config_name (str): Configuration environment (development, testing, production)
        
    Returns:
        Flask application instance
    """
    # Create Flask app
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    
    # Load environment variables
    load_dotenv()
    
    # Configure the app
    configure_app(app, config_name)
    
    # Register middleware
    register_middleware(app)
    
    # Register extensions
    register_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app

def configure_app(app, config_name):
    """Configure the Flask application"""
    # Set default configuration
    app.config.update(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-key-do-not-use-in-production'),
        JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY', 'jwt-dev-key-do-not-use-in-production'),
        DATABASE_URI=os.environ.get('DATABASE_URI', 'sqlite:///app.db'),
        DEBUG=True if config_name == 'development' else False,
        TESTING=True if config_name == 'testing' else False,
        OPENAI_API_KEY=os.environ.get('OPENAI_API_KEY', ''),
        ANTHROPIC_API_KEY=os.environ.get('ANTHROPIC_API_KEY', ''),
        LLAMA_API_KEY=os.environ.get('LLAMA_API_KEY', ''),
        JWT_ACCESS_TOKEN_EXPIRES=86400,  # 1 day
        MOCK_BLOCKCHAIN=True,  # Set to False to use real blockchain
        WEB3_PROVIDER_URI=os.environ.get('WEB3_PROVIDER_URI', 'http://localhost:8545'),
        CONTRACT_ADDRESS=os.environ.get('CONTRACT_ADDRESS', '0x0000000000000000000000000000000000000000')
    )

def register_middleware(app):
    """Register middleware for the Flask application"""
    # Enable CORS
    CORS(app)
    
    # Fix for proxied requests
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

def register_extensions(app):
    """Register Flask extensions"""
    # JWT Manager
    jwt = JWTManager(app)
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"message": "Token has expired", "error": "token_expired"}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"message": "Invalid token", "error": "invalid_token"}), 401

def register_blueprints(app):
    """Register Flask blueprints"""
    # Import blueprints here to avoid circular imports
    try:
        from app.routes.auth import auth_bp
        from app.routes.user import user_bp
        from app.routes.learning import learning_bp
        from app.routes.ai_model import ai_model_bp
        
        # Register blueprints
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(user_bp, url_prefix='/api/users')
        app.register_blueprint(learning_bp, url_prefix='/api/learning')
        app.register_blueprint(ai_model_bp, url_prefix='/api/ai-models')
    except ImportError as e:
        app.logger.warning(f"Could not register all blueprints: {str(e)}")

def register_error_handlers(app):
    """Register error handlers"""
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404
    
    @app.errorhandler(500)
    def server_error(error):
        return jsonify({"error": "Internal server error"}), 500 
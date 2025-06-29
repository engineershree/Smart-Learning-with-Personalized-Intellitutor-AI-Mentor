"""
Authentication routes for the Smart Learning with Personalized AI Tutor application
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from app.database.db import get_db_session
from app.models.user import User
import json

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Missing required fields"}), 400
    
    db_session = get_db_session()
    
    # Check if user already exists
    if db_session.query(User).filter_by(username=data['username']).first():
        db_session.remove()
        return jsonify({"error": "Username already exists"}), 400
    
    if db_session.query(User).filter_by(email=data['email']).first():
        db_session.remove()
        return jsonify({"error": "Email already exists"}), 400
    
    # Create new user
    user = User(
        username=data['username'],
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        learning_style=data.get('learning_style'),
        preferred_subjects=json.dumps(data.get('preferred_subjects', [])),
        difficulty_preference=data.get('difficulty_preference', 'adaptive'),
        preferred_ai_model_id=data.get('preferred_ai_model_id', 1)
    )
    
    try:
        db_session.add(user)
        db_session.commit()
        
        # Create tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            "message": "User registered successfully",
            "user": user.to_dict(),
            "access_token": access_token,
            "refresh_token": refresh_token
        }), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db_session.remove()

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Missing username or password"}), 400
    
    db_session = get_db_session()
    
    try:
        user = db_session.query(User).filter_by(username=data['username']).first()
        
        if not user or not check_password_hash(user.password_hash, data['password']):
            return jsonify({"error": "Invalid username or password"}), 401
        
        if not user.is_active:
            return jsonify({"error": "Account is inactive"}), 401
        
        # Create tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            "message": "Login successful",
            "user": user.to_dict(),
            "access_token": access_token,
            "refresh_token": refresh_token
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db_session.remove()

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=current_user_id)
    return jsonify({"access_token": access_token}), 200 
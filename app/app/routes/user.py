"""
User routes for the Smart Learning with Personalized AI Tutor application
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database.db import get_db_session
from app.models.user import User
import json

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile"""
    current_user_id = get_jwt_identity()
    db_session = get_db_session()
    
    try:
        user = db_session.query(User).filter_by(id=current_user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify({"user": user.to_dict()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db_session.remove()

@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    db_session = get_db_session()
    
    try:
        user = db_session.query(User).filter_by(id=current_user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Update user fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'learning_style' in data:
            user.learning_style = data['learning_style']
        if 'preferred_subjects' in data:
            user.preferred_subjects = json.dumps(data['preferred_subjects'])
        if 'difficulty_preference' in data:
            user.difficulty_preference = data['difficulty_preference']
        if 'preferred_ai_model_id' in data:
            user.preferred_ai_model_id = data['preferred_ai_model_id']
        
        db_session.commit()
        return jsonify({
            "message": "Profile updated successfully",
            "user": user.to_dict()
        }), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db_session.remove()

@user_bp.route('/preferences', methods=['GET'])
@jwt_required()
def get_preferences():
    """Get user preferences"""
    current_user_id = get_jwt_identity()
    db_session = get_db_session()
    
    try:
        user = db_session.query(User).filter_by(id=current_user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        preferences = {
            'learning_style': user.learning_style,
            'preferred_subjects': json.loads(user.preferred_subjects) if user.preferred_subjects else [],
            'difficulty_preference': user.difficulty_preference,
            'preferred_ai_model_id': user.preferred_ai_model_id
        }
        
        return jsonify({"preferences": preferences}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db_session.remove()

@user_bp.route('/preferences', methods=['PUT'])
@jwt_required()
def update_preferences():
    """Update user preferences"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    db_session = get_db_session()
    
    try:
        user = db_session.query(User).filter_by(id=current_user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Update preferences
        if 'learning_style' in data:
            user.learning_style = data['learning_style']
        if 'preferred_subjects' in data:
            user.preferred_subjects = json.dumps(data['preferred_subjects'])
        if 'difficulty_preference' in data:
            user.difficulty_preference = data['difficulty_preference']
        if 'preferred_ai_model_id' in data:
            user.preferred_ai_model_id = data['preferred_ai_model_id']
        
        db_session.commit()
        return jsonify({
            "message": "Preferences updated successfully",
            "preferences": {
                'learning_style': user.learning_style,
                'preferred_subjects': json.loads(user.preferred_subjects) if user.preferred_subjects else [],
                'difficulty_preference': user.difficulty_preference,
                'preferred_ai_model_id': user.preferred_ai_model_id
            }
        }), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db_session.remove() 
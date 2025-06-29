"""
AI model routes for the Smart Learning with Personalized AI Tutor application
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database.db import get_session, close_session
from app.models.user import User, UserProfile
from app.models.ai_model import AIModel, UserAIModelPreference, AIModelType
import json
from werkzeug.exceptions import BadRequest, NotFound, Unauthorized

# Create blueprint
ai_model_bp = Blueprint('ai_model', __name__, url_prefix='/ai-model')

@ai_model_bp.route('/list', methods=['GET'])
@jwt_required()
def list_models():
    """List available AI models"""
    session = get_session()
    
    # Get available models
    models = session.query(AIModel).filter_by(is_active=True).all()
    
    # Get user's preferences
    user_id = get_jwt_identity()
    user_preferences = session.query(UserAIModelPreference).filter_by(user_id=user_id).all()
    
    # Get default model
    user_profile = session.query(UserProfile).filter_by(user_id=user_id).first()
    default_model_id = user_profile.default_ai_model_id if user_profile else None
    
    # Format response
    models_data = [model.to_dict() for model in models]
    preferences_data = [pref.to_dict() for pref in user_preferences]
    
    result = {
        "models": models_data,
        "user_preferences": preferences_data,
        "default_model_id": default_model_id
    }
    
    close_session(session)
    return jsonify(result)

@ai_model_bp.route('/select', methods=['POST'])
@jwt_required()
def select_model():
    """Select an AI model as default for user"""
    user_id = get_jwt_identity()
    data = request.json
    
    # Validate request
    if not data or 'model_id' not in data:
        raise BadRequest('Model ID is required')
    
    session = get_session()
    
    # Check if model exists
    model = session.query(AIModel).filter_by(id=data['model_id'], is_active=True).first()
    if not model:
        close_session(session)
        raise NotFound('AI Model not found or inactive')
    
    # Get user profile
    user_profile = session.query(UserProfile).filter_by(user_id=user_id).first()
    if not user_profile:
        close_session(session)
        raise NotFound('User profile not found')
    
    # Update default model
    user_profile.default_ai_model_id = model.id
    
    # Create preference if not exists
    preference = session.query(UserAIModelPreference).filter_by(
        user_id=user_id, 
        ai_model_id=model.id
    ).first()
    
    if not preference:
        preference = UserAIModelPreference(
            user_id=user_id,
            ai_model_id=model.id,
            is_default=True
        )
        session.add(preference)
    else:
        preference.is_default = True
    
    # Set other preferences as non-default
    other_preferences = session.query(UserAIModelPreference).filter(
        UserAIModelPreference.user_id == user_id,
        UserAIModelPreference.ai_model_id != model.id
    ).all()
    
    for pref in other_preferences:
        pref.is_default = False
    
    session.commit()
    close_session(session)
    
    return jsonify({
        "message": f"Successfully set {model.name} as default AI model",
        "model": model.to_dict()
    })

@ai_model_bp.route('/settings', methods=['POST'])
@jwt_required()
def update_model_settings():
    """Update user's settings for an AI model"""
    user_id = get_jwt_identity()
    data = request.json
    
    # Validate request
    if not data or 'model_id' not in data:
        raise BadRequest('Model ID is required')
    
    session = get_session()
    
    # Check if model exists
    model = session.query(AIModel).filter_by(id=data['model_id'], is_active=True).first()
    if not model:
        close_session(session)
        raise NotFound('AI Model not found or inactive')
    
    # Get or create preference
    preference = session.query(UserAIModelPreference).filter_by(
        user_id=user_id, 
        ai_model_id=model.id
    ).first()
    
    if not preference:
        preference = UserAIModelPreference(
            user_id=user_id,
            ai_model_id=model.id
        )
        session.add(preference)
    
    # Update API key if provided
    if 'api_key' in data:
        preference.api_key = data['api_key']
    
    # Update custom parameters if provided
    if 'custom_parameters' in data:
        preference.custom_parameters = json.dumps(data['custom_parameters'])
    
    session.commit()
    
    result = preference.to_dict()
    close_session(session)
    
    return jsonify({
        "message": "Model settings updated successfully",
        "preference": result
    })

@ai_model_bp.route('/admin/create', methods=['POST'])
@jwt_required()
def admin_create_model():
    """Create a new AI model (admin only)"""
    user_id = get_jwt_identity()
    data = request.json
    
    session = get_session()
    
    # Check if user is admin
    user = session.query(User).filter_by(id=user_id).first()
    if not user or user.role.value != 'admin':
        close_session(session)
        raise Unauthorized('Admin access required')
    
    # Validate required fields
    required_fields = ['name', 'model_type', 'description', 'api_endpoint']
    for field in required_fields:
        if field not in data:
            close_session(session)
            raise BadRequest(f'Missing required field: {field}')
    
    # Create new model
    try:
        model_type = AIModelType(data['model_type'])
    except ValueError:
        close_session(session)
        raise BadRequest(f"Invalid model type. Must be one of: {', '.join([t.value for t in AIModelType])}")
    
    new_model = AIModel(
        name=data['name'],
        model_type=model_type,
        description=data['description'],
        capabilities=json.dumps(data.get('capabilities', [])),
        parameters=json.dumps(data.get('parameters', {})),
        api_endpoint=data['api_endpoint'],
        api_key_required=data.get('api_key_required', True),
        is_active=data.get('is_active', True)
    )
    
    session.add(new_model)
    session.commit()
    
    result = new_model.to_dict()
    close_session(session)
    
    return jsonify({
        "message": "AI Model created successfully",
        "model": result
    }), 201 
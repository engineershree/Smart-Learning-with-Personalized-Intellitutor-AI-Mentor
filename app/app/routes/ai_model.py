"""
AI model routes for the Smart Learning with Personalized AI Tutor
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database.db import get_db_session
from app.models.user import User, AIModel

ai_model_bp = Blueprint('ai_model', __name__)

@ai_model_bp.route('', methods=['GET'])
@jwt_required()
def get_models():
    """Get all AI models"""
    # Get database session
    db_session = get_db_session()
    
    try:
        # Get all active AI models
        models = db_session.query(AIModel).filter_by(is_active=True).all()
        
        return jsonify({
            "models": [model.to_dict() for model in models]
        }), 200
    except Exception as e:
        return jsonify({"error": f"Could not retrieve AI models: {str(e)}"}), 500
    finally:
        db_session.remove()

@ai_model_bp.route('/admin', methods=['GET'])
@jwt_required()
def admin_get_models():
    """Admin endpoint to get all AI models (including inactive)"""
    # Get current user ID from JWT
    user_id = get_jwt_identity()
    
    # Get database session
    db_session = get_db_session()
    
    try:
        # Check if user is admin
        user = db_session.query(User).filter_by(id=user_id).first()
        
        if not user or not user.is_admin:
            return jsonify({"error": "Unauthorized access"}), 403
        
        # Get all AI models
        models = db_session.query(AIModel).all()
        
        return jsonify({
            "models": [model.to_dict() for model in models]
        }), 200
    except Exception as e:
        return jsonify({"error": f"Could not retrieve AI models: {str(e)}"}), 500
    finally:
        db_session.remove()

@ai_model_bp.route('', methods=['POST'])
@jwt_required()
def create_model():
    """Create a new AI model (admin only)"""
    # Get current user ID from JWT
    user_id = get_jwt_identity()
    
    # Get request data
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    required_fields = ['name', 'provider', 'model_id']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Get database session
    db_session = get_db_session()
    
    try:
        # Check if user is admin
        user = db_session.query(User).filter_by(id=user_id).first()
        
        if not user or not user.is_admin:
            return jsonify({"error": "Unauthorized access"}), 403
        
        # Check if model with same name already exists
        existing_model = db_session.query(AIModel).filter_by(name=data['name']).first()
        
        if existing_model:
            return jsonify({"error": "AI model with this name already exists"}), 409
        
        # Create new AI model
        new_model = AIModel(
            name=data['name'],
            provider=data['provider'],
            model_id=data['model_id'],
            api_key_name=data.get('api_key_name'),
            description=data.get('description'),
            is_active=data.get('is_active', True),
            is_default=data.get('is_default', False),
            max_tokens=data.get('max_tokens')
        )
        
        # If this model is set as default, unset any existing default
        if new_model.is_default:
            existing_default = db_session.query(AIModel).filter_by(is_default=True).first()
            if existing_default:
                existing_default.is_default = False
        
        db_session.add(new_model)
        db_session.commit()
        
        return jsonify({
            "message": "AI model created successfully",
            "model": new_model.to_dict()
        }), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": f"Could not create AI model: {str(e)}"}), 500
    finally:
        db_session.remove()

@ai_model_bp.route('/<int:model_id>', methods=['PUT'])
@jwt_required()
def update_model(model_id):
    """Update an AI model (admin only)"""
    # Get current user ID from JWT
    user_id = get_jwt_identity()
    
    # Get request data
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Get database session
    db_session = get_db_session()
    
    try:
        # Check if user is admin
        user = db_session.query(User).filter_by(id=user_id).first()
        
        if not user or not user.is_admin:
            return jsonify({"error": "Unauthorized access"}), 403
        
        # Get AI model
        model = db_session.query(AIModel).filter_by(id=model_id).first()
        
        if not model:
            return jsonify({"error": "AI model not found"}), 404
        
        # Update fields
        updateable_fields = [
            'name', 'provider', 'model_id', 'api_key_name', 'description',
            'is_active', 'max_tokens'
        ]
        
        for field in updateable_fields:
            if field in data:
                setattr(model, field, data[field])
        
        # Handle is_default separately
        if 'is_default' in data and data['is_default'] != model.is_default:
            if data['is_default']:
                # Unset any existing default
                existing_default = db_session.query(AIModel).filter_by(is_default=True).first()
                if existing_default and existing_default.id != model_id:
                    existing_default.is_default = False
                model.is_default = True
            else:
                model.is_default = False
        
        db_session.commit()
        
        return jsonify({
            "message": "AI model updated successfully",
            "model": model.to_dict()
        }), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": f"Could not update AI model: {str(e)}"}), 500
    finally:
        db_session.remove()

@ai_model_bp.route('/<int:model_id>', methods=['DELETE'])
@jwt_required()
def delete_model(model_id):
    """Delete an AI model (admin only)"""
    # Get current user ID from JWT
    user_id = get_jwt_identity()
    
    # Get database session
    db_session = get_db_session()
    
    try:
        # Check if user is admin
        user = db_session.query(User).filter_by(id=user_id).first()
        
        if not user or not user.is_admin:
            return jsonify({"error": "Unauthorized access"}), 403
        
        # Get AI model
        model = db_session.query(AIModel).filter_by(id=model_id).first()
        
        if not model:
            return jsonify({"error": "AI model not found"}), 404
        
        # Check if model is in use
        if model.is_default:
            return jsonify({"error": "Cannot delete the default AI model"}), 400
        
        # Delete model
        db_session.delete(model)
        db_session.commit()
        
        return jsonify({
            "message": "AI model deleted successfully"
        }), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": f"Could not delete AI model: {str(e)}"}), 500
    finally:
        db_session.remove() 
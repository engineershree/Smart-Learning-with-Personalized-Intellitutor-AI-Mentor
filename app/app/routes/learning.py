"""
Learning routes for the Smart Learning with Personalized AI Tutor application
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database.db import get_db_session
from app.models.user import User
from app.models.learning_session import LearningSession, Conversation, Assessment
from datetime import datetime

learning_bp = Blueprint('learning', __name__)

@learning_bp.route('/sessions', methods=['POST'])
@jwt_required()
def create_session():
    """Create a new learning session"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('subject') or not data.get('topic'):
        return jsonify({"error": "Missing required fields"}), 400
    
    db_session = get_db_session()
    
    try:
        # Create new learning session
        session = LearningSession(
            user_id=current_user_id,
            subject=data['subject'],
            topic=data['topic'],
            difficulty_level=data.get('difficulty_level', 'beginner'),
            status='active'
        )
        
        db_session.add(session)
        db_session.commit()
        
        return jsonify({
            "message": "Learning session created successfully",
            "session": session.to_dict()
        }), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db_session.remove()

@learning_bp.route('/sessions/<int:session_id>', methods=['GET'])
@jwt_required()
def get_session(session_id):
    """Get learning session details"""
    current_user_id = get_jwt_identity()
    db_session = get_db_session()
    
    try:
        session = db_session.query(LearningSession).filter_by(
            id=session_id,
            user_id=current_user_id
        ).first()
        
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        return jsonify({"session": session.to_dict()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db_session.remove()

@learning_bp.route('/sessions/<int:session_id>/conversations', methods=['POST'])
@jwt_required()
def add_conversation(session_id):
    """Add a conversation to a learning session"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('message'):
        return jsonify({"error": "Message is required"}), 400
    
    db_session = get_db_session()
    
    try:
        session = db_session.query(LearningSession).filter_by(
            id=session_id,
            user_id=current_user_id
        ).first()
        
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        conversation = Conversation(
            learning_session_id=session_id,
            message=data['message'],
            response=data.get('response')
        )
        
        db_session.add(conversation)
        db_session.commit()
        
        return jsonify({
            "message": "Conversation added successfully",
            "conversation": conversation.to_dict()
        }), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db_session.remove()

@learning_bp.route('/sessions/<int:session_id>/assessments', methods=['POST'])
@jwt_required()
def add_assessment(session_id):
    """Add an assessment to a learning session"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('question'):
        return jsonify({"error": "Question is required"}), 400
    
    db_session = get_db_session()
    
    try:
        session = db_session.query(LearningSession).filter_by(
            id=session_id,
            user_id=current_user_id
        ).first()
        
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        assessment = Assessment(
            learning_session_id=session_id,
            question=data['question'],
            answer=data.get('answer'),
            is_correct=data.get('is_correct', -1),
            score=data.get('score'),
            feedback=data.get('feedback')
        )
        
        db_session.add(assessment)
        db_session.commit()
        
        return jsonify({
            "message": "Assessment added successfully",
            "assessment": assessment.to_dict()
        }), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db_session.remove()

@learning_bp.route('/sessions/<int:session_id>', methods=['PUT'])
@jwt_required()
def update_session(session_id):
    """Update a learning session"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    db_session = get_db_session()
    
    try:
        session = db_session.query(LearningSession).filter_by(
            id=session_id,
            user_id=current_user_id
        ).first()
        
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        # Update session fields
        if 'status' in data:
            session.status = data['status']
            if data['status'] == 'completed':
                session.end_time = datetime.utcnow()
                session.duration = int((session.end_time - session.start_time).total_seconds())
        
        if 'difficulty_level' in data:
            session.difficulty_level = data['difficulty_level']
        
        db_session.commit()
        
        return jsonify({
            "message": "Session updated successfully",
            "session": session.to_dict()
        }), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db_session.remove()

@learning_bp.route('/sessions', methods=['GET'])
@jwt_required()
def get_user_sessions():
    """Get all learning sessions for the current user"""
    current_user_id = get_jwt_identity()
    db_session = get_db_session()
    
    try:
        sessions = db_session.query(LearningSession).filter_by(
            user_id=current_user_id
        ).all()
        
        return jsonify({
            "sessions": [session.to_dict() for session in sessions]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db_session.remove() 
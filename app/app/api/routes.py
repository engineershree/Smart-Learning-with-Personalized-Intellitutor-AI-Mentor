"""
Main API routes for the Smart Learning with Personalized AI Tutor application
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database.db import get_session, close_session
from app.models.user import User, UserProfile
from app.models.learning import LearningSession, Conversation, Assessment
from app.models.nlp_processor import NLPProcessor
from app.blockchain.blockchain_handler import BlockchainHandler
import json
import datetime

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Initialize NLP processor
nlp_processor = NLPProcessor()

# Initialize blockchain handler
blockchain_handler = BlockchainHandler()

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.datetime.utcnow().isoformat()
    })

@api_bp.route('/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """Get user information"""
    # Check if the requesting user has permission to access this user
    current_user_id = get_jwt_identity()
    if current_user_id != user_id:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    session = get_session()
    user = session.query(User).filter_by(id=user_id).first()
    
    if not user:
        close_session(session)
        return jsonify({'error': 'User not found'}), 404
    
    user_data = user.to_dict()
    close_session(session)
    
    return jsonify(user_data)

@api_bp.route('/user/<int:user_id>/profile', methods=['GET', 'PUT'])
@jwt_required()
def user_profile(user_id):
    """Get or update user profile"""
    # Check if the requesting user has permission to access this profile
    current_user_id = get_jwt_identity()
    if current_user_id != user_id:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    session = get_session()
    user = session.query(User).filter_by(id=user_id).first()
    
    if not user:
        close_session(session)
        return jsonify({'error': 'User not found'}), 404
    
    if request.method == 'GET':
        # Get user profile
        if not user.profile:
            close_session(session)
            return jsonify({'error': 'Profile not found'}), 404
        
        profile_data = user.profile.to_dict()
        close_session(session)
        return jsonify(profile_data)
    
    elif request.method == 'PUT':
        # Update user profile
        data = request.json
        
        if not user.profile:
            # Create new profile if it doesn't exist
            from app.models.user import UserProfile, LearningStyle
            profile = UserProfile(user_id=user.id)
            user.profile = profile
        
        # Update profile fields
        if 'learning_style' in data:
            from app.models.user import LearningStyle
            user.profile.learning_style = LearningStyle(data['learning_style'])
        
        if 'preferred_subjects' in data:
            user.profile.preferred_subjects = json.dumps(data['preferred_subjects'])
        
        if 'skill_level' in data:
            user.profile.skill_level = data['skill_level']
        
        if 'interests' in data:
            user.profile.interests = json.dumps(data['interests'])
        
        if 'bio' in data:
            user.profile.bio = data['bio']
        
        if 'avatar_url' in data:
            user.profile.avatar_url = data['avatar_url']
        
        if 'grade_level' in data:
            user.profile.grade_level = data['grade_level']
        
        if 'school' in data:
            user.profile.school = data['school']
        
        if 'specialization' in data:
            user.profile.specialization = data['specialization']
        
        if 'years_experience' in data:
            user.profile.years_experience = data['years_experience']
        
        if 'department' in data:
            user.profile.department = data['department']
        
        if 'job_title' in data:
            user.profile.job_title = data['job_title']
        
        if 'response_time_preference' in data:
            user.profile.response_time_preference = data['response_time_preference']
        
        if 'communication_preference' in data:
            user.profile.communication_preference = data['communication_preference']
        
        session.commit()
        profile_data = user.profile.to_dict()
        close_session(session)
        
        return jsonify(profile_data)

@api_bp.route('/sessions', methods=['GET'])
@jwt_required()
def get_sessions():
    """Get all learning sessions for the current user"""
    user_id = get_jwt_identity()
    
    session = get_session()
    user = session.query(User).filter_by(id=user_id).first()
    
    if not user:
        close_session(session)
        return jsonify({'error': 'User not found'}), 404
    
    learning_sessions = session.query(LearningSession).filter_by(user_id=user_id).all()
    sessions_data = [ls.to_dict() for ls in learning_sessions]
    close_session(session)
    
    return jsonify(sessions_data)

@api_bp.route('/sessions', methods=['POST'])
@jwt_required()
def create_session():
    """Create a new learning session"""
    user_id = get_jwt_identity()
    data = request.json
    
    # Validate required fields
    required_fields = ['subject', 'topic']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    session = get_session()
    user = session.query(User).filter_by(id=user_id).first()
    
    if not user:
        close_session(session)
        return jsonify({'error': 'User not found'}), 404
    
    # Create new learning session
    learning_session = LearningSession(
        user_id=user_id,
        subject=data['subject'],
        topic=data['topic'],
        difficulty_level=data.get('difficulty_level', 1),
        learning_objectives=json.dumps(data.get('learning_objectives', []))
    )
    
    # Store session data hash on blockchain
    session_data = {
        'user_id': user_id,
        'subject': data['subject'],
        'topic': data['topic'],
        'timestamp': datetime.datetime.utcnow().isoformat()
    }
    data_hash = blockchain_handler.get_hash(session_data)
    
    # Store hash on blockchain if user has wallet address
    if user.wallet_address:
        try:
            tx_hash = blockchain_handler.store_data_hash(data_hash, user.wallet_address)
            learning_session.blockchain_tx_hash = tx_hash
        except Exception as e:
            current_app.logger.error(f"Blockchain error: {str(e)}")
    
    session.add(learning_session)
    session.commit()
    
    session_data = learning_session.to_dict()
    close_session(session)
    
    return jsonify(session_data), 201

@api_bp.route('/sessions/<int:session_id>', methods=['GET'])
@jwt_required()
def get_session_by_id(session_id):
    """Get a specific learning session"""
    user_id = get_jwt_identity()
    
    session = get_session()
    learning_session = session.query(LearningSession).filter_by(id=session_id).first()
    
    if not learning_session:
        close_session(session)
        return jsonify({'error': 'Session not found'}), 404
    
    # Check if user has permission to access this session
    if learning_session.user_id != user_id:
        close_session(session)
        return jsonify({'error': 'Unauthorized access'}), 403
    
    session_data = learning_session.to_dict()
    close_session(session)
    
    return jsonify(session_data)

@api_bp.route('/sessions/<int:session_id>/conversations', methods=['GET'])
@jwt_required()
def get_conversations(session_id):
    """Get all conversations for a learning session"""
    user_id = get_jwt_identity()
    
    session = get_session()
    learning_session = session.query(LearningSession).filter_by(id=session_id).first()
    
    if not learning_session:
        close_session(session)
        return jsonify({'error': 'Session not found'}), 404
    
    # Check if user has permission to access this session
    if learning_session.user_id != user_id:
        close_session(session)
        return jsonify({'error': 'Unauthorized access'}), 403
    
    conversations = session.query(Conversation).filter_by(learning_session_id=session_id).order_by(Conversation.timestamp).all()
    conversations_data = [conv.to_dict() for conv in conversations]
    close_session(session)
    
    return jsonify(conversations_data)

@api_bp.route('/sessions/<int:session_id>/conversations', methods=['POST'])
@jwt_required()
def create_conversation(session_id):
    """Create a new conversation in a learning session"""
    user_id = get_jwt_identity()
    data = request.json
    
    # Validate required fields
    if 'user_message' not in data:
        return jsonify({'error': 'Missing required field: user_message'}), 400
    
    session = get_session()
    learning_session = session.query(LearningSession).filter_by(id=session_id).first()
    
    if not learning_session:
        close_session(session)
        return jsonify({'error': 'Session not found'}), 404
    
    # Check if user has permission to access this session
    if learning_session.user_id != user_id:
        close_session(session)
        return jsonify({'error': 'Unauthorized access'}), 403
    
    # Get user profile for personalization
    user = session.query(User).filter_by(id=user_id).first()
    user_profile = user.profile.to_dict() if user.profile else {}
    
    # Process user message with NLP
    user_message = data['user_message']
    
    # Extract topics from message
    topics = nlp_processor.extract_topics(user_message)
    
    # Calculate sentiment score
    sentiment_score = nlp_processor.analyze_sentiment(user_message)
    
    # Calculate engagement score
    engagement_score = nlp_processor.calculate_engagement_score(user_message)
    
    # Generate personalized AI response
    ai_response = nlp_processor.generate_personalized_response(user_message, user_profile)
    
    # Create new conversation
    from app.models.learning import CommunicationType
    conversation = Conversation(
        learning_session_id=session_id,
        communication_type=CommunicationType(data.get('communication_type', 'text')),
        user_message=user_message,
        ai_response=ai_response,
        sentiment_score=sentiment_score,
        topics_covered=json.dumps(topics),
        user_engagement_score=engagement_score
    )
    
    # Store conversation data hash on blockchain
    conversation_data = {
        'session_id': session_id,
        'user_id': user_id,
        'user_message': user_message,
        'ai_response': ai_response,
        'timestamp': datetime.datetime.utcnow().isoformat()
    }
    data_hash = blockchain_handler.get_hash(conversation_data)
    conversation.content_hash = data_hash
    
    session.add(conversation)
    session.commit()
    
    conversation_data = conversation.to_dict()
    close_session(session)
    
    return jsonify(conversation_data), 201

@api_bp.route('/sessions/<int:session_id>/end', methods=['POST'])
@jwt_required()
def end_session(session_id):
    """End a learning session"""
    user_id = get_jwt_identity()
    
    session = get_session()
    learning_session = session.query(LearningSession).filter_by(id=session_id).first()
    
    if not learning_session:
        close_session(session)
        return jsonify({'error': 'Session not found'}), 404
    
    # Check if user has permission to access this session
    if learning_session.user_id != user_id:
        close_session(session)
        return jsonify({'error': 'Unauthorized access'}), 403
    
    # End the session
    learning_session.end_time = datetime.datetime.utcnow()
    learning_session.is_active = False
    
    # Generate session summary
    conversations = session.query(Conversation).filter_by(learning_session_id=session_id).all()
    topics_covered = set()
    for conv in conversations:
        if conv.topics_covered:
            topics_covered.update(json.loads(conv.topics_covered))
    
    summary = f"Session covered the following topics: {', '.join(topics_covered)}. "
    summary += f"Total of {len(conversations)} interactions."
    
    learning_session.session_summary = summary
    
    session.commit()
    session_data = learning_session.to_dict()
    close_session(session)
    
    return jsonify(session_data)

@api_bp.route('/sessions/<int:session_id>/assessments', methods=['POST'])
@jwt_required()
def create_assessment(session_id):
    """Create a new assessment for a learning session"""
    user_id = get_jwt_identity()
    data = request.json
    
    # Validate required fields
    required_fields = ['assessment_type', 'title', 'questions']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    session = get_session()
    learning_session = session.query(LearningSession).filter_by(id=session_id).first()
    
    if not learning_session:
        close_session(session)
        return jsonify({'error': 'Session not found'}), 404
    
    # Check if user has permission to access this session
    if learning_session.user_id != user_id:
        close_session(session)
        return jsonify({'error': 'Unauthorized access'}), 403
    
    # Create new assessment
    assessment = Assessment(
        learning_session_id=session_id,
        assessment_type=data['assessment_type'],
        title=data['title'],
        description=data.get('description', ''),
        questions=json.dumps(data['questions']),
        answers=json.dumps(data.get('answers', {})),
        score=data.get('score'),
        max_score=data.get('max_score'),
        feedback=data.get('feedback', ''),
        strengths=json.dumps(data.get('strengths', [])),
        areas_for_improvement=json.dumps(data.get('areas_for_improvement', []))
    )
    
    session.add(assessment)
    session.commit()
    
    assessment_data = assessment.to_dict()
    close_session(session)
    
    return jsonify(assessment_data), 201

@api_bp.route('/sessions/<int:session_id>/assessments', methods=['GET'])
@jwt_required()
def get_assessments(session_id):
    """Get all assessments for a learning session"""
    user_id = get_jwt_identity()
    
    session = get_session()
    learning_session = session.query(LearningSession).filter_by(id=session_id).first()
    
    if not learning_session:
        close_session(session)
        return jsonify({'error': 'Session not found'}), 404
    
    # Check if user has permission to access this session
    if learning_session.user_id != user_id:
        close_session(session)
        return jsonify({'error': 'Unauthorized access'}), 403
    
    assessments = session.query(Assessment).filter_by(learning_session_id=session_id).all()
    assessments_data = [assessment.to_dict() for assessment in assessments]
    close_session(session)
    
    return jsonify(assessments_data) 
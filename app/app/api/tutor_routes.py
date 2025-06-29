"""
Tutor-specific routes for the Smart Learning with Personalized AI Tutor application
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database.db import get_session, close_session
from app.models.user import User, UserProfile
from app.models.learning import LearningSession, Conversation, Assessment, CommunicationType
from app.models.nlp_processor import NLPProcessor
from app.models.ai_model import AIModel, UserAIModelPreference
from app.blockchain.blockchain_handler import BlockchainHandler
import json
import datetime
import os
import base64
import tempfile
import uuid

# Create blueprint
tutor_bp = Blueprint('tutor', __name__, url_prefix='/tutor')

# Initialize NLP processor
nlp_processor = NLPProcessor()

# Initialize blockchain handler
blockchain_handler = BlockchainHandler()

@tutor_bp.route('/ask', methods=['POST'])
@jwt_required()
def ask_question():
    """Ask a question to the AI tutor"""
    user_id = get_jwt_identity()
    data = request.json
    
    # Validate required fields
    required_fields = ['session_id', 'message']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    session = get_session()
    learning_session = session.query(LearningSession).filter_by(id=data['session_id']).first()
    
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
    user_message = data['message']
    
    # Extract topics from message
    topics = nlp_processor.extract_topics(user_message)
    
    # Calculate sentiment score
    sentiment_score = nlp_processor.analyze_sentiment(user_message)
    
    # Calculate engagement score
    engagement_score = nlp_processor.calculate_engagement_score(user_message)
    
    # Get previous conversations for context
    previous_conversations = session.query(Conversation).filter_by(
        learning_session_id=data['session_id']
    ).order_by(Conversation.timestamp.desc()).limit(5).all()
    
    conversation_history = [
        {
            'user_message': conv.user_message,
            'ai_response': conv.ai_response,
            'timestamp': conv.timestamp.isoformat()
        }
        for conv in previous_conversations
    ]
    conversation_history.reverse()  # Chronological order
    
    # Get user's preferred AI model if available
    ai_model = None
    ai_model_preference = None
    
    # Check if specific model requested in this request
    if 'model_id' in data:
        ai_model = session.query(AIModel).filter_by(id=data['model_id'], is_active=True).first()
        if ai_model:
            ai_model_preference = session.query(UserAIModelPreference).filter_by(
                user_id=user_id, 
                ai_model_id=ai_model.id
            ).first()
    
    # If no model specified, use user's default model
    if not ai_model and user.profile and user.profile.default_ai_model_id:
        ai_model = session.query(AIModel).filter_by(
            id=user.profile.default_ai_model_id, 
            is_active=True
        ).first()
        
        if ai_model:
            ai_model_preference = session.query(UserAIModelPreference).filter_by(
                user_id=user_id, 
                ai_model_id=ai_model.id
            ).first()
    
    # Generate personalized AI response with specified AI model if available
    ai_response = nlp_processor.generate_personalized_response(
        user_message, 
        user_profile,
        conversation_history,
        ai_model,
        ai_model_preference
    )
    
    # Create new conversation
    conversation = Conversation(
        learning_session_id=data['session_id'],
        communication_type=CommunicationType.TEXT,
        user_message=user_message,
        ai_response=ai_response,
        sentiment_score=sentiment_score,
        topics_covered=json.dumps(topics),
        user_engagement_score=engagement_score
    )
    
    # Store conversation data hash on blockchain
    conversation_data = {
        'session_id': data['session_id'],
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
    
    # Add AI model info if used
    if ai_model:
        conversation_data['ai_model'] = {
            'id': ai_model.id,
            'name': ai_model.name,
            'model_type': ai_model.model_type.value
        }
        
    close_session(session)
    
    return jsonify(conversation_data)

@tutor_bp.route('/voice', methods=['POST'])
@jwt_required()
def voice_interaction():
    """Handle voice interaction with the AI tutor"""
    user_id = get_jwt_identity()
    
    # Check if request has the file part
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    # Get session ID from form data
    session_id = request.form.get('session_id')
    if not session_id:
        return jsonify({'error': 'Missing session_id'}), 400
    
    db_session = get_session()
    learning_session = db_session.query(LearningSession).filter_by(id=session_id).first()
    
    if not learning_session:
        close_session(db_session)
        return jsonify({'error': 'Session not found'}), 404
    
    # Check if user has permission to access this session
    if learning_session.user_id != user_id:
        close_session(db_session)
        return jsonify({'error': 'Unauthorized access'}), 403
    
    # Get user profile for personalization
    user = db_session.query(User).filter_by(id=user_id).first()
    user_profile = user.profile.to_dict() if user.profile else {}
    
    # Read audio file
    audio_file = request.files['audio']
    audio_data = audio_file.read()
    
    # Convert speech to text
    user_message = nlp_processor.speech_to_text(audio_data)
    
    if not user_message:
        close_session(db_session)
        return jsonify({'error': 'Could not understand the audio'}), 400
    
    # Extract topics from message
    topics = nlp_processor.extract_topics(user_message)
    
    # Calculate sentiment score
    sentiment_score = nlp_processor.analyze_sentiment(user_message)
    
    # Calculate engagement score
    engagement_score = nlp_processor.calculate_engagement_score(user_message)
    
    # Get previous conversations for context
    previous_conversations = db_session.query(Conversation).filter_by(
        learning_session_id=session_id
    ).order_by(Conversation.timestamp.desc()).limit(5).all()
    
    conversation_history = [
        {
            'user_message': conv.user_message,
            'ai_response': conv.ai_response,
            'timestamp': conv.timestamp.isoformat()
        }
        for conv in previous_conversations
    ]
    conversation_history.reverse()  # Chronological order
    
    # Get user's preferred AI model if available
    ai_model = None
    ai_model_preference = None
    
    # Check if specific model requested
    model_id = request.form.get('model_id')
    if model_id:
        ai_model = db_session.query(AIModel).filter_by(id=model_id, is_active=True).first()
        if ai_model:
            ai_model_preference = db_session.query(UserAIModelPreference).filter_by(
                user_id=user_id, 
                ai_model_id=ai_model.id
            ).first()
    
    # If no model specified, use user's default model
    if not ai_model and user.profile and user.profile.default_ai_model_id:
        ai_model = db_session.query(AIModel).filter_by(
            id=user.profile.default_ai_model_id, 
            is_active=True
        ).first()
        
        if ai_model:
            ai_model_preference = db_session.query(UserAIModelPreference).filter_by(
                user_id=user_id, 
                ai_model_id=ai_model.id
            ).first()
    
    # Generate personalized AI response
    ai_response = nlp_processor.generate_personalized_response(
        user_message, 
        user_profile,
        conversation_history,
        ai_model,
        ai_model_preference
    )
    
    # Convert text response to speech
    response_audio_data = nlp_processor.text_to_speech(ai_response)
    
    # Create temporary file for response audio
    media_filename = f"{uuid.uuid4()}.mp3"
    media_path = os.path.join(current_app.config['UPLOAD_FOLDER'], media_filename)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(media_path), exist_ok=True)
    
    # Save response audio
    with open(media_path, 'wb') as f:
        f.write(response_audio_data)
    
    # Create new conversation
    conversation = Conversation(
        learning_session_id=session_id,
        communication_type=CommunicationType.VOICE,
        user_message=user_message,
        ai_response=ai_response,
        media_url=f"/media/{media_filename}",
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
        'media_url': f"/media/{media_filename}",
        'timestamp': datetime.datetime.utcnow().isoformat()
    }
    data_hash = blockchain_handler.get_hash(conversation_data)
    conversation.content_hash = data_hash
    
    db_session.add(conversation)
    db_session.commit()
    
    conversation_data = conversation.to_dict()
    
    # Add AI model info if used
    if ai_model:
        conversation_data['ai_model'] = {
            'id': ai_model.id,
            'name': ai_model.name,
            'model_type': ai_model.model_type.value
        }
    
    close_session(db_session)
    
    return jsonify(conversation_data)

@tutor_bp.route('/video', methods=['POST'])
@jwt_required()
def video_interaction():
    """Handle video interaction with the AI tutor"""
    user_id = get_jwt_identity()
    
    # Check if request has the file part
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    # Get session ID from form data
    session_id = request.form.get('session_id')
    if not session_id:
        return jsonify({'error': 'Missing session_id'}), 400
    
    db_session = get_session()
    learning_session = db_session.query(LearningSession).filter_by(id=session_id).first()
    
    if not learning_session:
        close_session(db_session)
        return jsonify({'error': 'Session not found'}), 404
    
    # Check if user has permission to access this session
    if learning_session.user_id != user_id:
        close_session(db_session)
        return jsonify({'error': 'Unauthorized access'}), 403
    
    # Get user profile for personalization
    user = db_session.query(User).filter_by(id=user_id).first()
    user_profile = user.profile.to_dict() if user.profile else {}
    
    # Save video file
    video_file = request.files['video']
    filename = f"{uuid.uuid4()}.mp4"
    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, filename)
    video_file.save(file_path)
    
    # TODO: Implement video processing and speech-to-text conversion
    # For now, we'll use a placeholder message
    user_message = "This is a video message that would be processed for content."
    
    # Extract topics from message
    topics = nlp_processor.extract_topics(user_message)
    
    # Calculate sentiment score
    sentiment_score = nlp_processor.analyze_sentiment(user_message)
    
    # Calculate engagement score
    engagement_score = nlp_processor.calculate_engagement_score(user_message)
    
    # Generate personalized AI response
    ai_response = nlp_processor.generate_personalized_response(user_message, user_profile)
    
    # Create new conversation
    conversation = Conversation(
        learning_session_id=session_id,
        communication_type=CommunicationType.VIDEO,
        user_message=user_message,
        ai_response=ai_response,
        media_url=filename,
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
        'media_url': filename,
        'timestamp': datetime.datetime.utcnow().isoformat()
    }
    data_hash = blockchain_handler.get_hash(conversation_data)
    conversation.content_hash = data_hash
    
    db_session.add(conversation)
    db_session.commit()
    
    conversation_data = conversation.to_dict()
    close_session(db_session)
    
    return jsonify(conversation_data)

@tutor_bp.route('/generate-assessment', methods=['POST'])
@jwt_required()
def generate_assessment():
    """Generate an assessment based on learning session"""
    user_id = get_jwt_identity()
    data = request.json
    
    # Validate required fields
    if 'session_id' not in data:
        return jsonify({'error': 'Missing required field: session_id'}), 400
    
    db_session = get_session()
    learning_session = db_session.query(LearningSession).filter_by(id=data['session_id']).first()
    
    if not learning_session:
        close_session(db_session)
        return jsonify({'error': 'Session not found'}), 404
    
    # Check if user has permission to access this session
    if learning_session.user_id != user_id:
        close_session(db_session)
        return jsonify({'error': 'Unauthorized access'}), 403
    
    # Get conversations from the session
    conversations = db_session.query(Conversation).filter_by(
        learning_session_id=data['session_id']
    ).all()
    
    if not conversations:
        close_session(db_session)
        return jsonify({'error': 'No conversations found in this session'}), 400
    
    # Extract topics from conversations
    all_topics = set()
    for conv in conversations:
        if conv.topics_covered:
            all_topics.update(json.loads(conv.topics_covered))
    
    # Generate assessment questions based on topics
    # This is a simplified example - in a real system, you would use more sophisticated
    # question generation techniques
    questions = []
    for i, topic in enumerate(list(all_topics)[:5]):  # Limit to 5 questions
        questions.append({
            "id": i + 1,
            "question": f"Explain the concept of {topic} in your own words.",
            "type": "open_ended"
        })
    
    # Create assessment
    assessment = Assessment(
        learning_session_id=data['session_id'],
        assessment_type="quiz",
        title=f"Assessment for {learning_session.subject}: {learning_session.topic}",
        description=f"This assessment covers the topics discussed in your learning session on {learning_session.topic}.",
        questions=json.dumps(questions)
    )
    
    db_session.add(assessment)
    db_session.commit()
    
    assessment_data = assessment.to_dict()
    close_session(db_session)
    
    return jsonify(assessment_data)

@tutor_bp.route('/submit-assessment', methods=['POST'])
@jwt_required()
def submit_assessment():
    """Submit answers to an assessment"""
    user_id = get_jwt_identity()
    data = request.json
    
    # Validate required fields
    required_fields = ['assessment_id', 'answers']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    db_session = get_session()
    assessment = db_session.query(Assessment).filter_by(id=data['assessment_id']).first()
    
    if not assessment:
        close_session(db_session)
        return jsonify({'error': 'Assessment not found'}), 404
    
    # Get learning session
    learning_session = db_session.query(LearningSession).filter_by(id=assessment.learning_session_id).first()
    
    # Check if user has permission to access this assessment
    if learning_session.user_id != user_id:
        close_session(db_session)
        return jsonify({'error': 'Unauthorized access'}), 403
    
    # Update assessment with answers
    assessment.answers = json.dumps(data['answers'])
    
    # TODO: Implement scoring logic
    # For now, we'll use a placeholder score
    assessment.score = 8.0
    assessment.max_score = 10.0
    
    # Generate feedback
    assessment.feedback = "Great job on the assessment! You demonstrated a good understanding of the key concepts."
    assessment.strengths = json.dumps(["Clear explanations", "Good use of examples"])
    assessment.areas_for_improvement = json.dumps(["Could provide more detail in some answers"])
    
    db_session.commit()
    
    assessment_data = assessment.to_dict()
    close_session(db_session)
    
    return jsonify(assessment_data)

@tutor_bp.route('/learning-style', methods=['POST'])
@jwt_required()
def detect_learning_style():
    """Detect user's learning style from text"""
    user_id = get_jwt_identity()
    data = request.json
    
    # Validate required fields
    if 'text' not in data:
        return jsonify({'error': 'Missing required field: text'}), 400
    
    # Detect learning style
    learning_style = nlp_processor.detect_learning_style(data['text'])
    
    # Update user profile if requested
    if data.get('update_profile', False):
        db_session = get_session()
        user = db_session.query(User).filter_by(id=user_id).first()
        
        if not user:
            close_session(db_session)
            return jsonify({'error': 'User not found'}), 404
        
        if not user.profile:
            from app.models.user import UserProfile, LearningStyle
            profile = UserProfile(user_id=user.id)
            user.profile = profile
        
        if learning_style:
            from app.models.user import LearningStyle
            user.profile.learning_style = LearningStyle(learning_style)
            db_session.commit()
        
        close_session(db_session)
    
    return jsonify({
        'learning_style': learning_style,
        'confidence': 0.8  # Placeholder confidence score
    }) 
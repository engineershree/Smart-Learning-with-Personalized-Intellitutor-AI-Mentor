"""
Dashboard routes for the Smart Learning with Personalized AI Tutor application
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database.db import get_session, close_session
from app.models.user import User, UserRole
from app.models.learning import LearningSession, Conversation, Assessment
from sqlalchemy import func, desc
import json
import datetime

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/overview', methods=['GET'])
@jwt_required()
def get_overview():
    """Get an overview of user's learning activities"""
    user_id = get_jwt_identity()
    
    session = get_session()
    user = session.query(User).filter_by(id=user_id).first()
    
    if not user:
        close_session(session)
        return jsonify({'error': 'User not found'}), 404
    
    # Get active sessions
    active_sessions = session.query(LearningSession).filter_by(
        user_id=user_id, 
        is_active=True
    ).all()
    
    # Get recent sessions
    recent_sessions = session.query(LearningSession).filter_by(
        user_id=user_id
    ).order_by(desc(LearningSession.start_time)).limit(5).all()
    
    # Get total sessions count
    total_sessions = session.query(func.count(LearningSession.id)).filter_by(
        user_id=user_id
    ).scalar()
    
    # Get total conversation count
    total_conversations = session.query(func.count(Conversation.id)).join(
        LearningSession
    ).filter(
        LearningSession.user_id == user_id
    ).scalar()
    
    # Get total assessment count
    total_assessments = session.query(func.count(Assessment.id)).join(
        LearningSession
    ).filter(
        LearningSession.user_id == user_id
    ).scalar()
    
    # Get average assessment score
    avg_score = session.query(func.avg(Assessment.score)).join(
        LearningSession
    ).filter(
        LearningSession.user_id == user_id,
        Assessment.score.isnot(None)
    ).scalar()
    
    # Get subjects studied
    subjects = session.query(
        LearningSession.subject, 
        func.count(LearningSession.id).label('count')
    ).filter_by(
        user_id=user_id
    ).group_by(
        LearningSession.subject
    ).all()
    
    # Get recent conversations
    recent_conversations = session.query(Conversation).join(
        LearningSession
    ).filter(
        LearningSession.user_id == user_id
    ).order_by(
        desc(Conversation.timestamp)
    ).limit(5).all()
    
    # Prepare response data
    overview_data = {
        'user': {
            'id': user.id,
            'username': user.username,
            'role': user.role.value,
            'first_name': user.first_name,
            'last_name': user.last_name
        },
        'stats': {
            'total_sessions': total_sessions,
            'active_sessions': len(active_sessions),
            'total_conversations': total_conversations,
            'total_assessments': total_assessments,
            'avg_assessment_score': float(avg_score) if avg_score else None
        },
        'active_sessions': [session.to_dict() for session in active_sessions],
        'recent_sessions': [session.to_dict() for session in recent_sessions],
        'subjects': [{'subject': subject, 'count': count} for subject, count in subjects],
        'recent_conversations': [conv.to_dict() for conv in recent_conversations]
    }
    
    close_session(session)
    
    return jsonify(overview_data)

@dashboard_bp.route('/progress', methods=['GET'])
@jwt_required()
def get_progress():
    """Get user's learning progress"""
    user_id = get_jwt_identity()
    
    session = get_session()
    user = session.query(User).filter_by(id=user_id).first()
    
    if not user:
        close_session(session)
        return jsonify({'error': 'User not found'}), 404
    
    # Get all assessments
    assessments = session.query(Assessment).join(
        LearningSession
    ).filter(
        LearningSession.user_id == user_id,
        Assessment.score.isnot(None)
    ).order_by(
        Assessment.timestamp
    ).all()
    
    # Calculate progress over time
    progress_data = []
    for assessment in assessments:
        progress_data.append({
            'timestamp': assessment.timestamp.isoformat(),
            'subject': assessment.learning_session.subject,
            'topic': assessment.learning_session.topic,
            'score': assessment.score,
            'max_score': assessment.max_score,
            'percentage': (assessment.score / assessment.max_score * 100) if assessment.max_score else None
        })
    
    # Get strengths and areas for improvement
    strengths = {}
    areas_for_improvement = {}
    
    for assessment in assessments:
        if assessment.strengths:
            for strength in json.loads(assessment.strengths):
                if strength in strengths:
                    strengths[strength] += 1
                else:
                    strengths[strength] = 1
        
        if assessment.areas_for_improvement:
            for area in json.loads(assessment.areas_for_improvement):
                if area in areas_for_improvement:
                    areas_for_improvement[area] += 1
                else:
                    areas_for_improvement[area] = 1
    
    # Sort by frequency
    strengths = [{'area': k, 'count': v} for k, v in sorted(strengths.items(), key=lambda item: item[1], reverse=True)]
    areas_for_improvement = [{'area': k, 'count': v} for k, v in sorted(areas_for_improvement.items(), key=lambda item: item[1], reverse=True)]
    
    # Get engagement metrics
    engagement_data = session.query(
        func.avg(Conversation.user_engagement_score).label('avg_engagement'),
        func.avg(Conversation.sentiment_score).label('avg_sentiment'),
        func.count(Conversation.id).label('count')
    ).join(
        LearningSession
    ).filter(
        LearningSession.user_id == user_id
    ).group_by(
        LearningSession.subject
    ).all()
    
    engagement_by_subject = [
        {
            'subject': subject,
            'avg_engagement': float(avg_engagement) if avg_engagement else None,
            'avg_sentiment': float(avg_sentiment) if avg_sentiment else None,
            'conversation_count': count
        }
        for subject, avg_engagement, avg_sentiment, count in engagement_data
    ]
    
    progress_overview = {
        'assessments': progress_data,
        'strengths': strengths[:5],  # Top 5 strengths
        'areas_for_improvement': areas_for_improvement[:5],  # Top 5 areas for improvement
        'engagement_by_subject': engagement_by_subject
    }
    
    close_session(session)
    
    return jsonify(progress_overview)

@dashboard_bp.route('/insights', methods=['GET'])
@jwt_required()
def get_insights():
    """Get personalized insights for the user"""
    user_id = get_jwt_identity()
    
    session = get_session()
    user = session.query(User).filter_by(id=user_id).first()
    
    if not user:
        close_session(session)
        return jsonify({'error': 'User not found'}), 404
    
    # Get user profile
    user_profile = user.profile
    
    if not user_profile:
        close_session(session)
        return jsonify({'error': 'User profile not found'}), 404
    
    # Get learning style
    learning_style = user_profile.learning_style.value if user_profile.learning_style else None
    
    # Get preferred subjects
    preferred_subjects = json.loads(user_profile.preferred_subjects) if user_profile.preferred_subjects else []
    
    # Get interests
    interests = json.loads(user_profile.interests) if user_profile.interests else []
    
    # Get most active subjects
    active_subjects = session.query(
        LearningSession.subject,
        func.count(LearningSession.id).label('count')
    ).filter_by(
        user_id=user_id
    ).group_by(
        LearningSession.subject
    ).order_by(
        desc('count')
    ).limit(3).all()
    
    active_subjects = [subject for subject, _ in active_subjects]
    
    # Get topics with highest engagement
    high_engagement_topics = session.query(
        LearningSession.topic,
        func.avg(Conversation.user_engagement_score).label('avg_engagement')
    ).join(
        Conversation
    ).filter(
        LearningSession.user_id == user_id
    ).group_by(
        LearningSession.topic
    ).order_by(
        desc('avg_engagement')
    ).limit(3).all()
    
    high_engagement_topics = [topic for topic, _ in high_engagement_topics]
    
    # Get topics with lowest engagement
    low_engagement_topics = session.query(
        LearningSession.topic,
        func.avg(Conversation.user_engagement_score).label('avg_engagement')
    ).join(
        Conversation
    ).filter(
        LearningSession.user_id == user_id
    ).group_by(
        LearningSession.topic
    ).order_by(
        'avg_engagement'
    ).limit(3).all()
    
    low_engagement_topics = [topic for topic, _ in low_engagement_topics]
    
    # Generate personalized recommendations
    recommendations = []
    
    # Recommend based on learning style
    if learning_style:
        if learning_style == 'visual':
            recommendations.append("Try using diagrams and visual aids to enhance your learning experience.")
        elif learning_style == 'auditory':
            recommendations.append("Consider using voice interactions more frequently for better learning outcomes.")
        elif learning_style == 'reading_writing':
            recommendations.append("Taking notes during your learning sessions may help you retain information better.")
        elif learning_style == 'kinesthetic':
            recommendations.append("Try practical exercises and hands-on activities to reinforce your learning.")
    
    # Recommend based on engagement
    if low_engagement_topics:
        recommendations.append(f"You seem less engaged with topics like {', '.join(low_engagement_topics)}. Consider trying a different learning approach for these topics.")
    
    if high_engagement_topics:
        recommendations.append(f"You show high engagement with topics like {', '.join(high_engagement_topics)}. Consider exploring more advanced content in these areas.")
    
    # Recommend based on interests
    if interests and active_subjects:
        potential_interests = [interest for interest in interests if interest not in active_subjects]
        if potential_interests:
            recommendations.append(f"Based on your interests, you might enjoy learning about {', '.join(potential_interests[:2])}.")
    
    insights_data = {
        'learning_style': learning_style,
        'preferred_subjects': preferred_subjects,
        'interests': interests,
        'active_subjects': active_subjects,
        'high_engagement_topics': high_engagement_topics,
        'low_engagement_topics': low_engagement_topics,
        'recommendations': recommendations
    }
    
    close_session(session)
    
    return jsonify(insights_data)

@dashboard_bp.route('/admin/overview', methods=['GET'])
@jwt_required()
def admin_overview():
    """Get an overview of all users and activities (admin only)"""
    user_id = get_jwt_identity()
    
    session = get_session()
    user = session.query(User).filter_by(id=user_id).first()
    
    if not user or user.role != UserRole.ADMIN:
        close_session(session)
        return jsonify({'error': 'Unauthorized access'}), 403
    
    # Get user counts by role
    user_counts = session.query(
        User.role,
        func.count(User.id).label('count')
    ).group_by(
        User.role
    ).all()
    
    user_counts_by_role = {role.value: count for role, count in user_counts}
    
    # Get active users in the last 7 days
    one_week_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    active_users = session.query(func.count(User.id)).join(
        LearningSession
    ).filter(
        LearningSession.start_time >= one_week_ago
    ).scalar()
    
    # Get total sessions
    total_sessions = session.query(func.count(LearningSession.id)).scalar()
    
    # Get total conversations
    total_conversations = session.query(func.count(Conversation.id)).scalar()
    
    # Get average session duration
    avg_duration = session.query(
        func.avg(
            func.julianday(LearningSession.end_time) - func.julianday(LearningSession.start_time)
        ) * 24 * 60  # Convert to minutes
    ).filter(
        LearningSession.end_time.isnot(None)
    ).scalar()
    
    # Get popular subjects
    popular_subjects = session.query(
        LearningSession.subject,
        func.count(LearningSession.id).label('count')
    ).group_by(
        LearningSession.subject
    ).order_by(
        desc('count')
    ).limit(5).all()
    
    popular_subjects = [{'subject': subject, 'count': count} for subject, count in popular_subjects]
    
    # Get recent sessions
    recent_sessions = session.query(LearningSession).order_by(
        desc(LearningSession.start_time)
    ).limit(10).all()
    
    admin_data = {
        'user_counts': user_counts_by_role,
        'active_users_last_week': active_users,
        'total_sessions': total_sessions,
        'total_conversations': total_conversations,
        'avg_session_duration_minutes': float(avg_duration) if avg_duration else None,
        'popular_subjects': popular_subjects,
        'recent_sessions': [session.to_dict() for session in recent_sessions]
    }
    
    close_session(session)
    
    return jsonify(admin_data) 
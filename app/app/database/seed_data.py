"""
Seed data for the Smart Learning with Personalized AI Tutor application
"""

import json
from app.models.user import User, UserRole, UserProfile, LearningStyle
from app.models.learning import LearningSession, Conversation, Assessment
from app.models.ai_model import AIModel, AIModelType, UserAIModelPreference
from werkzeug.security import generate_password_hash

def seed_ai_models(db_session):
    """Seed AI models"""
    
    # Check if models already exist
    existing_models = db_session.query(AIModel).all()
    if existing_models:
        print("AI models already exist, skipping seed")
        return
    
    # GPT model
    gpt_model = AIModel(
        name="GPT-3.5 Turbo",
        model_type=AIModelType.GPT,
        description="OpenAI's GPT-3.5 Turbo model for general-purpose AI assistance.",
        capabilities=json.dumps([
            "natural language understanding",
            "detailed explanations",
            "code generation",
            "creative writing",
            "tutoring"
        ]),
        parameters=json.dumps({
            "model": "gpt-3.5-turbo",
            "max_tokens": 500,
            "temperature": 0.7
        }),
        api_endpoint="https://api.openai.com/v1/chat/completions",
        api_key_required=True,
        is_active=True
    )
    
    # Claude model
    claude_model = AIModel(
        name="Claude 2",
        model_type=AIModelType.CLAUDE,
        description="Anthropic's Claude 2, an assistant that's helpful, harmless, and honest.",
        capabilities=json.dumps([
            "educational explanations",
            "detailed responses",
            "thoughtful reasoning",
            "contextual understanding"
        ]),
        parameters=json.dumps({
            "model": "claude-2.0",
            "max_tokens_to_sample": 500,
            "temperature": 0.7
        }),
        api_endpoint="https://api.anthropic.com/v1/complete",
        api_key_required=True,
        is_active=True
    )
    
    # BERT model (local)
    bert_model = AIModel(
        name="BERT Q&A",
        model_type=AIModelType.BERT,
        description="Local BERT model for specific Q&A tasks.",
        capabilities=json.dumps([
            "question answering",
            "information extraction",
            "named entity recognition"
        ]),
        parameters=json.dumps({
            "model": "bert-large-uncased-whole-word-masking-finetuned-squad",
            "use_local": True
        }),
        api_endpoint=None,
        api_key_required=False,
        is_active=True
    )
    
    # Llama model
    llama_model = AIModel(
        name="Llama 2",
        model_type=AIModelType.LLAMA,
        description="Meta's Llama 2 model for conversational AI.",
        capabilities=json.dumps([
            "educational conversation",
            "knowledge retrieval",
            "context awareness",
            "structured output"
        ]),
        parameters=json.dumps({
            "model": "llama-2-70b-chat",
            "max_length": 512,
            "temperature": 0.7
        }),
        api_endpoint="https://api.example.com/llama",  # Placeholder
        api_key_required=True,
        is_active=True
    )
    
    # Add models to session
    db_session.add(gpt_model)
    db_session.add(claude_model)
    db_session.add(bert_model)
    db_session.add(llama_model)
    
    # Commit to database
    db_session.commit()
    
    print("AI models seeded successfully")
    return [gpt_model, claude_model, bert_model, llama_model]

def seed_admin_user(db_session):
    """Seed admin user"""
    
    # Check if admin already exists
    admin = db_session.query(User).filter_by(username="admin").first()
    if admin:
        print("Admin user already exists, skipping seed")
        return admin
    
    # Create admin user
    admin = User(
        username="admin",
        email="admin@example.com",
        password="adminpassword",  # This will be hashed in the User model
        role=UserRole.ADMIN,
        first_name="Admin",
        last_name="User"
    )
    
    # Create admin profile
    admin_profile = UserProfile(
        user=admin,
        learning_style=LearningStyle.VISUAL,
        preferred_subjects=json.dumps(["Computer Science", "Artificial Intelligence"]),
        skill_level=10,
        interests=json.dumps(["Programming", "Machine Learning", "Education Technology"]),
        bio="Administrator of the Smart Learning Platform",
        response_time_preference=5,
        communication_preference="text"
    )
    
    # Add to session
    db_session.add(admin)
    db_session.add(admin_profile)
    
    # Commit to database
    db_session.commit()
    
    print("Admin user seeded successfully")
    return admin

def seed_demo_user(db_session, ai_models):
    """Seed demo user with AI model preferences"""
    
    # Check if demo user already exists
    demo_user = db_session.query(User).filter_by(username="demo").first()
    if demo_user:
        print("Demo user already exists, skipping seed")
        return demo_user
    
    # Create demo user
    demo_user = User(
        username="demo",
        email="demo@example.com",
        password="demopassword",  # This will be hashed in the User model
        role=UserRole.STUDENT,
        first_name="Demo",
        last_name="User"
    )
    
    # Create demo profile
    demo_profile = UserProfile(
        user=demo_user,
        learning_style=LearningStyle.AUDITORY,
        preferred_subjects=json.dumps(["Mathematics", "Physics", "Programming"]),
        skill_level=5,
        interests=json.dumps(["Science", "Technology", "Engineering"]),
        bio="Demo user for the Smart Learning Platform",
        grade_level="University",
        school="Demo University",
        response_time_preference=8,
        communication_preference="voice",
        default_ai_model_id=ai_models[0].id if ai_models else None  # Default to GPT
    )
    
    # Add to session
    db_session.add(demo_user)
    db_session.add(demo_profile)
    
    # Create AI model preferences if models exist
    if ai_models:
        for model in ai_models:
            preference = UserAIModelPreference(
                user_id=demo_user.id,
                ai_model_id=model.id,
                is_default=model.id == ai_models[0].id,  # First model is default
                custom_parameters=json.dumps({
                    "temperature": 0.8,
                    "max_tokens": 600
                }) if model.model_type == AIModelType.GPT else None
            )
            db_session.add(preference)
    
    # Commit to database
    db_session.commit()
    
    print("Demo user seeded successfully")
    return demo_user

def seed_all(db_session):
    """Seed all data"""
    ai_models = seed_ai_models(db_session)
    admin = seed_admin_user(db_session)
    demo_user = seed_demo_user(db_session, ai_models)
    
    print("All seed data created successfully") 
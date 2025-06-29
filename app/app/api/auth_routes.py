"""
Authentication routes for the Smart Learning with Personalized AI Tutor application
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app.database.db import get_session, close_session
from app.models.user import User, UserRole
from app.blockchain.blockchain_handler import BlockchainHandler
import datetime

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Initialize blockchain handler
blockchain_handler = BlockchainHandler()

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.json
    
    # Validate required fields
    required_fields = ['username', 'email', 'password', 'role']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    session = get_session()
    
    # Check if username already exists
    if session.query(User).filter_by(username=data['username']).first():
        close_session(session)
        return jsonify({'error': 'Username already exists'}), 400
    
    # Check if email already exists
    if session.query(User).filter_by(email=data['email']).first():
        close_session(session)
        return jsonify({'error': 'Email already exists'}), 400
    
    # Validate role
    try:
        role = UserRole(data['role'])
    except ValueError:
        close_session(session)
        return jsonify({'error': f'Invalid role. Must be one of: {[r.value for r in UserRole]}'}), 400
    
    # Create new user
    user = User(
        username=data['username'],
        email=data['email'],
        password=data['password'],
        role=role,
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        wallet_address=data.get('wallet_address')
    )
    
    session.add(user)
    session.commit()
    
    # Generate tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    user_data = user.to_dict()
    user_data['access_token'] = access_token
    user_data['refresh_token'] = refresh_token
    
    close_session(session)
    
    return jsonify(user_data), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login a user"""
    data = request.json
    
    # Validate required fields
    required_fields = ['username', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    session = get_session()
    
    # Find user by username
    user = session.query(User).filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        close_session(session)
        return jsonify({'error': 'Invalid username or password'}), 401
    
    if not user.is_active:
        close_session(session)
        return jsonify({'error': 'Account is inactive'}), 401
    
    # Generate tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    user_data = user.to_dict()
    user_data['access_token'] = access_token
    user_data['refresh_token'] = refresh_token
    
    close_session(session)
    
    return jsonify(user_data)

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    current_user_id = get_jwt_identity()
    
    session = get_session()
    user = session.query(User).filter_by(id=current_user_id).first()
    
    if not user or not user.is_active:
        close_session(session)
        return jsonify({'error': 'User not found or inactive'}), 401
    
    # Generate new access token
    access_token = create_access_token(identity=current_user_id)
    
    close_session(session)
    
    return jsonify({'access_token': access_token})

@auth_bp.route('/verify-wallet', methods=['POST'])
@jwt_required()
def verify_wallet():
    """Verify a blockchain wallet address"""
    user_id = get_jwt_identity()
    data = request.json
    
    # Validate required fields
    required_fields = ['wallet_address', 'signature', 'message']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    session = get_session()
    user = session.query(User).filter_by(id=user_id).first()
    
    if not user:
        close_session(session)
        return jsonify({'error': 'User not found'}), 404
    
    # Verify signature
    try:
        is_valid = blockchain_handler.verify_signature(
            data['message'],
            data['signature'],
            data['wallet_address']
        )
    except Exception as e:
        close_session(session)
        return jsonify({'error': f'Verification error: {str(e)}'}), 400
    
    if not is_valid:
        close_session(session)
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Update user's wallet address
    user.wallet_address = data['wallet_address']
    session.commit()
    
    user_data = user.to_dict()
    close_session(session)
    
    return jsonify(user_data)

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    user_id = get_jwt_identity()
    data = request.json
    
    # Validate required fields
    required_fields = ['current_password', 'new_password']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    session = get_session()
    user = session.query(User).filter_by(id=user_id).first()
    
    if not user:
        close_session(session)
        return jsonify({'error': 'User not found'}), 404
    
    # Verify current password
    if not user.check_password(data['current_password']):
        close_session(session)
        return jsonify({'error': 'Current password is incorrect'}), 400
    
    # Update password
    user.set_password(data['new_password'])
    session.commit()
    
    close_session(session)
    
    return jsonify({'message': 'Password updated successfully'})

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout a user"""
    # In a stateless JWT system, the client is responsible for discarding the token
    # This endpoint is provided for API completeness
    return jsonify({'message': 'Logout successful'})

@auth_bp.route('/delete-account', methods=['POST'])
@jwt_required()
def delete_account():
    """Delete a user account"""
    user_id = get_jwt_identity()
    data = request.json
    
    # Validate required fields
    if 'password' not in data:
        return jsonify({'error': 'Missing required field: password'}), 400
    
    session = get_session()
    user = session.query(User).filter_by(id=user_id).first()
    
    if not user:
        close_session(session)
        return jsonify({'error': 'User not found'}), 404
    
    # Verify password
    if not user.check_password(data['password']):
        close_session(session)
        return jsonify({'error': 'Password is incorrect'}), 400
    
    # Instead of deleting, mark as inactive
    user.is_active = False
    user.updated_at = datetime.datetime.utcnow()
    session.commit()
    
    close_session(session)
    
    return jsonify({'message': 'Account deactivated successfully'}) 
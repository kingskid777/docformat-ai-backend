"""
PublishPilot Studio - MVP API
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET', 'dev-secret-key-12345')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

CORS(app)
jwt = JWTManager(app)

# In-memory database
users_db = {}
subscriptions_db = {}

def validate_email(email):
    return '@' in email and '.' in email

def get_user_tier(user_id):
    sub = subscriptions_db.get(user_id, {})
    return sub.get('plan', 'free')

@app.route('/api/v1/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    
    if not validate_email(data['email']):
        return jsonify({'error': 'Invalid email'}), 400
    
    if data['email'] in users_db:
        return jsonify({'error': 'Email already registered'}), 409
    
    if len(data['password']) < 6:
        return jsonify({'error': 'Password must be 6+ characters'}), 400
    
    user_id = len(users_db) + 1
    users_db[data['email']] = {
        'id': user_id,
        'email': data['email'],
        'password_hash': generate_password_hash(data['password']),
        'first_name': data.get('first_name', ''),
        'last_name': data.get('last_name', ''),
        'created_at': datetime.now().isoformat()
    }
    
    subscriptions_db[user_id] = {
        'plan': 'free',
        'status': 'active',
        'started_at': datetime.now().isoformat(),
        'expires_at': None
    }
    
    return jsonify({
        'message': 'Registration successful',
        'user_id': user_id,
        'email': data['email']
    }), 201

@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    
    user = users_db.get(data['email'])
    if not user or not check_password_hash(user['password_hash'], data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    access_token = create_access_token(identity=user['id'])
    
    return jsonify({
        'access_token': access_token,
        'user': {
            'id': user['id'],
            'email': user['email'],
            'tier': get_user_tier(user['id'])
        }
    }), 200

@app.route('/api/v1/user/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = next((u for u in users_db.values() if u['id'] == user_id), None)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'id': user['id'],
        'email': user['email'],
        'first_name': user['first_name'],
        'last_name': user['last_name'],
        'tier': get_user_tier(user['id']),
        'created_at': user['created_at']
    }), 200

@app.route('/api/v1/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'ver

from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from app.models import User

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            current_user = User.query.get(current_user_id)
            
            if not current_user or not current_user.is_active:
                return jsonify({'message': 'User not found or inactive'}), 401
            
            # Attach user to request
            request.current_user = current_user
            request.jwt = get_jwt()
            
        except Exception as e:
            return jsonify({'message': 'Invalid or expired token'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

def role_required(required_role):
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated_function(*args, **kwargs):
            if not request.current_user.is_admin and required_role == "admin":
                return jsonify({'message': 'Admin access required'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def kyc_required(f):
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if request.current_user.kyc_status.value != 'verified':
            return jsonify({
                'message': 'KYC verification required',
                'kyc_status': request.current_user.kyc_status.value
            }), 403
        return f(*args, **kwargs)
    return decorated
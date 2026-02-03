from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from app.models import User
from ..services.otp_services import OTPService


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
            if required_role == "admin" and not request.current_user.is_admin:
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


# otp decorators
def otp_required(operation_type, amount_field='amount'):
    """Decorator that requires OTP verification for sensitive operations"""
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated_function(*args, **kwargs):
            current_user = request.current_user
            
            # Get amount from request if applicable
            amount = None
            if request.json and amount_field in request.json:
                amount = request.json[amount_field]
            
            # Check if OTP is required for this operation
            requires_otp = OTPService.is_otp_required_for_operation(
                operation_type=operation_type,
                amount=amount
            )
            
            if not requires_otp:
                # OTP not required, proceed
                return f(*args, **kwargs)
            
            # Check for OTP session token
            session_token = request.headers.get('X-OTP-Session-Token') or \
                           request.json.get('otp_session_token') if request.json else None
            
            if not session_token:
                # OTP required but not provided - ask for OTP
                return jsonify({
                    'requires_otp': True,
                    'message': f'OTP verification required for {operation_type.replace("_", " ")}',
                    'operation': operation_type
                }), 403
            
            # Verify session token
            token_result = OTPService.verify_otp_session_token(
                session_token, 
                expected_operation=operation_type
            )
            
            if not token_result['success']:
                return jsonify({
                    'requires_otp': True,
                    'message': token_result['message'],
                    'operation': operation_type
                }), 403
            
            # Check if token belongs to current user
            if token_result['user_id'] != current_user.id:
                return jsonify({'message': 'Invalid OTP session'}), 403
            
            # OTP verified, proceed
            request.otp_verified = True
            request.otp_metadata = token_result.get('metadata', {})
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
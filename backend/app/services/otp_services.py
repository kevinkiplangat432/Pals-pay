import jwt
import uuid
from datetime import datetime, timedelta, timezone
from flask import current_app
from ..extensions import db
from app.models import User, AuditLog


class OTPService:
    """Service for handling OTP operations"""
    
    @staticmethod
    def generate_otp_session_token(user_id, operation, metadata=None, expires_minutes=5):
        """Generate a session token after OTP verification"""
        payload = {
            'user_id': user_id,
            'operation': operation,
            'session_id': str(uuid.uuid4()),
            'exp': datetime.now(timezone.utc) + timedelta(minutes=expires_minutes),
            'iat': datetime.now(timezone.utc),
            'metadata': metadata or {}
        }
        
        token = jwt.encode(
            payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        
        return token
    
    @staticmethod
    def verify_otp_session_token(token, expected_operation=None):
        """Verify OTP session token"""
        try:
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            
            # Check expiration
            if datetime.fromtimestamp(payload['exp'], tz=timezone.utc) < datetime.now(timezone.utc):
                return {'success': False, 'message': 'Session expired'}
            
            # Check operation if specified
            if expected_operation and payload['operation'] != expected_operation:
                return {'success': False, 'message': 'Invalid operation'}
            
            return {
                'success': True,
                'user_id': payload['user_id'],
                'operation': payload['operation'],
                'metadata': payload.get('metadata', {})
            }
            
        except jwt.ExpiredSignatureError:
            return {'success': False, 'message': 'Session expired'}
        except jwt.InvalidTokenError:
            return {'success': False, 'message': 'Invalid session token'}
    
    @staticmethod
    def send_otp_via_sms(user_id, operation_type, metadata=None):
        """Send OTP via SMS (simulated for MVP)"""
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'message': 'User not found'}
        
        # Generate OTP
        otp_code, error = user.generate_otp(expires_minutes=10)
        if error:
            return {'success': False, 'message': error}
        
        db.session.commit()
        
        # to do in prod, send via SMS gateway
        # For MVP, log to console
        current_app.logger.info(
            f"OTP for {user.phone_number} ({operation_type}): {otp_code}"
        )
        
        # Log OTP generation
        AuditLog.log_user_action(
            actor_id=user_id,
            action=f'otp.sent.{operation_type}',
            resource_type='user',
            resource_id=user_id,
            metadata={
                'operation': operation_type,
                'phone': user.phone_number,
                'metadata': metadata
            },
            status='success'
        )
        
        return {
            'success': True,
            'message': 'OTP sent successfully',
            'phone_last4': user.phone_number[-4:],
            'expires_in_minutes': 10
        }
    
    @staticmethod
    def verify_user_otp(user_id, otp_code, operation_type):
        """Verify user's OTP code"""
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'message': 'User not found'}
        
        # Verify OTP
        result = user.verify_otp(otp_code)
        if not result['success']:
            # Log failed attempt
            AuditLog.log_user_action(
                actor_id=user_id,
                action=f'otp.failed.{operation_type}',
                resource_type='user',
                resource_id=user_id,
                metadata={'operation': operation_type},
                status='failed'
            )
            db.session.commit()
            return result
        
        # Generate session token
        session_token = OTPService.generate_otp_session_token(
            user_id=user_id,
            operation=operation_type
        )
        
        # Log successful verification
        AuditLog.log_user_action(
            actor_id=user_id,
            action=f'otp.verified.{operation_type}',
            resource_type='user',
            resource_id=user_id,
            metadata={'operation': operation_type},
            status='success'
        )
        db.session.commit()
        
        return {
            'success': True,
            'message': 'OTP verified successfully',
            'session_token': session_token
        }
    
    @staticmethod
    def is_otp_required_for_operation(operation_type, amount=None):
        """Check if OTP is required for this operation"""
        # OTP rules based on operation type
        otp_rules = {
            # Account operations
            'account_verification': True,  # Always required for verification
            'change_password': True,       # Always required
            'change_phone': True,          # Always required
            'change_email': True,          # Always required
            
            # Transaction operations
            'transfer': lambda amt: True,  # All transfers need OTP
            'withdrawal': True,            # All withdrawals need OTP
            
            # Beneficiary operations
            'add_beneficiary': True,       # Always required
            
            # Admin operations
            'admin_reverse': True,         # Admin actions need OTP
            'admin_freeze': True,
        }
        
        rule = otp_rules.get(operation_type)
        
        if callable(rule):
            return rule(amount or 0)
        
        return rule or False
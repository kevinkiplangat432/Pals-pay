import jwt
import uuid
from datetime import datetime, timedelta, timezone
from flask import current_app, request
from ..extensions import db
from ..models import User, AuditLog

class OTPService:
    
    @staticmethod
    def generate_otp(user_id, operation_type, expires_minutes=10):
        user = User.query.get(user_id)
        if not user:
            return None
        
        from ..utils.otp import generate_otp
        otp_code = generate_otp()
        
        user.otp_code = otp_code
        user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
        user.otp_attempts = 0
        user.otp_operation = operation_type
        
        db.session.commit()
        
        return otp_code
    
    @staticmethod
    def verify_otp(user_id, operation_type, otp_code):
        user = User.query.get(user_id)
        if not user:
            return False
        
        if user.otp_locked_until and datetime.now(timezone.utc) < user.otp_locked_until:
            return False
        
        if not user.otp_code or not user.otp_expires_at:
            return False
        
        if datetime.now(timezone.utc) > user.otp_expires_at:
            return False
        
        if user.otp_code != otp_code:
            user.otp_attempts += 1
            
            if user.otp_attempts >= 3:
                user.otp_locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
            
            db.session.commit()
            return False
        
        user.otp_code = None
        user.otp_expires_at = None
        user.otp_attempts = 0
        user.otp_operation = None
        
        db.session.commit()
        return True
    
    @staticmethod
    def generate_otp_session_token(user_id, operation, metadata=None, expires_minutes=5):
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
        try:
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            
            if datetime.fromtimestamp(payload['exp'], tz=timezone.utc) < datetime.now(timezone.utc):
                return {'success': False, 'message': 'Session expired'}
            
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
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'message': 'User not found'}
        
        otp_code = OTPService.generate_otp(user_id, operation_type, expires_minutes=10)
        if not otp_code:
            return {'success': False, 'message': 'Failed to generate OTP'}
        
        from .notification_service import NotificationService
        NotificationService.send_verification_otp(
            user_id=user_id,
            otp=otp_code,
            channel='sms'
        )
        
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
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'message': 'User not found'}
        
        if not OTPService.verify_otp(user_id, operation_type, otp_code):
            AuditLog.log_user_action(
                actor_id=user_id,
                action=f'otp.failed.{operation_type}',
                resource_type='user',
                resource_id=user_id,
                metadata={'operation': operation_type},
                status='failed'
            )
            db.session.commit()
            return {'success': False, 'message': 'Invalid or expired OTP'}
        
        session_token = OTPService.generate_otp_session_token(
            user_id=user_id,
            operation=operation_type
        )
        
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
        otp_rules = {
            'account_verification': True,
            'change_password': True,
            'change_phone': True,
            'change_email': True,
            'local_transfer': lambda amt: True,
            'international_transfer': True,
            'withdrawal': True,
            'add_beneficiary': True,
            'admin_reverse': True,
            'admin_freeze': True,
            'login': lambda user, ip: OTPService.is_login_otp_required(user, ip)
        }
        
        rule = otp_rules.get(operation_type)
        
        if callable(rule):
            if operation_type == 'login':
                return rule
            return rule(amount or 0)
        
        return rule or False
    
    @staticmethod
    def is_login_otp_required(user, ip_address):
        # Always require OTP for login via email
        return True
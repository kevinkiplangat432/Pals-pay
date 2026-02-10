from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta, timezone
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
import re
import uuid

from ..models.user import User
from ..models.audit_log import AuditLog
from ..models.account import Account
from ..models.user_account import UserAccount
from ..extensions import db
from ..services.otp_services import OTPService
from ..services.notification_service import NotificationService
from ..services.region_service import RegionService
from .decorators import token_required

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

PHONE_REGEX = r'^\+?[1-9]\d{1,14}$'  # E.164 format: optional +, followed by country code and subscriber number, total length up to 15 digits. This regex allows for international phone numbers with an optional leading + sign, ensuring that the number starts with a non-zero digit and is between 2 and 15 digits long (including country code). It does not allow for spaces, dashes, or parentheses, which are often used in formatted phone numbers, so the frontend should ensure that the phone number is sent in a clean format without any formatting characters.

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    name = data.get('name', '')
    email = data.get('email')
    password = data.get('password')
    phone_number = data.get('phone_number')
    country_code = data.get('country_code', 'KE')
    account_type = data.get('account_type', 'individual')
    
    if not RegionService.is_country_supported(country_code):
        return jsonify({'message': 'Country not supported'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already registered'}), 400
    
    if not name:
        return jsonify({'message': 'Name is required'}), 400

    name_parts = name.split(' ', 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ''
    
    region = RegionService.get_region_by_country(country_code)
    
    try:
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            username=email.split('@')[0],
            phone_number=phone_number,
            country_code=country_code,
            region=region,
            is_active=True,
            is_verified=False
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.flush()
        
        account = Account(
            account_type=account_type,
            legal_name=f"{first_name} {last_name}",
            primary_email=email,
            primary_phone=phone_number,
            country_of_incorporation=country_code,
            kyc_status='pending'
        )
        
        db.session.add(account)
        db.session.flush()
        
        user_account = UserAccount(
            user_id=user.id,
            account_id=account.id,
            role='owner',
            is_primary=True,
            is_active=True
        )
        
        db.session.add(user_account)
        
        otp = OTPService.generate_otp(user.id, 'email_verification')
        
        notification_preferences = {
            'email': data.get('notify_email', True),
            'sms': data.get('notify_sms', True),
            'whatsapp': data.get('notify_whatsapp', False)
        }
        
        NotificationService.send_verification_otp(
            user_id=user.id,
            otp=otp,
            channel='email',
            preferences=notification_preferences
        )
        
        db.session.commit()
        
        access_token = create_access_token(  # The access token is created with the user's ID as the identity and additional claims that include the user's admin status, KYC status, and account ID. This allows the frontend to easily access this information from the token without needing to make additional API calls to get the user's details. The token can be used for authenticated requests to protected endpoints in the API.
            identity=str(user.id),
            additional_claims={
                'type': 'access',
                'is_admin': user.is_admin,
                'kyc_status': user.kyc_status.value,
                'account_id': account.id
            }
        )
        
        refresh_token = create_refresh_token(identity=str(user.id))  #refresh token is created with the user's ID as the identity. The refresh token can be used to obtain a new access token when the current access token expires, allowing the user to stay logged in without having to re-enter their credentials. The refresh token should be stored securely on the client side and sent to the /refresh endpoint when the access token needs to be renewed.
        
        AuditLog.log_user_action(
            actor_id=user.id,
            action='user_registered',
            resource_type='user',
            resource_id=user.id,
            actor_ip=request.remote_addr,
            user_agent=request.user_agent.string
        )
        
        return jsonify({
            'message': 'Registration successful. Please verify your email.',
            'user': user.to_dict(include_accounts=True),
            'access_token': access_token,
            'refresh_token': refresh_token,
            'requires_verification': True
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Registration error: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'message': 'Registration failed', 'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or ('email' not in data and 'phone_number' not in data) or 'password' not in data:
        return jsonify({'message': 'Missing email/phone or password'}), 400
    
    if 'email' in data:
        user = User.query.filter_by(email=data['email']).first()
    else:
        user = User.query.filter_by(phone_number=data['phone_number']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    if not user.is_active:
        return jsonify({'message': 'Account is deactivated'}), 403
    
    user.last_login_at = datetime.now(timezone.utc)
    
    ip_address = request.remote_addr
    user_agent = request.user_agent.string
    
    if OTPService.is_login_otp_required(user, ip_address):
        otp = OTPService.generate_otp(user.id, 'login')
        NotificationService.send_login_otp(
            user_id=user.id,
            otp=otp,
            ip_address=ip_address
        )
        
        db.session.commit()
        
        return jsonify({
            'requires_otp': True,
            'message': 'Login OTP sent',
            'user_id': user.id
        }), 200
    
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            'type': 'access',
            'is_admin': user.is_admin,
            'kyc_status': user.kyc_status.value,
            'kyc_level': user.kyc_level,
            'account_id': user.primary_account.id if user.primary_account else None
        }
    )
    
    refresh_token = create_refresh_token(identity=str(user.id))
    
    AuditLog.log_user_action(
        actor_id=user.id,
        action='user_login',
        resource_type='user',
        resource_id=user.id,
        actor_ip=ip_address,
        user_agent=user_agent
    )
    
    db.session.commit()
    
    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(include_wallet=True, include_accounts=True),
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].seconds
    }), 200

@auth_bp.route('/login/verify-otp', methods=['POST'])
def verify_login_otp():
    data = request.get_json()
    
    user_id = data.get('user_id')
    otp_code = data.get('otp_code')
    
    if not user_id or not otp_code:
        return jsonify({'message': 'User ID and OTP code required'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    result = OTPService.verify_user_otp(
        user_id=user.id,
        otp_code=otp_code,
        operation_type='login'
    )
    
    if not result['success']:
        return jsonify({'message': result['message']}), 400
    
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            'type': 'access',
            'is_admin': user.is_admin,
            'kyc_status': user.kyc_status.value,
            'kyc_level': user.kyc_level,
            'account_id': user.primary_account.id if user.primary_account else None
        }
    )
    
    refresh_token = create_refresh_token(identity=str(user.id))
    
    AuditLog.log_user_action(
        actor_id=user.id,
        action='user_login_otp',
        resource_type='user',
        resource_id=user.id,
        actor_ip=request.remote_addr,
        status='success'
    )
    
    return jsonify({
        'message': 'OTP verified successfully',
        'user': user.to_dict(include_wallet=True, include_accounts=True),
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].seconds
    }), 200

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.is_active:
        return jsonify({'message': 'User not found or inactive'}), 401
    
    new_access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            'type': 'access',
            'is_admin': user.is_admin,
            'kyc_status': user.kyc_status.value,
            'kyc_level': user.kyc_level,
            'account_id': user.primary_account.id if user.primary_account else None
        }
    )
    
    return jsonify({
        'access_token': new_access_token,
        'token_type': 'Bearer',
        'expires_in': current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].seconds
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    user_id = request.current_user.id
    
    AuditLog.log_user_action(
        actor_id=user_id,
        action='user_logout',
        resource_type='user',
        resource_id=user_id,
        actor_ip=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    return jsonify({'message': 'Logout successful'}), 200

@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    data = request.get_json()
    
    if not data or 'email' not in data or 'otp' not in data:
        return jsonify({'message': 'Missing email or OTP'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    if user.is_verified:
        return jsonify({'message': 'Email already verified'}), 200
    
    if not OTPService.verify_otp(user.id, 'email_verification', data['otp']):
        return jsonify({'message': 'Invalid or expired OTP'}), 400
    
    user.is_verified = True
    
    NotificationService.send_welcome_notification(
        user_id=user.id,
        channel='email'
    )
    
    db.session.commit()
    
    AuditLog.log_user_action(
        actor_id=user.id,
        action='email_verified',
        resource_type='user',
        resource_id=user.id
    )
    
    return jsonify({
        'message': 'Email verified successfully',
        'user': user.to_dict()
    }), 200

@auth_bp.route('/verify-phone', methods=['POST'])
@token_required
def verify_phone():
    data = request.get_json()
    
    if not data or 'otp' not in data:
        return jsonify({'message': 'Missing OTP'}), 400
    
    user = request.current_user
    
    if not OTPService.verify_otp(user.id, 'phone_verification', data['otp']):
        return jsonify({'message': 'Invalid or expired OTP'}), 400
    
    AuditLog.log_user_action(
        actor_id=user.id,
        action='phone_verified',
        resource_type='user',
        resource_id=user.id
    )
    
    return jsonify({
        'message': 'Phone verification completed',
        'user': user.to_dict()
    }), 200

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    
    if not data or ('email' not in data and 'phone_number' not in data):
        return jsonify({'message': 'Missing email or phone number'}), 400
    
    if 'email' in data:
        user = User.query.filter_by(email=data['email']).first()
    else:
        user = User.query.filter_by(phone_number=data['phone_number']).first()
    
    if not user:
        return jsonify({
            'message': 'If your account exists, you will receive a reset code'
        }), 200
    
    otp = OTPService.generate_otp(user.id, 'password_reset')
    
    if 'email' in data:
        NotificationService.send_password_reset_otp(
            user_id=user.id,
            otp=otp,
            channel='email'
        )
    else:
        NotificationService.send_password_reset_otp(
            user_id=user.id,
            otp=otp,
            channel='sms'
        )
    
    AuditLog.log_user_action(
        actor_id=user.id,
        action='password_reset_requested',
        resource_type='user',
        resource_id=user.id,
        actor_ip=request.remote_addr
    )
    
    return jsonify({
        'message': 'Reset code sent successfully',
        'method': 'email' if 'email' in data else 'sms'
    }), 200

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    
    required_fields = ['email', 'otp', 'new_password']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing required field: {field}'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    if not OTPService.verify_otp(user.id, 'password_reset', data['otp']):
        return jsonify({'message': 'Invalid or expired OTP'}), 400
    
    if len(data['new_password']) < 8:
        return jsonify({'message': 'Password must be at least 8 characters'}), 400
    
    user.set_password(data['new_password'])
    
    NotificationService.send_password_changed_notification(
        user_id=user.id,
        channel='email'
    )
    
    db.session.commit()
    
    AuditLog.log_user_action(
        actor_id=user.id,
        action='password_reset',
        resource_type='user',
        resource_id=user.id
    )
    
    return jsonify({'message': 'Password reset successfully'}), 200

@auth_bp.route('/countries', methods=['GET'])
def get_supported_countries():
    countries = RegionService.get_supported_countries()
    
    country_data = []
    country_info = {
        'KE': {'name': 'Kenya', 'flag': '🇰🇪', 'dialing_code': '+254'},
        'TZ': {'name': 'Tanzania', 'flag': '🇹🇿', 'dialing_code': '+255'},
        'UG': {'name': 'Uganda', 'flag': '🇺🇬', 'dialing_code': '+256'},
        'RW': {'name': 'Rwanda', 'flag': '🇷🇼', 'dialing_code': '+250'},
        'NG': {'name': 'Nigeria', 'flag': '🇳🇬', 'dialing_code': '+234'},
        'GH': {'name': 'Ghana', 'flag': '🇬🇭', 'dialing_code': '+233'},
        'ZA': {'name': 'South Africa', 'flag': '🇿🇦', 'dialing_code': '+27'},
        'US': {'name': 'United States', 'flag': '🇺🇸', 'dialing_code': '+1'},
        'GB': {'name': 'United Kingdom', 'flag': '🇬🇧', 'dialing_code': '+44'},
        'IN': {'name': 'India', 'flag': '🇮🇳', 'dialing_code': '+91'},
        'CN': {'name': 'China', 'flag': '🇨🇳', 'dialing_code': '+86'},
        'AE': {'name': 'UAE', 'flag': '🇦🇪', 'dialing_code': '+971'},
    }
    
    for code in countries:
        info = country_info.get(code, {'name': code, 'flag': '', 'dialing_code': ''})
        country_data.append({
            'code': code,
            'name': info['name'],
            'flag': info['flag'],
            'dialing_code': info['dialing_code'],
            'supported': True
        })
    
    return jsonify({
        'countries': country_data,
        'count': len(countries)
    }), 200

@auth_bp.route('/currencies', methods=['GET'])
def get_supported_currencies():
    from ..services.currency_service import CurrencyService
    
    currencies = ['KES', 'USD', 'EUR', 'GBP', 'NGN', 'GHS', 'ZAR', 'UGX', 'TZS', 'RWF']
    
    currency_data = []
    for code in currencies:
        currency_data.append({
            'code': code,
            'name': CurrencyService.get_currency_name(code),
            'symbol': CurrencyService.get_currency_symbol(code),
            'supported': True
        })
    
    return jsonify({
        'currencies': currency_data,
        'count': len(currencies)
    }), 200
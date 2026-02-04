from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import jwt
from ..models.user import User
from ..extensions import db
from .decorators import token_required
from app.utils.otp import generate_otp  
from app.services.region_service import RegionService

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
otp=generate_otp  #import otp generator function


#register a new user
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Required fields
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    phone_number = data.get('phone_number')
    country_code = data.get('country_code', 'KE')  # Default to Kenya
    
    # Validate country code
    if not RegionService.is_country_supported(country_code):
        return jsonify({'message': 'Country not supported'}), 400
    
    # Check if user exists
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'User already exists!'}), 400
    
    # Parse name into first and last
    name_parts = name.split(' ', 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ''
    
    # Get region based on country
    region = RegionService.get_region_by_country(country_code)
    
    # Create user
    new_user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        username=email.split('@')[0],  # Use email prefix as username
        phone_number=phone_number,
        country_code=country_code,
        region=region,
        is_active=True,
        is_verified=False  # Will verify via OTP
    )
    
    new_user.set_password(password)
    
    # Generate verification OTP
    otp_code = generate_otp()
    new_user.otp_code = otp_code
    new_user.otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    db.session.add(new_user)
    db.session.commit()
    
    # In production, send OTP via SMS/Email
    print(f"Verification OTP for {email}: {otp_code}")
    
    return jsonify({
        'message': 'User registered successfully! Please verify your account.',
        'user_id': new_user.id,
        'requires_verification': True
    }), 201

    
#login user and return JWT token
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({'message': 'Invalid credentials!'}), 401

    token = jwt.encode({  #create JWT token
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(hours=24)  #create token valid for 24 hours
    }, current_app.config['SECRET_KEY'], algorithm="HS256")  #code the token with secret key

    return jsonify({'token': token}), 200


#get user profile
@auth_bp.route('/profile', methods=['GET'])
@token_required
def profile(current_user):
    user_data = {
        'id': current_user.id,
        'name': current_user.name,
        'email': current_user.email,
        'is_active': current_user.is_active,
        'created_at': current_user.created_at
    }
    return jsonify(user_data), 200



#update user profile
@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')

    if name:
        current_user.name = name
    if email:
        if User.query.filter_by(email=email).first():
            return jsonify({'message': 'Email already in use!'}), 400
        current_user.email = email

    db.session.commit()

    return jsonify({'message': 'Profile updated successfully!'}), 200

#forgot password route
@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'message': 'User not found!'}), 404

    otp_code = otp()  #generate otp code
    user.reset_otp = otp_code  #store otp code
    user.reset_otp_expiration = datetime.utcnow() + timedelta(minutes=10)  #set otp expiration time
    user.reset_otp_used = False  #mark otp as unused
    db.session.commit()

    # In real application, send the OTP via email/SMS here

    return jsonify({'message': 'OTP sent to your email!'}), 200

#verify otp
@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get('email')
    otp_code = data.get('otp')

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'message': 'User not found!'}), 404

    if user.reset_otp_used:
        return jsonify({'message': 'OTP has already been used!'}), 400

    if user.reset_otp != otp_code:
        return jsonify({'message': 'Invalid OTP!'}), 400

    if datetime.utcnow() > user.reset_otp_expiration:
        return jsonify({'message': 'OTP has expired!'}), 400

    user.reset_otp_used = True  #mark otp as used
    db.session.commit()

    return jsonify({'message': 'OTP verified successfully!'}), 200

#reset password with otp
@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data.get('email')
    otp_code = data.get('otp')
    new_password = data.get('new_password')

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'message': 'User not found!'}), 404

    if user.reset_otp_used:
        return jsonify({'message': 'OTP has already been used!'}), 400

    if user.reset_otp != otp_code:
        return jsonify({'message': 'Invalid OTP!'}), 400

    if datetime.utcnow() > user.reset_otp_expiration:
        return jsonify({'message': 'OTP has expired!'}), 400

    user.set_password(new_password)  #set new password
    user.reset_otp_used = True  #mark otp as used
    db.session.commit()

    return jsonify({'message': 'Password reset successfully!'}), 200



@auth_bp.route('/countries', methods=['GET'])
def get_supported_countries():
    """Get list of supported countries"""
    countries = RegionService.get_supported_countries()
    
    # Add country names and flags
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
    }
    
    for code in countries:
        info = country_info.get(code, {'name': code, 'flag': '', 'dialing_code': ''})
        country_data.append({
            'code': code,
            'name': info['name'],
            'flag': info['flag'],
            'dialing_code': info['dialing_code']
        })
    
    return jsonify({
        'countries': country_data,
        'count': len(countries)
    }), 200

@auth_bp.route('/regions', methods=['GET'])
def get_active_regions():
    """Get active regions with details"""
    regions = RegionService.get_active_regions()
    
    region_data = []
    for key, config in regions.items():
        region_data.append({
            'key': key,
            'name': config.get('name', key),
            'countries': config.get('countries', []),
            'currencies': config.get('currencies', []),
            'default_currency': config.get('default_currency', 'USD'),
            'active': config.get('active', False)
        })
    
    return jsonify({
        'regions': region_data,
        'count': len(regions)
    }), 200
6
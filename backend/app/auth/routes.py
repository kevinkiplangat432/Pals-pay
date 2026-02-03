from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import jwt
from ..models.user import User
from ..extensions import db
from app.auth.decorators import token_required
from app.utils.otp import generate_otp  


auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
otp=generate_otp  #import otp generator function


#register a new user
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() #get user data from request
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if User.query.filter_by(email=email).first():  # Check if user already exists
        return jsonify({'message': 'User already exists!'}), 400

    new_user = User(name=name, email=email)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully!'}), 201
    
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
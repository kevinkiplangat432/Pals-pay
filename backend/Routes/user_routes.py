from flask import Blueprint, request, jsonify
# from server.extensions import db
# from server.models import User, Transaction, Wallet, Beneficiary
from server.auth import token_required
import re

user_bp = Blueprint('user_bp', __name__, url_prefix='/api/users')

# Number should optionally start with + and country code, followed by 10 to 12 digits or just 10 digits
PHONE_REGEX = r'^\+?1?\d{10,12}$'

# Profile after login

@user_bp.route('/user', methods=['GET'])
@token_required
def get_user():
    user = request.current_user
    return jsonify(user.to_dict()), 200

@user_bp.route('/user', methods=['PUT'])
@token_required
def update_user():
    user = request.current_user
    data = request.get_json()

    if 'username' in data and data['username'] is not None:
        user.username = data['username']

    if 'fullname' in data and data['fullname'] is not None:
        user.fullname = data['fullname']

    if 'phonenumber' in data :
        phonenumber = data.get('phonenumber')

    if phonenumber and not re.match(PHONE_REGEX, phonenumber):
        return jsonify({'message': 'Invalid phone number format Use format +2547XXXXXXXX'}), 400
    
    if phonenumber:
        existing = User.query.filter_by(User.phonenumber == phonenumber, User.id != user.id).first()
        if existing:
            return jsonify({'message': 'Phone number already registered'}), 400
        user.phonenumber = phonenumber

    if 'avatar_url' in data:
        user.avatar_url = data['avatar_url']

@user_bp.route('/user/change_pin', methods=['PUT'])
@token_required
def change_pin():
    user = request.current_user
    data = request.get_json()

    current_pin = data.get('current_pin')
    new_pin = data.get('new_pin')

    if not current_pin or not new_pin:
        return jsonify({'message': 'Current pin and new pin are required'}), 400
    if not user.check_pin(current_pin):
        return jsonify({'message': 'Current pin is incorrect'}), 400

    user.set_pin(data['new_pin'])
    db.session.commit()

    return jsonify({'message': 'Pin updated successfully'}), 200

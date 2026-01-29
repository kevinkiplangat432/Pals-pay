from flask import Blueprint, request, jsonify
from sqlalchemy import func
from backend.extensions import db
from app.models import User, Transaction, Wallet, Beneficiary
from server.auth import token_required
import re

beneficiaries_bp = Blueprint('beneficiaries_bp', __name__, url_prefix='/api/beneficiaries')

# Number should optionally start with + and country code, followed by 10 to 12 digits or just 10 digits
PHONE_REGEX = r'^\+?1?\d{10,12}$'


@beneficiaries_bp.route('/user/beneficiaries', methods=['GET'])
@token_required
def get_beneficiaries():
    user = request.current_user
    beneficiaries = Beneficiary.query.filter_by(user_id=user.id).all()
    return jsonify([b.to_dict() for b in beneficiaries]), 200

@beneficiaries_bp.route('/user/beneficiaries', methods=['POST'])
@token_required
def create_beneficiary():
    """
    Body: 
    External:{"name": "John Doe", "phonenumber": "+2547XXXXXXXX"} (outside registered users)
    Internal:{"name": "Jane Doe", "recipient_user_id": 2, "phonenumber": "+2547XXXXXXXX"} (registered users)
    """
    user = request.current_user
    data = request.get_json()

    name = data.get('name')
    phonenumber = data.get('phonenumber')
    recipient_user_id = data.get('recipient_user_id')

    if not name:
        return jsonify({'message': 'Name is required'}), 400

    if recipient_user_id:
        # Internal beneficiary

        if not re.match(PHONE_REGEX, phonenumber):
            return jsonify({'message': 'Invalid phone number format Use format +2547XXXXXXXX'}), 400
        
        recipient = User.query.get(recipient_user_id)
        if not recipient:
            return jsonify({'message': 'Recipient user not found'}), 404

        existing = Beneficiary.query.filter_by(user_id=user.id, recipient_user_id=recipient_user_id).first()
        if existing:
            return jsonify({'message': 'Beneficiary already exists'}), 400

        beneficiary = Beneficiary(
            user_id=user.id,
            name=name,
            recipient_user_id=recipient_user_id
        )
    elif phonenumber:
        # External beneficiary
        if not re.match(PHONE_REGEX, phonenumber):
            return jsonify({'message': 'Invalid phone number format Use format +2547XXXXXXXX'}), 400

        existing = Beneficiary.query.filter_by(user_id=user.id, phonenumber=phonenumber).first()
        if existing:
            return jsonify({'message': 'Beneficiary already exists'}), 400

        beneficiary = Beneficiary(
            user_id=user.id,
            name=name,
            phonenumber=phonenumber
        )
    else:
        return jsonify({'message': 'Either recipient_user_id or phonenumber is required'}), 400

    db.session.add(beneficiary)
    db.session.commit()

    return jsonify( {"message": "Beneficiary created successfully", "beneficiary": beneficiary.to_dict()}), 201




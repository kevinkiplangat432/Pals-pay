from flask import Blueprint, request, jsonify
from sqlalchemy import func
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

# WALLET

@user_bp.route('/user/wallet', methods=['GET'])
@token_required
def wallet_summary():
    user = request.current_user
    wallet = Wallet.query.filter_by(user_id=user.id).first()
    if not wallet:
        wallet = Wallet(user_id=user.id, balance=0)
        db.session.add(wallet)
        db.session.commit()

    return jsonify({'balance': float(wallet.balance)}), 200

@user_bp.route('/user/wallet/add-funds', methods=['POST'])
@token_required
def add_funds():
    """
    Body: {"amount": 1000, "source": "mpesa|card|bank", "note": "optional"}
    Postgres-safe:
    -lock wallet row for update(one update at a time)
    -update balance
    -create transaction (topup, has to make a transaction not just update balance)
    """

    user = request.current_user
    data = request.get_json()
    amount = data.get('amount')
    source = data.get('source')
    note = data.get('note', '')

    if not amount or amount <= 0:
        return jsonify({'message': 'Invalid amount'}), 400
    
    try:
        amount = float(amount)
    except ValueError:
        return jsonify({'message': 'Amount must be a number'}), 400
    
    if source not in ['mpesa', 'card', 'bank']:
        return jsonify({'message': 'Invalid source'}), 400

    try:
        with db.session.begin():
            wallet = (db.session.query(Wallet).filter(Wallet.user_id == user.id).with_for_update().one_or_none())
            if not wallet:
                wallet = Wallet(user_id=user.id, balance=0)
                db.session.add(wallet)
                db.session.flush()  # Save for now don't make permanent

                wallet.balance = (wallet.balance or 0) + amount
            transaction = Transaction(
                user_id=user.id,
                type='topup',
                amount=amount,
                source=source,
                note=note
            )
            db.session.add(transaction)

        return jsonify({'message': 'Funds added successfully', 'new_balance': float(wallet.balance)}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'An error occurred while adding funds', 'error': str(e)}), 500
    
@user_bp.route('/user/wallet/analytics', methods=['GET'])
@token_required
def wallet_analytics():
    user = request.current_user

    wallet = Wallet.query.filter_by(user_id=user.id).first()
    if not wallet:
        wallet = Wallet(user_id=user.id, balance=0)
        db.session.add(wallet)
        db.session.commit()
    
    # Calculate total money that entered the wallet
    total_in = db.session.query(
        func.coalesce(func.sum(Transaction.amount), 0.0)
    ).filter(
        Transaction.recipient_user_id == user.id,
        Transaction.status == 'success',
        Transaction.type.in_(['topup', 'transfer'])
    ).scalar() # return single value

    # Calculate total money that left the wallet
    total_out = db.session.query(
        func.coalesce(func.sum(Transaction.amount), 0.0)
    ).filter(
        Transaction.user_id == user.id,
        Transaction.status == 'success',
        Transaction.type.in_(['transfer'])
    ).scalar() # return single value

    return jsonify({
        'balance': float(wallet.balance),
        'total_in': float(total_in),
        'total_out': float(total_out)
    }), 200

# BENEFICIARIES

@user_bp.route('/user/beneficiaries', methods=['GET'])
@token_required
def get_beneficiaries():
    user = request.current_user
    beneficiaries = Beneficiary.query.filter_by(user_id=user.id).all()
    return jsonify([b.to_dict() for b in beneficiaries]), 200

@user_bp.route('/user/beneficiaries', methods=['POST'])
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




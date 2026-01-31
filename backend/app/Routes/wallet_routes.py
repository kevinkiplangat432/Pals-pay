from flask import Blueprint, request, jsonify
from decimal import Decimal
from backend.extensions import db
from app.models import Transaction, Wallet, Beneficiary
from server.auth import token_required
import re

wallet_bp = Blueprint('wallet_bp', __name__, url_prefix='/api/wallet')


@wallet_bp.route('/user/wallet', methods=['GET'])
@token_required
def wallet_summary():
    user = request.current_user
    wallet = Wallet.query.filter_by(user_id=user.id).first()
    if not wallet:
        wallet = Wallet(user_id=user.id)
        db.session.add(wallet)
        db.session.commit()

    return jsonify((wallet.to_dict())), 200

@wallet_bp.route('/user/wallet/add-funds', methods=['POST'])
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

    if not amount :
        return jsonify({'message': 'Amount is required'}), 400
    
    try:
        amount = Decimal(str(amount))
        if amount <= 0:
            return jsonify({'message': 'Amount must be positive'}), 400
    except ValueError:
        return jsonify({'message': 'Amount must be a number'}), 400
    
    if source not in ['mpesa', 'card', 'bank']:
        return jsonify({'message': 'Invalid source'}), 400

    try:
        with db.session.begin():
            wallet = (db.session.query(Wallet).filter(Wallet.user_id == user.id).with_for_update().one_or_none())
            if not wallet:
                wallet = Wallet(user_id=user.id)
                db.session.add(wallet)
                db.session.flush()  # Save for now don't make permanent

                wallet.balance += amount
            transaction = Transaction(
                sender_id=None,
                receiver_id=user.id,
                transaction_type='deposit',
                amount=amount,
                source=source,
                note=note,
                status= 'completed'
            )
            db.session.add(transaction)

        return jsonify({'message': 'Funds added successfully', 'new_balance': float(wallet.balance)}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'An error occurred while adding funds', 'error': str(e)}), 500

@wallet_bp.route('/user/wallet/analytics', methods=['GET'])
@token_required
def wallet_analytics():
    user = request.current_user

    wallet = Wallet.query.filter_by(user_id=user.id).first()
    if not wallet:
        wallet = Wallet(user_id=user.id, balance=0)
        db.session.add(wallet)
        db.session.commit()
    
    return jsonify(wallet.get_analytics()), 200

@wallet_bp.route('/user/wallet/transactions', methods=['POST'])
@token_required
def send_money():
    """
    Body: { "beneficiary_id": 2, "amount": 500, "reference": "optional"}

    """
    user = request.current_user
    data = request.get_json()

    beneficiary_id = data.get('beneficiary_id')
    amount = data.get('amount')
    reference = data.get('reference', '')

    if not beneficiary_id:
        return jsonify({'message': 'Beneficiary ID is required'}), 400
    if amount is None:
        return jsonify({'message': 'Amount is required'}), 400
    try:
        amount = Decimal(str(amount))
        if amount <= 0:
            return jsonify({'message': 'Amount must be positive'}), 400
    except ValueError:
        return jsonify({'message': 'Amount must be a number'}), 400
    
    if amount <= Decimal('0.00'):
        return jsonify({'message': 'Amount must be greater than zero'}), 400
    
    beneficiary = Beneficiary.query.filter_by(user_id=user.id, beneficiary_id=beneficiary_id).first()
    if not beneficiary:
        return jsonify({'message': 'Beneficiary not found'}), 404
    
    recipient_user_id = beneficiary.beneficiary_user.id

    sender_wallet = None

    try:
        with db.session.begin():
            sender_wallet = (
                db.session.query(Wallet).filter(Wallet.user_id == user.id).with_for_update().one_or_none()

            )
            if not sender_wallet:
                sender_wallet = Wallet(
                    user_id=user.id,
                    balance=Decimal('0.00')
                )
                db.session.add(sender_wallet)
                db.session.flush()  # Ensure wallet is saved before proceeding

            if sender_wallet.balance < amount:
                raise ValueError('Insufficient funds')
            
            recipient_wallet = (
                db.session.query(Wallet).filter(Wallet.user_id == recipient_user_id).with_for_update().one_or_none()    
            )
            if not recipient_wallet:
                recipient_wallet = Wallet(
                    user_id=recipient_user_id,
                    balance=Decimal('0.00')
                )
                db.session.add(recipient_wallet)
                db.session.flush()  # Ensure wallet is saved before proceeding

            sender_wallet.balance -= amount
            recipient_wallet.balance += amount

            transaction = Transaction(
                reference=reference,
                type='transfer',
                status='success',\
                amount=amount,
                sender_id=user.id,
                receiver_id=recipient_user_id
                beneficiary_id=beneficiary_id
            )
            db.session.add(transaction)

        return jsonify({'message': 'Transfer successful', 'new_balance': float(sender_wallet.balance)}), 200
    except ValueError as e:
        if str(e) == 'Insufficient funds':
            return jsonify({'message': 'Insufficient funds'}), 400
        return jsonify({'message': 'Transfer failed', 'error': str(e)}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'An error occurred during the transfer', 'error': str(e)}), 500

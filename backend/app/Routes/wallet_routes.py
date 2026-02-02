from flask import Blueprint, request, jsonify
from decimal import Decimal
from backend.extensions import db
from app.models import Transaction, Wallet
from app.auth import token_required
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



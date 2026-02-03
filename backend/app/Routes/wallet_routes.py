from flask import Blueprint, request, jsonify
from decimal import Decimal
from datetime import datetime
from ..extensions import db
from app.models import Wallet, Transaction, PaymentMethod
from app.models.enums import TransactionType, TransactionStatus, PaymentProvider
from app.auth.decorators import token_required, kyc_required, otp_required
from app.services.wallet_service import WalletService
from app.services.transaction_service import TransactionService
import uuid

wallet_bp = Blueprint('wallet', __name__, url_prefix='/api/wallet')


@wallet_bp.route('/summary', methods=['GET'])
@token_required
def wallet_summary(current_user):
    """Get wallet summary"""
    wallet = Wallet.query.filter_by(user_id=current_user.id).first()
    if not wallet:
        wallet = Wallet(user_id=current_user.id)
        db.session.add(wallet)
        db.session.commit()
    
    summary = WalletService.get_wallet_balance(current_user.id)
    
    return jsonify(summary), 200


@wallet_bp.route('/analytics', methods=['GET'])
@token_required
def wallet_analytics(current_user):
    """Get wallet analytics"""
    analytics = WalletService.get_wallet_analytics(current_user.id)
    
    return jsonify(analytics), 200


@wallet_bp.route('/deposit/mpesa', methods=['POST'])
@token_required
@kyc_required
def deposit_via_mpesa(current_user):
    """Deposit via MPesa"""
    data = request.get_json()
    
    amount = data.get('amount')
    phone_number = data.get('phone_number')
    
    if not amount or not phone_number:
        return jsonify({'message': 'Amount and phone number are required'}), 400
    
    try:
        amount = Decimal(str(amount))
        if amount <= 0:
            return jsonify({'message': 'Amount must be positive'}), 400
        if amount > Decimal('70000'):  # MPesa limit
            return jsonify({'message': 'Amount exceeds MPesa limit (70,000 KES)'}), 400
    except:
        return jsonify({'message': 'Invalid amount'}), 400
    
    # Initialize payment service
    from app import create_app
    from app.services.payment_service import DarajaPaymentService
    app = create_app()
    payment_service = DarajaPaymentService()
    payment_service.init_app(app)
    
    # Process deposit
    result = payment_service.process_deposit(
        user_id=current_user.id,
        amount=amount,
        phone_number=phone_number
    )
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@wallet_bp.route('/transfer', methods=['POST'])
@token_required
@kyc_required
@otp_required('transfer', 'amount')
def transfer_to_beneficiary(current_user):
    """Transfer to beneficiary with OTP verification"""
    data = request.get_json()
    
    beneficiary_wallet_id = data.get('beneficiary_wallet_id')
    amount = data.get('amount')
    description = data.get('description')
    
    if not beneficiary_wallet_id or not amount:
        return jsonify({'message': 'Beneficiary wallet ID and amount are required'}), 400
    
    # Process transfer
    result = TransactionService.create_transfer(
        sender_user_id=current_user.id,
        receiver_wallet_id=beneficiary_wallet_id,
        amount=amount,
        description=description
    )
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@wallet_bp.route('/transfer/phone', methods=['POST'])
@token_required
@kyc_required
@otp_required('transfer', 'amount')
def transfer_to_phone(current_user):
    """Transfer to phone number with OTP verification"""
    data = request.get_json()
    
    phone_number = data.get('phone_number')
    amount = data.get('amount')
    description = data.get('description')
    
    if not phone_number or not amount:
        return jsonify({'message': 'Phone number and amount are required'}), 400
    
    # Find user by phone number
    from app.models import User
    receiver_user = User.query.filter_by(phone_number=phone_number, is_active=True).first()
    if not receiver_user:
        return jsonify({'message': 'User with this phone number not found'}), 404
    
    # Get receiver's wallet
    receiver_wallet = Wallet.query.filter_by(user_id=receiver_user.id).first()
    if not receiver_wallet:
        return jsonify({'message': 'Receiver wallet not found'}), 404
    
    # Process transfer
    result = TransactionService.create_transfer(
        sender_user_id=current_user.id,
        receiver_wallet_id=receiver_wallet.id,
        amount=amount,
        description=description or f"Transfer to {phone_number}"
    )
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@wallet_bp.route('/withdraw', methods=['POST'])
@token_required
@kyc_required
@otp_required('withdrawal', 'amount')
def withdraw_funds(current_user):
    """Withdraw funds with OTP verification"""
    data = request.get_json()
    
    amount = data.get('amount')
    payment_method_id = data.get('payment_method_id')
    
    if not amount or not payment_method_id:
        return jsonify({'message': 'Amount and payment method are required'}), 400
    
    try:
        amount = Decimal(str(amount))
        if amount <= 0:
            return jsonify({'message': 'Amount must be positive'}), 400
    except:
        return jsonify({'message': 'Invalid amount'}), 400
    
    # Get payment method
    payment_method = PaymentMethod.query.filter_by(
        id=payment_method_id,
        user_id=current_user.id,
        is_verified=True
    ).first_or_404()
    
    # Get wallet
    wallet = Wallet.query.filter_by(user_id=current_user.id).first()
    if not wallet:
        return jsonify({'message': 'Wallet not found'}), 404
    
    # Check if sufficient balance
    if wallet.available_balance < amount:
        return jsonify({'message': 'Insufficient available balance'}), 400
    
    # Calculate fee
    fee = Transaction.calculate_fee(amount, 'withdrawal')
    total_debit = amount + fee
    
    if wallet.available_balance < total_debit:
        return jsonify({'message': 'Insufficient balance to cover amount and fee'}), 400
    
    try:
        with db.session.begin_nested():
            # Create withdrawal transaction
            transaction = Transaction(
                sender_wallet_id=wallet.id,
                receiver_wallet_id=None,
                external_receiver=payment_method.account_reference,
                amount=amount,
                fee=fee,
                net_amount=amount,
                transaction_type=TransactionType.withdrawal,
                status=TransactionStatus.pending,
                provider=payment_method.provider,
                description=f"Withdrawal to {payment_method.provider.value}",
                metadata={'payment_method_id': payment_method_id}
            )
            
            db.session.add(transaction)
            db.session.flush()
            
            # Create ledger entry
            from app.models import LedgerEntry
            ledger_entry = LedgerEntry(
                wallet_id=wallet.id,
                transaction_id=transaction.id,
                amount=-total_debit,
                balance_before=wallet.balance,
                balance_after=wallet.balance - total_debit,
                entry_type='debit',
                description=f"Withdrawal to {payment_method.provider.value}"
            )
            
            db.session.add(ledger_entry)
            
            # Update wallet balance
            wallet.balance -= total_debit
            wallet.available_balance -= total_debit
            wallet.last_transaction_at = datetime.utcnow()
            
            # Mark payment method as used
            payment_method.mark_as_used()
            
            # Update transaction status
            transaction.update_status(TransactionStatus.completed)
            
            # Log the action
            from app.models import AuditLog
            AuditLog.log_user_action(
                actor_id=current_user.id,
                action='withdrawal.create',
                resource_type='transaction',
                resource_id=transaction.id,
                new_values={'amount': float(amount), 'fee': float(fee), 'provider': payment_method.provider.value},
                status='success'
            )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Withdrawal initiated successfully',
            'transaction': transaction.to_dict(),
            'new_balance': float(wallet.balance)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Withdrawal failed: {str(e)}'}), 500


@wallet_bp.route('/transactions/summary', methods=['GET'])
@token_required
def transaction_summary(current_user):
    """Get transaction summary"""
    days = request.args.get('days', 30, type=int)
    
    summary = TransactionService.get_transaction_summary(current_user.id, days)
    
    return jsonify(summary), 200
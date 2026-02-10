from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from decimal import Decimal

from ..extensions import db
from ..models import Transaction, Wallet, PaymentMethod, AuditLog
from ..models.enums import TransactionStatus, TransactionType, PaymentProvider
from ..auth.decorators import token_required
from ..services.payment_service import PaymentService

payment_bp = Blueprint('payments', __name__, url_prefix='/api/v1/payments')

@payment_bp.route('/mpesa/deposit', methods=['POST'])
@token_required
def mpesa_deposit():
    data = request.get_json()  
    
    amount = data.get('amount')
    phone_number = data.get('phone_number')
    
    if not amount or not phone_number:
        return jsonify({'message': 'Amount and phone number required'}), 400
    
    user = request.current_user
    
    try:
        amount_decimal = Decimal(str(amount))
        if amount_decimal <= 0:
            return jsonify({'message': 'Amount must be positive'}), 400
        if amount_decimal > Decimal('70000'):
            return jsonify({'message': 'Amount exceeds MPesa limit (70,000 KES)'}), 400
    except:
        return jsonify({'message': 'Invalid amount'}), 400
    
    result = PaymentService.process_mpesa_deposit(
        user_id=user.id,
        amount=amount_decimal,
        phone_number=phone_number
    )
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@payment_bp.route('/mpesa/withdraw', methods=['POST'])
@token_required
def mpesa_withdraw():
    data = request.get_json()
    
    amount = data.get('amount')
    phone_number = data.get('phone_number')
    
    if not amount or not phone_number:
        return jsonify({'message': 'Amount and phone number required'}), 400
    
    user = request.current_user
    
    try:
        amount_decimal = Decimal(str(amount))
        if amount_decimal <= 0:
            return jsonify({'message': 'Amount must be positive'}), 400
    except:
        return jsonify({'message': 'Invalid amount'}), 400
    
    wallet = Wallet.query.filter_by(user_id=user.id).first()
    if not wallet:
        return jsonify({'message': 'Wallet not found'}), 404
    
    if wallet.available_balance < amount_decimal:
        return jsonify({'message': 'Insufficient balance'}), 400
    
    result = PaymentService.process_mpesa_withdrawal(
        user_id=user.id,
        amount=amount_decimal,
        phone_number=phone_number
    )
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@payment_bp.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    try:
        data = request.get_json()
        current_app.logger.info(f"MPesa Callback Received: {data}")
        
        callback_data = data.get('Body', {}).get('stkCallback', {})  # a callback is a confirmation of payment
        checkout_request_id = callback_data.get('CheckoutRequestID')
        result_code = callback_data.get('ResultCode')
        result_desc = callback_data.get('ResultDesc')
        callback_metadata = callback_data.get('CallbackMetadata', {})
        
        transaction = Transaction.query.filter_by(
            external_reference=checkout_request_id
        ).first()
        
        if not transaction:
            current_app.logger.error(f"Transaction not found for checkout ID: {checkout_request_id}")
            return jsonify({'ResultCode': 0, 'ResultDesc': 'Transaction not found'})
        
        if result_code == 0:
            metadata_items = {}
            if callback_metadata and 'Item' in callback_metadata:
                for item in callback_metadata['Item']:
                    metadata_items[item.get('Name')] = item.get('Value')
            
            amount = metadata_items.get('Amount')
            mpesa_receipt = metadata_items.get('MpesaReceiptNumber')
            phone_number = metadata_items.get('PhoneNumber')
            
            transaction.status = TransactionStatus.completed
            transaction.external_reference = mpesa_receipt
            transaction.metadata = {
                **transaction.metadata,
                'callback_data': callback_data,
                'phone_number': phone_number
            }
            
            if transaction.receiver_wallet:
                transaction.receiver_wallet.balance += transaction.amount
                transaction.receiver_wallet.available_balance += transaction.amount
                transaction.receiver_wallet.last_transaction_at = datetime.utcnow()
            
            AuditLog.log_system_action(
                action='payment.mpesa.success',
                resource_type='transaction',
                resource_id=transaction.id,
                metadata={
                    'amount': amount,
                    'receipt': mpesa_receipt,
                    'phone': phone_number
                },
                status='success'
            )
            
            current_app.logger.info(f"Payment successful: {mpesa_receipt}")
        else:
            transaction.status = TransactionStatus.failed
            transaction.metadata = {
                **transaction.metadata,
                'callback_data': callback_data,  # Storing the full callback data will help us debug and analyze failed payments in the future
                'failure_reason': result_desc  # This will help us understand why the payment failed and take appropriate actions
            }
            
            AuditLog.log_system_action(
                action='payment.mpesa.failed',
                resource_type='transaction',
                resource_id=transaction.id,
                metadata={'reason': result_desc},
                status='failed'
            )
            
            current_app.logger.error(f"Payment failed: {result_desc}")
        
        db.session.commit()
        
        return jsonify({'ResultCode': 0, 'ResultDesc': 'Callback processed successfully'})
        
    except Exception as e:
        current_app.logger.error(f"Error processing MPesa callback: {str(e)}")
        return jsonify({'ResultCode': 1, 'ResultDesc': f'Error: {str(e)}'}), 500

@payment_bp.route('/bank/deposit', methods=['POST'])
@token_required
def bank_deposit():
    data = request.get_json()
    
    amount = data.get('amount')
    bank_account_id = data.get('bank_account_id')
    
    if not amount or not bank_account_id:
        return jsonify({'message': 'Amount and bank account ID required'}), 400
    
    user = request.current_user
    
    payment_method = PaymentMethod.query.filter_by(
        id=bank_account_id,
        user_id=user.id,
        provider=PaymentProvider.bank,
        is_verified=True
    ).first()
    
    if not payment_method:
        return jsonify({'message': 'Bank account not found or not verified'}), 404
    
    try:
        amount_decimal = Decimal(str(amount))
        if amount_decimal <= 0:
            return jsonify({'message': 'Amount must be positive'}), 400
    except:
        return jsonify({'message': 'Invalid amount'}), 400
    
    result = PaymentService.process_bank_deposit(
        user_id=user.id,
        amount=amount_decimal,
        bank_account_id=bank_account_id
    )
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@payment_bp.route('/bank/withdraw', methods=['POST'])
@token_required
def bank_withdraw():
    data = request.get_json()
    
    amount = data.get('amount')
    bank_account_id = data.get('bank_account_id')
    
    if not amount or not bank_account_id:
        return jsonify({'message': 'Amount and bank account ID required'}), 400
    
    user = request.current_user
    
    payment_method = PaymentMethod.query.filter_by(
        id=bank_account_id,
        user_id=user.id,
        provider=PaymentProvider.bank,
        is_verified=True
    ).first()
    
    if not payment_method:
        return jsonify({'message': 'Bank account not found or not verified'}), 404
    
    wallet = Wallet.query.filter_by(user_id=user.id).first()
    if not wallet:
        return jsonify({'message': 'Wallet not found'}), 404
    
    try:
        amount_decimal = Decimal(str(amount))
        if amount_decimal <= 0:
            return jsonify({'message': 'Amount must be positive'}), 400
    except:
        return jsonify({'message': 'Invalid amount'}), 400
    
    if wallet.available_balance < amount_decimal:
        return jsonify({'message': 'Insufficient balance'}), 400
    
    result = PaymentService.process_bank_withdrawal(
        user_id=user.id,
        amount=amount_decimal,
        bank_account_id=bank_account_id
    )
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@payment_bp.route('/card/deposit', methods=['POST'])
@token_required
def card_deposit():
    data = request.get_json()
    
    amount = data.get('amount')
    card_token = data.get('card_token')  # In a real implementation, this would be a token representing the card details securely stored by a payment gateway like Stripe or PayPal. The frontend would send this token after the user enters their card details and the payment gateway processes it.
    
    if not amount or not card_token:
        return jsonify({'message': 'Amount and card token required'}), 400
    
    user = request.current_user
    
    try:
        amount_decimal = Decimal(str(amount))
        if amount_decimal <= 0:
            return jsonify({'message': 'Amount must be positive'}), 400
    except:
        return jsonify({'message': 'Invalid amount'}), 400
    
    result = PaymentService.process_card_deposit(
        user_id=user.id,
        amount=amount_decimal,
        card_token=card_token
    )
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@payment_bp.route('/status/<string:reference>', methods=['GET'])
@token_required
def get_payment_status(reference):
    user = request.current_user
    
    transaction = Transaction.query.filter_by(
        external_reference=reference  # The external_reference field is used to store the unique identifier from the payment provider (e.g., MPesa receipt number, Stripe charge ID, etc.) that we can use to look up the transaction in our system when the user wants to check the status of their payment. This allows us to correlate the payment provider's data with our internal transaction records.
    ).first()
    
    if not transaction:
        return jsonify({'message': 'Transaction not found'}), 404
    
    if transaction.sender_wallet and transaction.sender_wallet.user_id != user.id:
        if transaction.receiver_wallet and transaction.receiver_wallet.user_id != user.id:
            return jsonify({'message': 'Unauthorized access'}), 403
    
    return jsonify({
        'status': transaction.status.value,
        'amount': float(transaction.amount),
        'currency': transaction.sender_currency if transaction.sender_currency else 'KES',
        'reference': transaction.external_reference,
        'created_at': transaction.created_at.isoformat() if transaction.created_at else None,
        'completed_at': transaction.completed_at.isoformat() if transaction.completed_at else None
    }), 200
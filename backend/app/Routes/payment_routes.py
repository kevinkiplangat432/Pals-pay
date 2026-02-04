# Routes/payment_routes.py - NEW FILE
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from ..extensions import db
from app.models import Transaction, AuditLog
from app.models.enums import TransactionStatus
from ..auth.decorators import token_required
from app.services.transaction_service import TransactionService

payment_bp = Blueprint('payments', __name__, url_prefix='/api/payments')

@payment_bp.route('/mpesa-callback', methods=['POST'])
def mpesa_callback():
    """Handle M-Pesa STK Push callback"""
    try:
        data = request.get_json()
        current_app.logger.info(f"MPesa Callback Received: {data}")
        
        # Parse callback data
        callback_data = data.get('Body', {}).get('stkCallback', {})
        checkout_request_id = callback_data.get('CheckoutRequestID')
        result_code = callback_data.get('ResultCode')
        result_desc = callback_data.get('ResultDesc')
        callback_metadata = callback_data.get('CallbackMetadata', {})
        
        # Find transaction
        transaction = Transaction.query.filter_by(
            external_reference=checkout_request_id
        ).first()
        
        if not transaction:
            current_app.logger.error(f"Transaction not found for checkout ID: {checkout_request_id}")
            return jsonify({'ResultCode': 0, 'ResultDesc': 'Transaction not found'})
        
        if result_code == 0:
            # Payment successful
            # Extract payment details
            metadata_items = {}
            if callback_metadata and 'Item' in callback_metadata:
                for item in callback_metadata['Item']:
                    metadata_items[item.get('Name')] = item.get('Value')
            
            amount = metadata_items.get('Amount')
            mpesa_receipt = metadata_items.get('MpesaReceiptNumber')
            phone_number = metadata_items.get('PhoneNumber')
            
            # Update transaction
            transaction.status = TransactionStatus.completed
            transaction.external_reference = mpesa_receipt
            transaction.metadata = {
                **transaction.metadata,
                'callback_data': callback_data,
                'phone_number': phone_number
            }
            
            # Update wallet balance
            if transaction.receiver_wallet:
                transaction.receiver_wallet.balance += transaction.amount
                transaction.receiver_wallet.available_balance += transaction.amount
                transaction.receiver_wallet.last_transaction_at = datetime.utcnow()
            
            # Log success
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
            # Payment failed
            transaction.status = TransactionStatus.failed
            transaction.metadata = {
                **transaction.metadata,
                'callback_data': callback_data,
                'failure_reason': result_desc
            }
            
            # Log failure
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
from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models import Transaction, Wallet
from ..models.enums import TransactionStatus, TransactionType, PaymentProvider
from decimal import Decimal
import logging

mpesa_bp = Blueprint('mpesa', __name__, url_prefix='/api/v1/mpesa')

logger = logging.getLogger(__name__)


@mpesa_bp.route('/callback', methods=['POST'])
def stk_callback():
    """Handle M-Pesa STK Push callback"""
    data = request.get_json()
    logger.info(f"M-Pesa STK Callback: {data}")
    
    try:
        body = data.get('Body', {}).get('stkCallback', {})
        result_code = body.get('ResultCode')
        checkout_request_id = body.get('CheckoutRequestID')
        
        # Find transaction by checkout_request_id stored in meta_data
        transaction = Transaction.query.filter(
            Transaction.meta_data['checkout_request_id'].astext == checkout_request_id
        ).first()
        
        if not transaction:
            logger.error(f"Transaction not found for CheckoutRequestID: {checkout_request_id}")
            return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'}), 200
        
        if result_code == 0:
            # Payment successful
            callback_metadata = body.get('CallbackMetadata', {}).get('Item', [])
            mpesa_receipt = None
            phone_number = None
            
            for item in callback_metadata:
                if item.get('Name') == 'MpesaReceiptNumber':
                    mpesa_receipt = item.get('Value')
                elif item.get('Name') == 'PhoneNumber':
                    phone_number = item.get('Value')
            
            # Update transaction
            transaction.status = TransactionStatus.completed
            transaction.external_reference = mpesa_receipt
            if transaction.meta_data:
                transaction.meta_data['mpesa_receipt'] = mpesa_receipt
                transaction.meta_data['phone_number'] = phone_number
            else:
                transaction.meta_data = {
                    'mpesa_receipt': mpesa_receipt,
                    'phone_number': phone_number
                }
            
            # Credit wallet
            wallet = transaction.receiver_wallet
            wallet.balance += transaction.net_amount
            
            db.session.commit()
            logger.info(f"Transaction {transaction.id} completed successfully")
        else:
            # Payment failed
            transaction.status = TransactionStatus.failed
            if transaction.meta_data:
                transaction.meta_data['failure_reason'] = body.get('ResultDesc')
            else:
                transaction.meta_data = {'failure_reason': body.get('ResultDesc')}
            db.session.commit()
            logger.warning(f"Transaction {transaction.id} failed: {body.get('ResultDesc')}")
        
        return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'}), 200
        
    except Exception as e:
        logger.error(f"Error processing M-Pesa callback: {str(e)}")
        return jsonify({'ResultCode': 1, 'ResultDesc': 'Failed'}), 500


@mpesa_bp.route('/b2c/result', methods=['POST'])
def b2c_result():
    """Handle M-Pesa B2C result callback"""
    data = request.get_json()
    logger.info(f"M-Pesa B2C Result: {data}")
    
    try:
        result = data.get('Result', {})
        result_code = result.get('ResultCode')
        conversation_id = result.get('ConversationID')
        
        # Find transaction by conversation_id
        transaction = Transaction.query.filter(
            Transaction.meta_data['conversation_id'].astext == conversation_id
        ).first()
        
        if not transaction:
            logger.error(f"Transaction not found for ConversationID: {conversation_id}")
            return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'}), 200
        
        if result_code == 0:
            # Payout successful
            result_parameters = result.get('ResultParameters', {}).get('ResultParameter', [])
            receipt_number = None
            
            for param in result_parameters:
                if param.get('Key') == 'TransactionReceipt':
                    receipt_number = param.get('Value')
            
            transaction.status = TransactionStatus.completed
            transaction.external_reference = receipt_number
            db.session.commit()
            logger.info(f"B2C Transaction {transaction.id} completed")
        else:
            # Payout failed
            transaction.status = TransactionStatus.failed
            if transaction.meta_data:
                transaction.meta_data['failure_reason'] = result.get('ResultDesc')
            else:
                transaction.meta_data = {'failure_reason': result.get('ResultDesc')}
            
            # Refund sender wallet
            sender_wallet = transaction.sender_wallet
            sender_wallet.balance += transaction.amount
            
            db.session.commit()
            logger.warning(f"B2C Transaction {transaction.id} failed")
        
        return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'}), 200
        
    except Exception as e:
        logger.error(f"Error processing B2C result: {str(e)}")
        return jsonify({'ResultCode': 1, 'ResultDesc': 'Failed'}), 500


@mpesa_bp.route('/b2c/timeout', methods=['POST'])
def b2c_timeout():
    """Handle M-Pesa B2C timeout"""
    data = request.get_json()
    logger.warning(f"M-Pesa B2C Timeout: {data}")
    return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'}), 200


@mpesa_bp.route('/validation', methods=['POST'])
def validation():
    """C2B Validation endpoint"""
    data = request.get_json()
    logger.info(f"M-Pesa Validation: {data}")
    # Accept all transactions
    return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'}), 200


@mpesa_bp.route('/confirmation', methods=['POST'])
def confirmation():
    """C2B Confirmation endpoint"""
    data = request.get_json()
    logger.info(f"M-Pesa Confirmation: {data}")
    
    try:
        trans_id = data.get('TransID')
        amount = Decimal(str(data.get('TransAmount', 0)))
        phone = data.get('MSISDN')
        bill_ref_number = data.get('BillRefNumber')
        
        # Find user wallet by phone or bill reference
        wallet = Wallet.query.join(Wallet.user).filter(
            (Wallet.user.phone_number == phone) | 
            (Wallet.user.username == bill_ref_number)
        ).first()
        
        if wallet:
            # Create transaction
            transaction = Transaction(
                receiver_wallet_id=wallet.id,
                amount=amount,
                net_amount=amount,
                transaction_type=TransactionType.deposit,
                status=TransactionStatus.completed,
                provider=PaymentProvider.mpesa,
                external_reference=trans_id,
                metadata={'phone': phone, 'bill_ref': bill_ref_number}
            )
            
            # Credit wallet
            wallet.balance += amount
            
            db.session.add(transaction)
            db.session.commit()
            logger.info(f"C2B payment processed: {trans_id}")
        
        return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'}), 200
        
    except Exception as e:
        logger.error(f"Error processing C2B confirmation: {str(e)}")
        return jsonify({'ResultCode': 1, 'ResultDesc': 'Failed'}), 500

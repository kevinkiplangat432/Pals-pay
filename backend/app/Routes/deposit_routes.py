from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models import Transaction, Wallet
from ..models.enums import TransactionStatus, TransactionType, PaymentProvider
from ..auth.decorators import token_required
from ..services.mpesa_service import MpesaService
from decimal import Decimal

deposit_bp = Blueprint('deposit', __name__, url_prefix='/api/v1/deposit')


@deposit_bp.route('/mpesa', methods=['POST'])
@token_required
def deposit_via_mpesa(current_user):
    """Initiate M-Pesa STK Push for deposit"""
    data = request.get_json()
    
    amount = data.get('amount')
    phone_number = data.get('phone_number', current_user.phone_number)
    
    if not amount or Decimal(str(amount)) <= 0:
        return jsonify({'message': 'Invalid amount'}), 400
    
    wallet = current_user.wallet
    if not wallet:
        return jsonify({'message': 'Wallet not found'}), 404
    
    try:
        # Create pending transaction
        transaction = Transaction(
            receiver_wallet_id=wallet.id,
            amount=Decimal(str(amount)),
            net_amount=Decimal(str(amount)),
            transaction_type=TransactionType.deposit,
            status=TransactionStatus.pending,
            provider=PaymentProvider.mpesa,
            metadata={'description': f"M-Pesa deposit to wallet"}
        )
        
        db.session.add(transaction)
        db.session.flush()
        
        # Initiate STK Push
        response = MpesaService.stk_push(
            phone_number=phone_number,
            amount=amount,
            account_reference=f"WALLET-{wallet.id}",
            transaction_desc=f"Deposit to PalsPay"
        )
        
        if response.get('ResponseCode') == '0':
            # STK Push initiated successfully
            transaction.metadata = {
                'checkout_request_id': response.get('CheckoutRequestID'),
                'merchant_request_id': response.get('MerchantRequestID')
            }
            db.session.commit()
            
            return jsonify({
                'message': 'STK Push sent. Please enter your M-Pesa PIN',
                'transaction_id': transaction.id,
                'checkout_request_id': response.get('CheckoutRequestID')
            }), 200
        else:
            # STK Push failed
            transaction.status = TransactionStatus.failed
            transaction.metadata = {'error': response}
            db.session.commit()
            
            return jsonify({
                'message': response.get('errorMessage', 'Failed to initiate payment'),
                'error': response
            }), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error: {str(e)}'}), 500


@deposit_bp.route('/mpesa/status/<int:transaction_id>', methods=['GET'])
@token_required
def check_deposit_status(current_user, transaction_id):
    """Check M-Pesa deposit transaction status"""
    transaction = Transaction.query.filter_by(
        id=transaction_id,
        receiver_wallet_id=current_user.wallet.id
    ).first_or_404()
    
    if transaction.status == TransactionStatus.pending:
        # Query M-Pesa for status
        checkout_request_id = transaction.metadata.get('checkout_request_id')
        if checkout_request_id:
            try:
                response = MpesaService.query_stk_status(checkout_request_id)
                result_code = response.get('ResultCode')
                
                if result_code == '0':
                    transaction.status = TransactionStatus.completed
                    db.session.commit()
                elif result_code == '1032':
                    # User cancelled
                    transaction.status = TransactionStatus.cancelled
                    db.session.commit()
            except Exception as e:
                pass
    
    return jsonify({
        'transaction_id': transaction.id,
        'status': transaction.status.value,
        'amount': str(transaction.amount),
        'created_at': transaction.created_at.isoformat()
    }), 200

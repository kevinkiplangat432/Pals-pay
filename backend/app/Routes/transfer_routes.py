from flask import Blueprint, request, jsonify, current_app
from decimal import Decimal
from datetime import datetime, timezone

from ..extensions import db
from ..models import Transaction, Wallet, Beneficiary, AuditLog, ExchangeRate
from ..models.enums import TransactionStatus, TransactionType, PaymentProvider
from ..auth.decorators import token_required, kyc_required, otp_required
from ..services.transfer_service import TransferService
from ..services.currency_service import CurrencyService
from ..services.compliance_service import ComplianceService
from ..services.otp_services import OTPService
from ..services.notification_service import NotificationService

transfer_bp = Blueprint('transfers', __name__, url_prefix='/api/v1/transfers')

@transfer_bp.route('/local/quote', methods=['POST'])
@token_required
@kyc_required
def get_local_transfer_quote():
    data = request.get_json()
    
    amount = data.get('amount')
    currency = data.get('currency', 'KES')
    receiver_wallet_id = data.get('receiver_wallet_id')
    receiver_phone = data.get('receiver_phone')
    
    if not amount or (not receiver_wallet_id and not receiver_phone):
        return jsonify({'message': 'Amount and receiver required'}), 400
    
    user = request.current_user
    sender_wallet = Wallet.query.filter_by(user_id=user.id).first()
    
    if not sender_wallet:
        return jsonify({'message': 'Sender wallet not found'}), 404
    
    try:
        amount_decimal = Decimal(str(amount))
        if amount_decimal <= 0:
            return jsonify({'message': 'Amount must be positive'}), 400
    except:
        return jsonify({'message': 'Invalid amount'}), 400
    
    quote = TransferService.get_local_transfer_quote(
        sender_wallet_id=sender_wallet.id,
        amount=amount_decimal,
        currency=currency,
        receiver_wallet_id=receiver_wallet_id,
        receiver_phone=receiver_phone
    )
    
    if not quote['success']:
        return jsonify({'message': quote['message']}), 400
    
    return jsonify(quote), 200

@transfer_bp.route('/local/initiate', methods=['POST'])
@token_required
@kyc_required
@otp_required('local_transfer', 'amount')
def initiate_local_transfer():
    data = request.get_json()
    
    amount = data.get('amount')
    currency = data.get('currency', 'KES')
    receiver_wallet_id = data.get('receiver_wallet_id')
    receiver_phone = data.get('receiver_phone')
    description = data.get('description')
    beneficiary_id = data.get('beneficiary_id')
    
    if not amount or (not receiver_wallet_id and not receiver_phone and not beneficiary_id):
        return jsonify({'message': 'Amount and receiver required'}), 400
    
    user = request.current_user
    
    if beneficiary_id:
        beneficiary = Beneficiary.query.filter_by(
            id=beneficiary_id,
            user_id=user.id
        ).first()
        
        if not beneficiary:
            return jsonify({'message': 'Beneficiary not found'}), 404
        
        receiver_wallet_id = beneficiary.beneficiary_wallet_id
        
        can_send = beneficiary.can_send(amount)
        if not can_send['allowed']: #
            return jsonify({'message': can_send['reason']}), 400
    
    result = TransferService.initiate_local_transfer(
        sender_user_id=user.id,
        amount=amount,
        currency=currency,
        receiver_wallet_id=receiver_wallet_id,
        receiver_phone=receiver_phone,
        description=description
    )
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400  

@transfer_bp.route('/international/quote', methods=['POST'])
@token_required
@kyc_required
def get_international_transfer_quote():
    data = request.get_json()
    
    amount = data.get('amount')
    source_currency = data.get('source_currency')
    target_currency = data.get('target_currency')
    destination_country = data.get('destination_country')
    receiver_details = data.get('receiver_details')
    
    if not amount or not source_currency or not target_currency or not destination_country or not receiver_details:
        return jsonify({'message': 'Missing required fields'}), 400
    
    user = request.current_user
    
    try:
        amount_decimal = Decimal(str(amount))
        if amount_decimal <= 0:
            return jsonify({'message': 'Amount must be positive'}), 400
    except:
        return jsonify({'message': 'Invalid amount'}), 400
    
    quote = TransferService.get_international_transfer_quote(  #t
        sender_user_id=user.id,
        amount=amount_decimal,
        source_currency=source_currency,
        target_currency=target_currency,
        destination_country=destination_country,
        receiver_details=receiver_details
    )
    
    if not quote['success']:  # If the quote retrieval was not successful, we return a 400 Bad Request with the message from the quote. This allows the frontend to display the specific reason why the quote could not be generated (e.g., unsupported currency pair, compliance issues, etc.) and take appropriate actions (e.g., ask the user to change the amount or currency).
        return jsonify({'message': quote['message']}), 400
    
    return jsonify(quote), 200

@transfer_bp.route('/international/initiate', methods=['POST'])
@token_required
@kyc_required
@otp_required('international_transfer', 'amount')
def initiate_international_transfer():
    data = request.get_json()
    
    quote_id = data.get('quote_id')
    receiver_details = data.get('receiver_details')
    funding_source_id = data.get('funding_source_id')  #
    
    if not quote_id or not receiver_details:
        return jsonify({'message': 'Quote ID and receiver details required'}), 400
    
    user = request.current_user
    
    result = TransferService.initiate_international_transfer(
        sender_user_id=user.id,
        quote_id=quote_id,
        receiver_details=receiver_details,
        funding_source_id=funding_source_id,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@transfer_bp.route('/international/compliance', methods=['POST'])
@token_required
@kyc_required
def check_international_compliance():
    data = request.get_json()
    
    source_country = data.get('source_country')
    destination_country = data.get('destination_country')
    amount = data.get('amount')
    currency = data.get('currency', 'USD')
    
    if not source_country or not destination_country or not amount:
        return jsonify({'message': 'Missing required fields'}), 400
    
    try:
        amount_decimal = Decimal(str(amount))
    except:
        return jsonify({'message': 'Invalid amount'}), 400
    
    compliance_check = ComplianceService.check_international_transfer( # This endpoint allows the frontend to check if an international transfer is compliant with regulations before the user goes through the process of initiating the transfer. The frontend can use this information to inform the user about any potential issues (e.g., if the transfer exceeds limits, if the destination country has restrictions, etc.) and prevent them from going through a process that would ultimately fail due to compliance issues.
        source_country=source_country,
        destination_country=destination_country,
        amount=amount_decimal,
        currency=currency
    )
    
    return jsonify(compliance_check), 200

@transfer_bp.route('/<int:transaction_id>', methods=['GET'])
@token_required
def get_transfer_status(transaction_id):
    user = request.current_user
    
    transaction = Transaction.query.get(transaction_id)
    if not transaction:
        return jsonify({'message': 'Transaction not found'}), 404
    
    sender_wallet = transaction.sender_wallet
    if sender_wallet and sender_wallet.user_id != user.id:
        if transaction.receiver_wallet and transaction.receiver_wallet.user_id != user.id:
            return jsonify({'message': 'Unauthorized access'}), 403
    
    transfer_status = TransferService.get_transfer_status(transaction_id)
    
    return jsonify(transfer_status), 200

@transfer_bp.route('/<int:transaction_id>/cancel', methods=['POST'])
@token_required
def cancel_transfer(transaction_id):
    user = request.current_user
    
    transaction = Transaction.query.get(transaction_id)
    if not transaction:
        return jsonify({'message': 'Transaction not found'}), 404
    
    if transaction.sender_wallet.user_id != user.id:
        return jsonify({'message': 'Unauthorized access'}), 403
    
    if transaction.status != TransactionStatus.pending:
        return jsonify({'message': 'Only pending transactions can be cancelled'}), 400
    
    result = TransferService.cancel_transfer(
        transaction_id=transaction_id,
        cancelled_by=user.id
    )
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@transfer_bp.route('/history', methods=['GET'])
@token_required
def get_transfer_history():
    user = request.current_user
    wallet = Wallet.query.filter_by(user_id=user.id).first()
    
    if not wallet:
        return jsonify({'transactions': [], 'total': 0}), 200
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    transaction_type = request.args.get('type')
    status = request.args.get('status')
    
    query = Transaction.query.filter(
        (Transaction.sender_wallet_id == wallet.id) |
        (Transaction.receiver_wallet_id == wallet.id)
    )
    
    if transaction_type:
        from ..models.enums import TransactionType
        try:
            query = query.filter_by(transaction_type=TransactionType(transaction_type))
        except ValueError:
            pass
    
    if status:
        from ..models.enums import TransactionStatus
        try:
            query = query.filter_by(status=TransactionStatus(status))
        except ValueError:
            pass
    
    query = query.order_by(Transaction.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'transactions': [tx.to_dict(include_wallets=True) for tx in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

@transfer_bp.route('/summary', methods=['GET'])
@token_required
def get_transfer_summary():
    user = request.current_user
    
    days = request.args.get('days', 30, type=int) # This endpoint provides a summary of the user's transfer activity over a specified number of days (defaulting to 30). The frontend can use this information to display insights to the user about their transfer habits, such as total amount sent/received, number of transfers, average transfer amount, etc. This can help users understand their financial behavior and make informed decisions about their transfers.
    
    summary = TransferService.get_user_transfer_summary(
        user_id=user.id,
        days=days
    )
    
    return jsonify(summary), 200

@transfer_bp.route('/currencies/convert', methods=['POST'])
@token_required
def convert_currency():
    data = request.get_json()
    
    amount = data.get('amount')
    from_currency = data.get('from_currency')
    to_currency = data.get('to_currency')
    
    if not amount or not from_currency or not to_currency:
        return jsonify({'message': 'Amount, from_currency and to_currency required'}), 400
    
    try:
        amount_decimal = Decimal(str(amount))
        if amount_decimal <= 0:
            return jsonify({'message': 'Amount must be positive'}), 400
    except:
        return jsonify({'message': 'Invalid amount'}), 400
    
    exchange_rate = CurrencyService.get_exchange_rate(from_currency, to_currency)
    converted_amount = amount_decimal * exchange_rate
    
    return jsonify({
        'from_amount': float(amount_decimal),
        'from_currency': from_currency,
        'to_amount': float(converted_amount),
        'to_currency': to_currency,
        'exchange_rate': float(exchange_rate),
        'timestamp': datetime.now(timezone.utc).isoformat()
    }), 200
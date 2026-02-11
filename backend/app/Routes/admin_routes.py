from flask import Blueprint, request, jsonify
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from decimal import Decimal

from app.models import User, Wallet, Transaction, KYCVerification, AuditLog
from app.models.enums import TransactionStatus, KYCStatus
from ..extensions import db
from app.auth.decorators import token_required, role_required, kyc_required, otp_required
from app.services.analytics_service import AnalyticsService
from app.services.kyc_service import KYCService

admin_bp = Blueprint('admin', __name__, url_prefix='/api/v1/admin')

# Get all users with pagination
@admin_bp.route('/users', methods=['GET'])
@token_required
@role_required('admin')
def get_all_users(current_user):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = User.query
    
    # Filter by status if provided
    status = request.args.get('status')
    if status == 'active':
        query = query.filter_by(is_active=True)
    elif status == 'inactive':
        query = query.filter_by(is_active=False)
    
    # Filter by KYC status
    kyc_status = request.args.get('kyc_status')
    if kyc_status:
        query = query.filter_by(kyc_status=KYCStatus(kyc_status))
    
    # Search
    search = request.args.get('search')
    if search:
        query = query.filter(
            (User.email.ilike(f'%{search}%')) |
            (User.username.ilike(f'%{search}%')) |
            (User.phone_number.ilike(f'%{search}%')) |
            (User.first_name.ilike(f'%{search}%')) |
            (User.last_name.ilike(f'%{search}%'))
        )
    
    # Order by
    order_by = request.args.get('order_by', 'created_at')
    order_dir = request.args.get('order_dir', 'desc')
    
    if order_by == 'created_at':
        query = query.order_by(desc(User.created_at) if order_dir == 'desc' else User.created_at)
    elif order_by == 'last_login':
        query = query.order_by(desc(User.last_login_at) if order_dir == 'desc' else User.last_login_at)
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'users': [user.to_dict(include_wallet=True, include_kyc=True) for user in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

# Toggle user status
@admin_bp.route('/users/<int:user_id>/status', methods=['PUT'])
@token_required
@role_required('admin')
def toggle_user_status(current_user, user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if 'is_active' not in data:
        return jsonify({'message': 'Missing is_active field'}), 400
    
    old_status = user.is_active
    user.is_active = data['is_active']
    
    db.session.commit()
    
    # Log the action
    AuditLog.log_admin_action(
        actor_id=request.current_user.id,
        action='user.status.update',
        resource_type='user',
        resource_id=user.id,
        old_values={'is_active': old_status},
        new_values={'is_active': user.is_active},
        status='success'
    )
    
    return jsonify({
        'message': f'User {user.username} {"activated" if user.is_active else "deactivated"} successfully',
        'user': user.to_dict()
    }), 200

# Get all wallets
@admin_bp.route('/wallets', methods=['GET'])
@token_required
@role_required('admin')
def get_all_wallets(current_user):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Wallet.query.join(User)
    
    # Filter by status
    status = request.args.get('status')
    if status:
        from app.models.enums import WalletStatus
        query = query.filter_by(status=WalletStatus(status))
    
    # Filter by minimum balance
    min_balance = request.args.get('min_balance', type=float)
    if min_balance:
        query = query.filter(Wallet.balance >= Decimal(str(min_balance)))
    
    # Search by user
    search = request.args.get('search')
    if search:
        query = query.filter(
            (User.email.ilike(f'%{search}%')) |
            (User.username.ilike(f'%{search}%')) |
            (User.phone_number.ilike(f'%{search}%'))
        )
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    wallets_data = []
    for wallet in pagination.items:
        wallet_dict = wallet.to_dict()
        wallet_dict['user'] = wallet.user.to_dict()
        wallets_data.append(wallet_dict)
    
    return jsonify({
        'wallets': wallets_data,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

# Get all transactions
@admin_bp.route('/transactions', methods=['GET'])
@token_required
@role_required('admin')
def get_all_transactions(current_user):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    query = Transaction.query
    
    # Filter by status
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=TransactionStatus(status))
    
    # Filter by type
    transaction_type = request.args.get('type')
    if transaction_type:
        from app.models.enums import TransactionType
        query = query.filter_by(transaction_type=TransactionType(transaction_type))
    
    # Filter by date range
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if start_date:
        query = query.filter(Transaction.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(Transaction.created_at <= datetime.fromisoformat(end_date))
    
    # Filter by amount range
    min_amount = request.args.get('min_amount', type=float)
    max_amount = request.args.get('max_amount', type=float)
    if min_amount:
        query = query.filter(Transaction.amount >= Decimal(str(min_amount)))
    if max_amount:
        query = query.filter(Transaction.amount <= Decimal(str(max_amount)))
    
    # Order by
    query = query.order_by(desc(Transaction.created_at))
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'transactions': [tx.to_dict(include_wallets=True) for tx in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

# Get system statistics
@admin_bp.route('/stats', methods=['GET'])
@token_required
@role_required('admin')
def get_system_stats(current_user):
    stats = AnalyticsService.get_system_analytics()
    return jsonify(stats), 200

# Reverse transaction
@admin_bp.route('/transactions/<int:tx_id>/reverse', methods=['POST'])
@token_required
@role_required('admin')
@otp_required('admin_reverse')
def reverse_transaction(tx_id, current_user):
    transaction = Transaction.query.get_or_404(tx_id)
    
    if transaction.status != TransactionStatus.completed:
        return jsonify({'message': 'Only completed transactions can be reversed'}), 400
    
    # Check if already reversed
    if transaction.status == TransactionStatus.reversed:
        return jsonify({'message': 'Transaction already reversed'}), 400
    
    try:
        with db.session.begin_nested():
            # Create reversal transaction
            reversal = Transaction(
                sender_wallet_id=transaction.receiver_wallet_id,
                receiver_wallet_id=transaction.sender_wallet_id,
                amount=transaction.net_amount,
                fee=Decimal('0.00'),
                net_amount=transaction.net_amount,
                transaction_type=transaction.transaction_type,
                status=TransactionStatus.completed,
                provider=transaction.provider,
                description=f"Reversal of transaction {transaction.reference}",
                metadata={'reversal_for': transaction.id}
            )
            
            db.session.add(reversal)
            db.session.flush()
            
            # Create ledger entries for reversal
            from app.models import LedgerEntry
            entries = LedgerEntry.create_entries(reversal)
            for entry in entries:
                db.session.add(entry)
            
            # Update original transaction status
            transaction.update_status(TransactionStatus.reversed)
            
            # Log the action
            AuditLog.log_admin_action(
                actor_id=request.current_user.id,
                action='transaction.reverse',
                resource_type='transaction',
                resource_id=transaction.id,
                new_values={'reversal_id': reversal.id},
                status='success'
            )
        
        db.session.commit()
        
        return jsonify({
            'message': 'Transaction reversed successfully',
            'original_transaction': transaction.to_dict(),
            'reversal_transaction': reversal.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Failed to reverse transaction: {str(e)}'}), 500

# Get suspicious activities
@admin_bp.route('/suspicious-activities', methods=['GET'])
@token_required
@role_required('admin')
def get_suspicious_activities(current_user):
    suspicious = AnalyticsService.get_suspicious_activities()
    return jsonify(suspicious), 200

# Get KYC pending verification
@admin_bp.route('/kyc/pending', methods=['GET'])
@token_required
@role_required('admin')
def get_pending_kyc(current_user):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = KYCVerification.query.filter_by(status=KYCStatus.pending).join(User, KYCVerification.user_id == User.id)
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    kyc_list = []
    for kyc in pagination.items:
        kyc_dict = kyc.to_dict()
        kyc_dict['user'] = kyc.user.to_dict()
        kyc_list.append(kyc_dict)
    
    return jsonify({
        'kyc_verifications': kyc_list,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

# Verify KYC
@admin_bp.route('/kyc/<int:kyc_id>/verify', methods=['POST'])
@token_required
@role_required('admin')
def verify_kyc(current_user, kyc_id):
    data = request.get_json()
    approved = data.get('approved', True)
    rejection_reason = data.get('rejection_reason')
    
    if not approved and not rejection_reason:
        return jsonify({'message': 'Rejection reason required when rejecting KYC'}), 400
    
    result = KYCService.verify_kyc(kyc_id, request.current_user.id, approved, rejection_reason)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400

# Get profit trends
@admin_bp.route('/analytics/profit-trends', methods=['GET'])
@token_required
@role_required('admin')
def get_profit_trends(current_user):
    days = request.args.get('days', 30, type=int)
    trends = AnalyticsService.get_profit_trends(days)
    return jsonify(trends), 200

# Get audit logs
@admin_bp.route('/audit-logs', methods=['GET'])
@token_required
@role_required('admin')
def get_audit_logs(current_user):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    query = AuditLog.query
    
    # Filter by action
    action = request.args.get('action')
    if action:
        query = query.filter_by(action=action)
    
    # Filter by actor
    actor_id = request.args.get('actor_id', type=int)
    if actor_id:
        query = query.filter_by(actor_id=actor_id)
    
    # Filter by resource
    resource_type = request.args.get('resource_type')
    if resource_type:
        query = query.filter_by(resource_type=resource_type)
    
    resource_id = request.args.get('resource_id', type=int)
    if resource_id:
        query = query.filter_by(resource_id=resource_id)
    
    # Filter by date range
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if start_date:
        query = query.filter(AuditLog.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(AuditLog.created_at <= datetime.fromisoformat(end_date))
    
    # Order by
    query = query.order_by(desc(AuditLog.created_at))
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'audit_logs': [log.to_dict() for log in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import func
from ..extensions import db
from app.models import Wallet, Transaction, LedgerEntry, AuditLog
from app.models.enums import TransactionStatus, TransactionType, PaymentProvider

class WalletService:
    
    @staticmethod
    def get_wallet_balance(user_id):
        """
        Get wallet balance for a user
        """
        wallet = Wallet.query.filter_by(user_id=user_id).first()
        if not wallet:
            return None
        
        return {
            'balance': float(wallet.balance),
            'available_balance': float(wallet.available_balance),
            'locked_balance': float(wallet.locked_balance),
            'currency': wallet.primary_currency,
            'daily_limit': float(wallet.daily_limit),
            'monthly_limit': float(wallet.monthly_limit),
            'last_transaction_at': wallet.last_transaction_at
        }
    
    @staticmethod
    def get_wallet_analytics(user_id):
        """
        Get wallet analytics including transaction trends
        """
        wallet = Wallet.query.filter_by(user_id=user_id).first()
        if not wallet:
            return {}
        
        # Last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Get deposits
        deposits = Transaction.query.filter(
            Transaction.receiver_wallet_id == wallet.id,
            Transaction.transaction_type == TransactionType.deposit,
            Transaction.status == TransactionStatus.completed,
            Transaction.created_at >= thirty_days_ago
        ).all()
        total_deposits = sum([tx.amount for tx in deposits], Decimal('0.00'))
        
        # Get withdrawals
        withdrawals = Transaction.query.filter(
            Transaction.sender_wallet_id == wallet.id,
            Transaction.transaction_type == TransactionType.withdrawal,
            Transaction.status == TransactionStatus.completed,
            Transaction.created_at >= thirty_days_ago
        ).all()
        total_withdrawals = sum([tx.amount for tx in withdrawals], Decimal('0.00'))
        
        # Get transfers (sent)
        transfers = Transaction.query.filter(
            Transaction.sender_wallet_id == wallet.id,
            Transaction.transaction_type == TransactionType.transfer,
            Transaction.status == TransactionStatus.completed,
            Transaction.created_at >= thirty_days_ago
        ).all()
        total_transfers = sum([tx.amount for tx in transfers], Decimal('0.00'))
        
        # Total transaction count
        transaction_count = Transaction.query.filter(
            (Transaction.sender_wallet_id == wallet.id) |
            (Transaction.receiver_wallet_id == wallet.id),
            Transaction.status == TransactionStatus.completed,
            Transaction.created_at >= thirty_days_ago
        ).count()
        
        return {
            'total_deposits': float(total_deposits),
            'total_withdrawals': float(total_withdrawals),
            'total_transfers': float(total_transfers),
            'transaction_count': transaction_count
        }
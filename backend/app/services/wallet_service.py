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
        
        # Today's date
        today = datetime.utcnow().date()
        
        # Today's transactions
        today_start = datetime.combine(today, datetime.min.time())
        today_transactions = Transaction.query.filter(
            (Transaction.sender_wallet_id == wallet.id) |
            (Transaction.receiver_wallet_id == wallet.id),
            Transaction.status == TransactionStatus.completed,
            Transaction.created_at >= today_start
        ).all()
        
        today_sent = sum([tx.amount for tx in today_transactions if tx.sender_wallet_id == wallet.id], Decimal('0.00'))
        today_received = sum([tx.amount for tx in today_transactions if tx.receiver_wallet_id == wallet.id], Decimal('0.00'))
        
        # Monthly transactions
        month_start = datetime(today.year, today.month, 1)
        monthly_transactions = Transaction.query.filter(
            (Transaction.sender_wallet_id == wallet.id) |
            (Transaction.receiver_wallet_id == wallet.id),
            Transaction.status == TransactionStatus.completed,
            Transaction.created_at >= month_start
        ).all()
        
        monthly_sent = sum([tx.amount for tx in monthly_transactions if tx.sender_wallet_id == wallet.id], Decimal('0.00'))
        monthly_received = sum([tx.amount for tx in monthly_transactions if tx.receiver_wallet_id == wallet.id], Decimal('0.00'))
        
        # Transaction count by type
        sent_count = Transaction.query.filter(
            Transaction.sender_wallet_id == wallet.id,
            Transaction.status == TransactionStatus.completed
        ).count()
        
        received_count = Transaction.query.filter(
            Transaction.receiver_wallet_id == wallet.id,
            Transaction.status == TransactionStatus.completed
        ).count()
        
        # Top beneficiaries (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        from app.models import Beneficiary
        top_beneficiaries = db.session.query(
            Beneficiary,
            func.count(Transaction.id).label('count'),
            func.sum(Transaction.amount).label('total')
        ).join(
            Transaction,
            (Transaction.receiver_wallet_id == Beneficiary.beneficiary_wallet_id) &
            (Transaction.sender_wallet_id == wallet.id)
        ).filter(
            Transaction.status == TransactionStatus.completed,
            Transaction.created_at >= thirty_days_ago,
            Beneficiary.user_id == user_id
        ).group_by(Beneficiary.id).order_by(func.sum(Transaction.amount).desc()).limit(5).all()
        
        analytics = {
            'wallet_summary': wallet.to_dict(),
            'today': {
                'sent': float(today_sent),
                'received': float(today_received),
                'count': len(today_transactions)
            },
            'this_month': {
                'sent': float(monthly_sent),
                'received': float(monthly_received),
                'count': len(monthly_transactions)
            },
            'overall': {
                'sent_count': sent_count,
                'received_count': received_count,
                'total_transactions': sent_count + received_count
            },
            'top_beneficiaries': [
                {
                    'beneficiary': beneficiary.to_dict(include_user=True),
                    'transaction_count': count,
                    'total_amount': float(total)
                }
                for beneficiary, count, total in top_beneficiaries
            ] if top_beneficiaries else []
        }
        
        return analytics
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import func, extract, and_
from backend.app.extensions import db
from app.models import User, Wallet, Transaction, AuditLog
from app.models.enums import TransactionStatus, KYCStatus

class AnalyticsService:
    
    @staticmethod
    def get_system_analytics():
        """
        Get overall system analytics for admin dashboard
        """
        # User statistics
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        new_users_today = User.query.filter(
            User.created_at >= datetime.utcnow().date()
        ).count()
        
        # KYC statistics
        kyc_verified = User.query.filter_by(kyc_status=KYCStatus.verified).count()
        kyc_pending = User.query.filter_by(kyc_status=KYCStatus.pending).count()
        kyc_rejected = User.query.filter_by(kyc_status=KYCStatus.rejected).count()
        
        # Wallet statistics
        total_wallets = Wallet.query.count()
        total_balance = db.session.query(func.sum(Wallet.balance)).scalar() or Decimal('0.00')
        avg_balance = db.session.query(func.avg(Wallet.balance)).scalar() or Decimal('0.00')
        
        # Transaction statistics (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        total_transactions = Transaction.query.filter(
            Transaction.created_at >= thirty_days_ago
        ).count()
        
        completed_transactions = Transaction.query.filter(
            Transaction.status == TransactionStatus.completed,
            Transaction.created_at >= thirty_days_ago
        ).count()
        
        total_volume = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.status == TransactionStatus.completed,
            Transaction.created_at >= thirty_days_ago
        ).scalar() or Decimal('0.00')
        
        total_fees = db.session.query(func.sum(Transaction.fee)).filter(
            Transaction.status == TransactionStatus.completed,
            Transaction.created_at >= thirty_days_ago
        ).scalar() or Decimal('0.00')
        
        # Today's statistics
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        today_transactions = Transaction.query.filter(
            Transaction.created_at >= today_start
        ).count()
        
        today_volume = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.status == TransactionStatus.completed,
            Transaction.created_at >= today_start
        ).scalar() or Decimal('0.00')
        
        today_fees = db.session.query(func.sum(Transaction.fee)).filter(
            Transaction.status == TransactionStatus.completed,
            Transaction.created_at >= today_start
        ).scalar() or Decimal('0.00')
        
        return {
            'users': {
                'total': total_users,
                'active': active_users,
                'new_today': new_users_today,
                'kyc_verified': kyc_verified,
                'kyc_pending': kyc_pending,
                'kyc_rejected': kyc_rejected
            },
            'wallets': {
                'total': total_wallets,
                'total_balance': float(total_balance),
                'average_balance': float(avg_balance)
            },
            'transactions': {
                'total_last_30_days': total_transactions,
                'completed_last_30_days': completed_transactions,
                'volume_last_30_days': float(total_volume),
                'fees_last_30_days': float(total_fees),
                'today_count': today_transactions,
                'today_volume': float(today_volume),
                'today_fees': float(today_fees)
            }
        }
    
    @staticmethod
    def get_profit_trends(days=30):
        """
        Get profit trends over time
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Group by day
        daily_profits = db.session.query(
            func.date(Transaction.created_at).label('date'),
            func.sum(Transaction.fee).label('total_fees'),
            func.count(Transaction.id).label('transaction_count'),
            func.sum(Transaction.amount).label('total_volume')
        ).filter(
            Transaction.status == TransactionStatus.completed,
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date
        ).group_by(
            func.date(Transaction.created_at)
        ).order_by(
            func.date(Transaction.created_at)
        ).all()
        
        # Group by transaction type
        profit_by_type = db.session.query(
            Transaction.transaction_type,
            func.sum(Transaction.fee).label('total_fees'),
            func.count(Transaction.id).label('transaction_count')
        ).filter(
            Transaction.status == TransactionStatus.completed,
            Transaction.created_at >= start_date
        ).group_by(
            Transaction.transaction_type
        ).all()
        
        # Top performing users (by fees generated)
        top_users = db.session.query(
            User.id,
            User.username,
            User.email,
            func.sum(Transaction.fee).label('total_fees'),
            func.count(Transaction.id).label('transaction_count')
        ).join(
            Wallet, Wallet.user_id == User.id
        ).join(
            Transaction, Transaction.sender_wallet_id == Wallet.id
        ).filter(
            Transaction.status == TransactionStatus.completed,
            Transaction.created_at >= start_date
        ).group_by(
            User.id, User.username, User.email
        ).order_by(
            func.sum(Transaction.fee).desc()
        ).limit(10).all()
        
        return {
            'daily_trends': [
                {
                    'date': row.date.isoformat() if row.date else None,
                    'total_fees': float(row.total_fees or 0),
                    'transaction_count': row.transaction_count or 0,
                    'total_volume': float(row.total_volume or 0)
                }
                for row in daily_profits
            ],
            'by_transaction_type': [
                {
                    'type': row.transaction_type.value,
                    'total_fees': float(row.total_fees or 0),
                    'transaction_count': row.transaction_count or 0
                }
                for row in profit_by_type
            ],
            'top_users': [
                {
                    'user_id': row.id,
                    'username': row.username,
                    'email': row.email,
                    'total_fees': float(row.total_fees or 0),
                    'transaction_count': row.transaction_count or 0
                }
                for row in top_users
            ],
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            }
        }
    
    @staticmethod
    def get_suspicious_activities():
        """
        Detect and return suspicious activities
        """
        # Large transactions (above 100,000)
        threshold_amount = 100000
        last_24_hours = datetime.utcnow() - timedelta(hours=24)
        
        large_transactions = Transaction.query.filter(
            Transaction.amount >= threshold_amount,
            Transaction.created_at >= last_24_hours
        ).order_by(
            Transaction.amount.desc()
        ).limit(50).all()
        
        # Multiple transactions from same user in short time
        suspicious_users = db.session.query(
            Transaction.sender_wallet_id,
            func.count(Transaction.id).label('tx_count'),
            func.sum(Transaction.amount).label('total_amount')
        ).filter(
            Transaction.created_at >= last_24_hours
        ).group_by(
            Transaction.sender_wallet_id
        ).having(
            func.count(Transaction.id) > 10  # More than 10 transactions in 24 hours
        ).all()
        
        # Failed login attempts
        failed_logins = AuditLog.query.filter(
            AuditLog.action == 'login.failed',
            AuditLog.created_at >= last_24_hours
        ).order_by(
            AuditLog.created_at.desc()
        ).limit(100).all()
        
        return {
            'large_transactions': [
                {
                    'transaction_id': tx.id,
                    'amount': float(tx.amount),
                    'user_id': tx.sender_wallet.user_id if tx.sender_wallet else None,
                    'timestamp': tx.created_at.isoformat() if tx.created_at else None,
                    'status': tx.status.value
                }
                for tx in large_transactions
            ],
            'suspicious_users': [
                {
                    'wallet_id': row.sender_wallet_id,
                    'user_id': Wallet.query.get(row.sender_wallet_id).user_id if row.sender_wallet_id else None,
                    'transaction_count': row.tx_count,
                    'total_amount': float(row.total_amount or 0)
                }
                for row in suspicious_users
            ],
            'failed_logins': [
                {
                    'actor_id': log.actor_id,
                    'actor_ip': log.actor_ip,
                    'timestamp': log.created_at.isoformat() if log.created_at else None,
                    'error_message': log.error_message
                }
                for log in failed_logins
            ]
        }
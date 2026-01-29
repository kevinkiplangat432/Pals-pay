"""
Wallet Model - Manages user balances and funds
"""

from datetime import datetime, timezone
from decimal import Decimal
from extensions import db


class Wallet(db.Model):
    """
    Wallet model for managing user balances and funds
    One-to-one relationship with User
    """
    __tablename__ = 'wallets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    balance = db.Column(db.Numeric(precision=10, scale=2), default=Decimal('0.00'), nullable=False)
    currency = db.Column(db.String(3), default='USD', nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    def to_dict(self):
        """
        Returns wallet data for API responses
        
        Returns:
            dict: Wallet data dictionary
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'balance': float(self.balance),
            'currency': self.currency,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_analytics(self):
        """
        Calculates wallet statistics and analytics
        
        Returns:
            dict: Analytics including totals and counts by transaction type
        """
        from .transaction import Transaction
        
        # Get all completed transactions
        sent_transactions = Transaction.query.filter_by(
            sender_id=self.user_id,
            status='completed'
        ).all()
        
        received_transactions = Transaction.query.filter_by(
            receiver_id=self.user_id,
            status='completed'
        ).all()
        
        # Calculate totals
        total_sent = sum(Decimal(str(t.amount)) for t in sent_transactions if t.transaction_type == 'transfer')
        total_received = sum(Decimal(str(t.amount)) for t in received_transactions if t.transaction_type == 'transfer')
        total_deposited = sum(Decimal(str(t.amount)) for t in received_transactions if t.transaction_type == 'deposit')
        total_withdrawn = sum(Decimal(str(t.amount)) for t in sent_transactions if t.transaction_type == 'withdrawal')
        
        # Count transactions by type
        transfers_sent = sum(1 for t in sent_transactions if t.transaction_type == 'transfer')
        transfers_received = sum(1 for t in received_transactions if t.transaction_type == 'transfer')
        deposits = sum(1 for t in received_transactions if t.transaction_type == 'deposit')
        withdrawals = sum(1 for t in sent_transactions if t.transaction_type == 'withdrawal')
        
        return {
            'current_balance': float(self.balance),
            'currency': self.currency,
            'totals': {
                'sent': float(total_sent),
                'received': float(total_received),
                'deposited': float(total_deposited),
                'withdrawn': float(total_withdrawn)
            },
            'transaction_counts': {
                'transfers_sent': transfers_sent,
                'transfers_received': transfers_received,
                'deposits': deposits,
                'withdrawals': withdrawals,
                'total': transfers_sent + transfers_received + deposits + withdrawals
            }
        }
    
    def __repr__(self):
        return f'<Wallet user_id={self.user_id} balance={self.balance} {self.currency}>'

"""
Transaction Model - Records all money movements
"""

from datetime import datetime
from decimal import Decimal
import uuid
from extensions import db


class Transaction(db.Model):
    """
    Transaction model for recording all money movements
    Supports transfers, deposits, and withdrawals
    """
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Participants
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    
    # Transaction details
    amount = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    transaction_type = db.Column(
        db.String(20), 
        nullable=False,
        default='transfer'
    )  # 'transfer', 'deposit', 'withdrawal'
    
    status = db.Column(
        db.String(20),
        nullable=False,
        default='pending'
    )  # 'pending', 'completed', 'failed'
    
    transaction_fee = db.Column(db.Numeric(precision=10, scale=2), default=Decimal('0.00'), nullable=False)
    reference = db.Column(db.String(100), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    description = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint('amount > 0', name='check_positive_amount'),
        db.CheckConstraint(
            "transaction_type IN ('transfer', 'deposit', 'withdrawal')",
            name='check_transaction_type'
        ),
        db.CheckConstraint(
            "status IN ('pending', 'completed', 'failed')",
            name='check_status'
        ),
    )
    
    @staticmethod
    def calculate_fee(amount):
        """
        Calculate transaction fee: 1% of amount, minimum $0.50
        
        Args:
            amount (Decimal or float): Transaction amount
            
        Returns:
            Decimal: Calculated fee
        """
        amount = Decimal(str(amount))
        fee = amount * Decimal('0.01')  # 1% fee
        min_fee = Decimal('0.50')
        return max(fee, min_fee)
    
    def to_dict(self, include_users=True):
        """
        Serializes transaction data for API responses
        Includes sender/receiver usernames if available
        
        Args:
            include_users (bool): Whether to include user details
            
        Returns:
            dict: Transaction data dictionary
        """
        data = {
            'id': self.id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'amount': float(self.amount),
            'transaction_type': self.transaction_type,
            'status': self.status,
            'transaction_fee': float(self.transaction_fee),
            'reference': self.reference,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
        
        if include_users:
            if self.sender:
                data['sender_username'] = self.sender.username
                data['sender_phone'] = self.sender.phone_number
                data['sender_name'] = f"{self.sender.first_name} {self.sender.last_name}"
            
            if self.receiver:
                data['receiver_username'] = self.receiver.username
                data['receiver_phone'] = self.receiver.phone_number
                data['receiver_name'] = f"{self.receiver.first_name} {self.receiver.last_name}"
        
        return data
    
    def __repr__(self):
        return f'<Transaction {self.reference} {self.transaction_type} {self.amount} {self.status}>'

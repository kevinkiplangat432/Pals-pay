"""
Wallet Model - Manages user balances and funds with ledger-based accounting
"""
from datetime import datetime, timezone
from decimal import Decimal
from extensions import db
from .enums import WalletStatus


class Wallet(db.Model):
    """
    Wallet model with explicit ledger-based accounting
    Balance should be derived from ledger entries, not manipulated directly
    """
    __tablename__ = 'wallets'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id', ondelete='CASCADE'), 
        unique=True, 
        nullable=False,
        index=True
    )
    
    # Balance fields (denormalized for performance)
    balance = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    available_balance = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    locked_balance = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    
    # Configuration
    currency = db.Column(db.String(3), default='KES', nullable=False)
    status = db.Column(
        db.Enum(WalletStatus, name="wallet_status_enum"),
        default=WalletStatus.active,
        nullable=False
    )
    
    # Security
    daily_limit = db.Column(db.Numeric(12, 2), default=Decimal('100000.00'), nullable=False)
    monthly_limit = db.Column(db.Numeric(12, 2), default=Decimal('1000000.00'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=db.func.now(), nullable=True)
    last_transaction_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Relationships
    ledger_entries = db.relationship(
        'LedgerEntry', 
        backref='wallet', 
        lazy='dynamic',
        order_by='desc(LedgerEntry.created_at)',
        cascade='all, delete-orphan'
    )
    
    # Indexes
    __table_args__ = (
        db.Index('idx_wallets_user_status', 'user_id', 'status'),
        db.Index('idx_wallets_balance', 'balance'),
        db.Index('idx_wallets_created_at', 'created_at'),
        db.CheckConstraint('balance >= 0', name='check_non_negative_balance'),
        db.CheckConstraint('available_balance >= 0', name='check_non_negative_available'),
        db.CheckConstraint('locked_balance >= 0', name='check_non_negative_locked'),
        db.CheckConstraint('balance = available_balance + locked_balance', name='check_balance_consistency'),
    )
    
    def update_balance_from_ledger(self):
        """
        Recalculates balance from ledger entries
        Should be called after ledger changes
        """
        from .ledger_entry import LedgerEntry
        
        # Get the latest ledger entry
        last_entry = self.ledger_entries.first()
        if last_entry:
            self.balance = last_entry.balance_after
            self.available_balance = last_entry.balance_after - self.locked_balance
        else:
            self.balance = Decimal('0.00')
            self.available_balance = Decimal('0.00')
    
    def can_withdraw(self, amount):
        """
        Checks if withdrawal is allowed
        
        Args:
            amount (Decimal): Amount to withdraw
            
        Returns:
            dict: {'allowed': bool, 'reason': str}
        """
        amount = Decimal(str(amount))
        
        if self.status != WalletStatus.active:
            return {'allowed': False, 'reason': f'Wallet is {self.status.value}'}
        
        if amount <= 0:
            return {'allowed': False, 'reason': 'Amount must be positive'}
        
        if amount > self.available_balance:
            return {'allowed': False, 'reason': 'Insufficient available balance'}
        
        # Check daily limit (simplified - should check actual daily total)
        if amount > self.daily_limit:
            return {'allowed': False, 'reason': 'Exceeds daily limit'}
        
        return {'allowed': True, 'reason': 'OK'}
    
    def lock_funds(self, amount):
        """
        Locks funds for pending transaction
        
        Args:
            amount (Decimal): Amount to lock
            
        Returns:
            bool: Success status
        """
        amount = Decimal(str(amount))
        
        if amount > self.available_balance:
            return False
        
        self.locked_balance += amount
        self.available_balance -= amount
        return True
    
    def unlock_funds(self, amount):
        """
        Unlocks previously locked funds
        
        Args:
            amount (Decimal): Amount to unlock
            
        Returns:
            bool: Success status
        """
        amount = Decimal(str(amount))
        
        if amount > self.locked_balance:
            return False
        
        self.locked_balance -= amount
        self.available_balance += amount
        return True
    
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
            'available_balance': float(self.available_balance),
            'locked_balance': float(self.locked_balance),
            'currency': self.currency,
            'status': self.status.value,
            'daily_limit': float(self.daily_limit),
            'monthly_limit': float(self.monthly_limit),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_transaction_at': self.last_transaction_at.isoformat() if self.last_transaction_at else None
        }
    
    def __repr__(self):
        return f'<Wallet user_id={self.user_id} balance={self.balance} status={self.status.value}>'
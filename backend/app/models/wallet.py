# models/wallet.py - Updated for multi-currency
from datetime import datetime, timezone
from decimal import Decimal
from ..extensions import db
from .enums import WalletStatus

class Wallet(db.Model):
    __tablename__ = 'wallets'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    
    # Primary wallet balance (in user's preferred currency)
    balance = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    available_balance = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    locked_balance = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    
    # Multi-currency balances (stored as JSON)
    currency_balances = db.Column(db.JSON, default={}, nullable=False)  # {'USD': 100.00, 'EUR': 50.00}
    
    # Configuration
    primary_currency = db.Column(db.String(3), default='KES', nullable=False)
    supported_currencies = db.Column(db.JSON, default=['KES'], nullable=False)
    
    # Status
    status = db.Column(db.Enum(WalletStatus, name="wallet_status_enum"), default=WalletStatus.active, nullable=False)
    
    # Security Limits (in primary currency)
    daily_limit = db.Column(db.Numeric(12, 2), default=Decimal('100000.00'), nullable=False)
    monthly_limit = db.Column(db.Numeric(12, 2), default=Decimal('1000000.00'), nullable=False)
    
    # Cross-border limits
    cross_border_daily_limit = db.Column(db.Numeric(12, 2), default=Decimal('50000.00'), nullable=False)
    cross_border_monthly_limit = db.Column(db.Numeric(12, 2), default=Decimal('500000.00'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=db.func.now(), nullable=True)
    last_transaction_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Relationships
    ledger_entries = db.relationship('LedgerEntry', backref='wallet', lazy='dynamic', order_by='desc(LedgerEntry.created_at)', cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_wallets_user_status', 'user_id', 'status'),
        db.Index('idx_wallets_currency_balances', db.func.jsonb_array_elements_text('currency_balances')),
        db.CheckConstraint('balance >= 0', name='check_non_negative_balance'),
    )
    
    def update_balance_from_ledger(self):
        from .ledger_entry import LedgerEntry
        
        last_entry = self.ledger_entries.filter_by(currency=self.primary_currency).first()
        if last_entry:
            self.balance = last_entry.balance_after
            self.available_balance = last_entry.balance_after - self.locked_balance
        else:
            self.balance = Decimal('0.00')
            self.available_balance = Decimal('0.00')
    
    def get_balance_in_currency(self, currency_code):
        """Get balance in specific currency"""
        if currency_code == self.primary_currency:
            return self.balance
        
        if currency_code in self.currency_balances:
            return Decimal(str(self.currency_balances[currency_code]))
        
        # Convert from primary currency
        from app.services.currency_service import CurrencyService
        exchange_rate = CurrencyService.get_exchange_rate(self.primary_currency, currency_code)
        return self.balance * exchange_rate
    
    def can_withdraw(self, amount, currency='KES', target_country=None):
        amount = Decimal(str(amount))
        
        if self.status != WalletStatus.active:
            return {'allowed': False, 'reason': f'Wallet is {self.status.value}'}
        
        if amount <= 0:
            return {'allowed': False, 'reason': 'Amount must be positive'}
        
        # Check available balance in the requested currency
        available_in_currency = self.get_balance_in_currency(currency)
        
        # Convert amount to wallet's primary currency for limit checking
        if currency != self.primary_currency:
            from app.services.currency_service import CurrencyService
            exchange_rate = CurrencyService.get_exchange_rate(currency, self.primary_currency)
            amount_in_primary = amount * exchange_rate
        else:
            amount_in_primary = amount
        
        if amount_in_primary > self.available_balance:
            return {'allowed': False, 'reason': 'Insufficient available balance'}
        
        # Check if cross-border transfer
        if target_country and self.user and target_country != self.user.country_code:
            if amount_in_primary > self.cross_border_daily_limit:
                return {'allowed': False, 'reason': 'Exceeds cross-border daily limit'}
        else:
            # Local transfer limit
            if amount_in_primary > self.daily_limit:
                return {'allowed': False, 'reason': 'Exceeds daily limit'}
        
        return {'allowed': True, 'reason': 'OK'}
    
    def lock_funds(self, amount, currency='KES'):
        amount = Decimal(str(amount))
        
        if currency == self.primary_currency:
            if amount > self.available_balance:
                return False
            self.locked_balance += amount
            self.available_balance -= amount
        else:
            # Lock in currency-specific balance
            if currency not in self.currency_balances:
                self.currency_balances[currency] = 0
            if amount > Decimal(str(self.currency_balances[currency])):
                return False
            self.currency_balances[currency] = float(Decimal(str(self.currency_balances[currency])) - amount)
        
        return True
    
    def to_dict(self, include_user=False):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'balance': float(self.balance),
            'available_balance': float(self.available_balance),
            'locked_balance': float(self.locked_balance),
            'currency_balances': self.currency_balances,
            'primary_currency': self.primary_currency,
            'supported_currencies': self.supported_currencies,
            'status': self.status.value,
            'daily_limit': float(self.daily_limit),
            'monthly_limit': float(self.monthly_limit),
            'cross_border_daily_limit': float(self.cross_border_daily_limit),
            'cross_border_monthly_limit': float(self.cross_border_monthly_limit),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_transaction_at': self.last_transaction_at.isoformat() if self.last_transaction_at else None
        }
        
        if include_user and self.user:
            data['user'] = self.user.to_dict()
        
        return data
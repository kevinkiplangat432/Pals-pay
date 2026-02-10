from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.dialects.postgresql import JSONB
from ..extensions import db
from .enums import WalletStatus


class Wallet(db.Model):
    __tablename__ = 'wallets'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id', ondelete='CASCADE'), nullable=True, index=True)

    
    # Primary wallet balance (in user's preferred currency)
    balance = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    available_balance = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    locked_balance = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    
    # Multi-currency balances (stored as JSONB for querying)
    currency_balances = db.Column(JSONB, default={}, nullable=False)  # {'USD': 100.00, 'EUR': 50.00}
    
    # Configuration
    primary_currency = db.Column(db.String(3), default='KES', nullable=False)
    supported_currencies = db.Column(JSONB, default=['KES'], nullable=False)
    
    # Status
    status = db.Column(db.Enum(WalletStatus, name="wallet_status_enum"), default=WalletStatus.active, nullable=False)
    
    # Security Limits (in primary currency) - Updated per regulatory requirements
    daily_limit = db.Column(db.Numeric(12, 2), default=Decimal('500000.00'), nullable=False)  # Updated to 500,000
    monthly_limit = db.Column(db.Numeric(12, 2), default=Decimal('10000000.00'), nullable=False)  # Updated to 10M
    
    # Cross-border limits
    cross_border_daily_limit = db.Column(db.Numeric(12, 2), default=Decimal('1000000.00'), nullable=False)  # Updated to 1M
    cross_border_monthly_limit = db.Column(db.Numeric(12, 2), default=Decimal('10000000.00'), nullable=False)  # Updated to 10M
    
    # Usage tracking for limit enforcement
    daily_usage = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    monthly_usage = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    cross_border_daily_usage = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    cross_border_monthly_usage = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    
    # Limit reset tracking
    daily_usage_reset_at = db.Column(db.DateTime(timezone=True), nullable=True)
    monthly_usage_reset_at = db.Column(db.DateTime(timezone=True), nullable=True)
    cross_border_daily_reset_at = db.Column(db.DateTime(timezone=True), nullable=True)
    cross_border_monthly_reset_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Risk and compliance
    risk_score = db.Column(db.Integer, default=0, nullable=False)
    flags = db.Column(JSONB, default={}, nullable=True)
    last_screened_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Versioning for consistency
    version = db.Column(db.Integer, default=1, nullable=False)
    ledger_version = db.Column(db.Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=db.func.now(), nullable=True)
    last_transaction_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Relationships
    ledger_entries = db.relationship('LedgerEntry', backref='wallet', lazy='dynamic', 
                                     order_by='desc(LedgerEntry.created_at)', 
                                     cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_wallets_user_status', 'user_id', 'status'),
        db.Index('idx_wallets_currency_balances', 'currency_balances', postgresql_using='gin'),
        db.Index('idx_wallets_daily_reset', 'daily_usage_reset_at'),
        db.Index('idx_wallets_monthly_reset', 'monthly_usage_reset_at'),
        db.CheckConstraint('balance >= 0', name='check_non_negative_balance'),
        db.CheckConstraint('available_balance >= 0', name='check_non_negative_available'),
        db.CheckConstraint('locked_balance >= 0', name='check_non_negative_locked'),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        now = datetime.now(timezone.utc)
        self.daily_usage_reset_at = now
        self.monthly_usage_reset_at = now
        self.cross_border_daily_reset_at = now
        self.cross_border_monthly_reset_at = now
    
    def _reset_usage_if_needed(self):
        """Reset usage counters based on timestamp"""
        now = datetime.now(timezone.utc)
        
        # Reset daily usage if new day
        if self.daily_usage_reset_at.date() != now.date():
            self.daily_usage = Decimal('0.00')
            self.daily_usage_reset_at = now
        
        # Reset monthly usage if new month
        if self.monthly_usage_reset_at.month != now.month:
            self.monthly_usage = Decimal('0.00')
            self.monthly_usage_reset_at = now
        
        # Reset cross-border daily usage if new day
        if self.cross_border_daily_reset_at.date() != now.date():
            self.cross_border_daily_usage = Decimal('0.00')
            self.cross_border_daily_reset_at = now
        
        # Reset cross-border monthly usage if new month
        if self.cross_border_monthly_reset_at.month != now.month:
            self.cross_border_monthly_usage = Decimal('0.00')
            self.cross_border_monthly_reset_at = now
    
    def update_balance_from_ledger(self):
        """Update wallet balance from ledger entries for primary currency"""
        from .ledger_entry import LedgerEntry
        
        # Get the most recent ledger entry for primary currency
        last_entry = self.ledger_entries.filter(
            LedgerEntry.currency == self.primary_currency
        ).order_by(LedgerEntry.created_at.desc()).first()
        
        if last_entry:
            self.balance = last_entry.balance_after
            self.available_balance = last_entry.balance_after - self.locked_balance
            self.ledger_version = last_entry.sequence_number
        else:
            self.balance = Decimal('0.00')
            self.available_balance = Decimal('0.00')
    
    def get_balance_in_currency(self, currency_code):
        """Get balance in specific currency"""
        if currency_code == self.primary_currency:
            return self.balance
        
        if currency_code in self.currency_balances:
            return Decimal(str(self.currency_balances[currency_code]))
        
        # Convert from primary currency using snapshotted rate
        from app.services.currency_service import CurrencyService
        exchange_rate = CurrencyService.get_exchange_rate(self.primary_currency, currency_code)
        return (self.balance * exchange_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def can_withdraw(self, amount, currency='KES', target_country=None, check_usage=True):
        """Enhanced withdrawal check with usage-based limit enforcement"""
        amount = Decimal(str(amount)).quantize(Decimal('0.01'))
        
        # Basic checks
        if self.status != WalletStatus.active:
            return {'allowed': False, 'reason': f'Wallet is {self.status.value}'}
        
        if amount <= 0:
            return {'allowed': False, 'reason': 'Amount must be positive'}
        
        # Check regulatory per-transaction limit (250,000 KES)
        if amount > Decimal('250000.00'):
            return {'allowed': False, 'reason': 'Exceeds per-transaction limit of 250,000 KES'}
        
        # Check available balance in requested currency
        available_in_currency = self.get_balance_in_currency(currency)
        
        # Convert amount to wallet's primary currency for limit checking
        if currency != self.primary_currency:
            from app.services.currency_service import CurrencyService
            exchange_rate = CurrencyService.get_exchange_rate(currency, self.primary_currency)
            amount_in_primary = (amount * exchange_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            amount_in_primary = amount
        
        if amount_in_primary > self.available_balance:
            return {'allowed': False, 'reason': 'Insufficient available balance'}
        
        # Reset usage counters if needed
        self._reset_usage_if_needed()
        
        # Check if cross-border transfer
        is_cross_border = target_country and self.user and target_country != self.user.country_code
        
        if is_cross_border:
            # Check cross-border daily limit
            if check_usage and (self.cross_border_daily_usage + amount_in_primary) > self.cross_border_daily_limit:
                return {'allowed': False, 'reason': f'Exceeds cross-border daily limit. Used: {float(self.cross_border_daily_usage)}, Limit: {float(self.cross_border_daily_limit)}'}
            
            # Check cross-border monthly limit
            if check_usage and (self.cross_border_monthly_usage + amount_in_primary) > self.cross_border_monthly_limit:
                return {'allowed': False, 'reason': f'Exceeds cross-border monthly limit. Used: {float(self.cross_border_monthly_usage)}, Limit: {float(self.cross_border_monthly_limit)}'}
        else:
            # Check local daily limit
            if check_usage and (self.daily_usage + amount_in_primary) > self.daily_limit:
                return {'allowed': False, 'reason': f'Exceeds daily limit. Used: {float(self.daily_usage)}, Limit: {float(self.daily_limit)}'}
            
            # Check local monthly limit
            if check_usage and (self.monthly_usage + amount_in_primary) > self.monthly_limit:
                return {'allowed': False, 'reason': f'Exceeds monthly limit. Used: {float(self.monthly_usage)}, Limit: {float(self.monthly_limit)}'}
        
        return {
            'allowed': True, 
            'reason': 'OK',
            'amount_in_primary': float(amount_in_primary),
            'is_cross_border': is_cross_border
        }
    
    def lock_funds(self, amount, currency='KES'):
        """Lock funds for pending transaction"""
        amount = Decimal(str(amount)).quantize(Decimal('0.01'))
        
        if currency == self.primary_currency:
            if amount > self.available_balance:
                return False
            self.locked_balance += amount
            self.available_balance -= amount
        else:
            # Lock in currency-specific balance
            if currency not in self.currency_balances:
                self.currency_balances[currency] = 0.0
            balance_decimal = Decimal(str(self.currency_balances[currency]))
            if amount > balance_decimal:
                return False
            self.currency_balances[currency] = float(balance_decimal - amount)
        
        self.version += 1
        return True
    
    def unlock_funds(self, amount, currency='KES'):
        """Unlock funds after transaction completion or failure"""
        amount = Decimal(str(amount)).quantize(Decimal('0.01'))
        
        if currency == self.primary_currency:
            if amount > self.locked_balance:
                return False
            self.locked_balance -= amount
            self.available_balance += amount
        else:
            # Unlock in currency-specific balance
            if currency not in self.currency_balances:
                return False
            self.currency_balances[currency] = float(Decimal(str(self.currency_balances[currency])) + amount)
        
        self.version += 1
        return True
    
    def record_usage(self, amount, is_cross_border=False):
        """Record usage for limit tracking"""
        amount = Decimal(str(amount)).quantize(Decimal('0.01'))
        
        if is_cross_border:
            self.cross_border_daily_usage += amount
            self.cross_border_monthly_usage += amount
        else:
            self.daily_usage += amount
            self.monthly_usage += amount
        
        self.last_transaction_at = datetime.now(timezone.utc)
        self.version += 1
    
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
            'daily_usage': float(self.daily_usage),
            'monthly_usage': float(self.monthly_usage),
            'cross_border_daily_usage': float(self.cross_border_daily_usage),
            'cross_border_monthly_usage': float(self.cross_border_monthly_usage),
            'risk_score': self.risk_score,
            'version': self.version,
            'ledger_version': self.ledger_version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_transaction_at': self.last_transaction_at.isoformat() if self.last_transaction_at else None,
            'last_screened_at': self.last_screened_at.isoformat() if self.last_screened_at else None
        }
        
        if include_user and self.user:
            data['user'] = self.user.to_dict()
        
        return data
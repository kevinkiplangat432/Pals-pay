from datetime import datetime, timezone
from extensions import db
from .enums import PaymentProvider


class PaymentMethod(db.Model):
    __tablename__ = 'payment_methods'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id', ondelete='CASCADE'), 
        nullable=False,
        index=True
    )
    
    # Provider details
    provider = db.Column(
        db.Enum(PaymentProvider, name="payment_provider_enum"),
        nullable=False
    )
    
    # Account reference (phone number for MPesa, account number for bank)
    account_reference = db.Column(db.String(50), nullable=False)
    account_name = db.Column(db.String(100), nullable=True)
    
    # Provider-specific metadata
    provider_metadata = db.Column(db.JSON, nullable=True)  # Store bank details, card last4, etc.
    
    # Status
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Security
    verification_token = db.Column(db.String(100), nullable=True)
    verified_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=db.func.now(), nullable=True)
    last_used_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='payment_methods_list')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_payment_methods_user_provider', 'user_id', 'provider'),
        db.Index('idx_payment_methods_account_ref', 'account_reference'),
        db.Index('idx_payment_methods_is_default', 'is_default'),
        db.UniqueConstraint('user_id', 'provider', 'account_reference', name='unique_user_payment_method'),
    )
    
    def set_as_default(self):
        # First, unset any existing default
        PaymentMethod.query.filter_by(
            user_id=self.user_id, 
            is_default=True
        ).update({'is_default': False})
        
        self.is_default = True
        return self
    
    def mark_as_used(self):
        self.last_used_at = datetime.now(timezone.utc)
        return self
    
    def verify(self, token=None):
        if token and self.verification_token != token:
            return False
        
        self.is_verified = True
        self.verified_at = datetime.now(timezone.utc)
        self.verification_token = None
        return True
    
    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'provider': self.provider.value,
            'account_reference': self.account_reference,
            'account_name': self.account_name,
            'is_default': self.is_default,
            'is_verified': self.is_verified,
            'is_active': self.is_active,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_sensitive and self.provider_metadata:
            data['provider_metadata'] = self.provider_metadata
        
        # Mask sensitive data for security
        if not include_sensitive and self.account_reference:
            if self.provider == PaymentProvider.mpesa:
                # Mask phone number: +2547*****89
                data['account_reference'] = self._mask_phone_number(self.account_reference)
            elif self.provider == PaymentProvider.bank:
                # Mask account number: ****1234
                data['account_reference'] = self._mask_account_number(self.account_reference)
            elif self.provider == PaymentProvider.card:
                # Mask card number: **** **** **** 1234
                data['account_reference'] = self._mask_card_number(self.account_reference)
        
        return data
    
    @staticmethod
    def _mask_phone_number(phone):
        if len(phone) >= 10:
            return phone[:4] + '*' * (len(phone) - 6) + phone[-2:]
        return phone
    
    @staticmethod
    def _mask_account_number(account):
        if len(account) >= 4:
            return '*' * (len(account) - 4) + account[-4:]
        return account
    
    @staticmethod
    def _mask_card_number(card):
        if len(card) >= 4:
            return '**** **** **** ' + card[-4:]
        return card
    
    def __repr__(self):
        return f'<PaymentMethod user_id={self.user_id} provider={self.provider.value} ref={self.account_reference}>'
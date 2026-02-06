# models/payout_destination.py - Traceability for money destinations
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import JSONB
from decimal import Decimal
from ..extensions import db
from .enums import PaymentProvider


class PayoutDestination(db.Model):
    __tablename__ = 'payout_destinations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Destination details
    destination_type = db.Column(db.String(20), nullable=False)  # 'mpesa', 'bank', 'wallet', 'cash_pickup'
    provider = db.Column(db.Enum(PaymentProvider, name="payment_provider_enum"), nullable=True)
    
    # Identifier (masked for security)
    masked_identifier = db.Column(db.String(100), nullable=False, index=True)
    full_identifier = db.Column(db.String(200), nullable=True)  # Encrypted in production
    
    # Account information
    account_name = db.Column(db.String(100), nullable=False)
    account_type = db.Column(db.String(30), nullable=True)
    
    # Location
    country = db.Column(db.String(2), nullable=False)  # ISO 3166-1 alpha-2
    institution_name = db.Column(db.String(100), nullable=True)
    institution_code = db.Column(db.String(20), nullable=True)
    branch_code = db.Column(db.String(20), nullable=True)
    
    # Status
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    verification_method = db.Column(db.String(30), nullable=True)
    
    # Limits
    daily_limit = db.Column(db.Numeric(12, 2), nullable=True)
    monthly_limit = db.Column(db.Numeric(12, 2), nullable=True)
    
    # Usage tracking
    total_payouts = db.Column(db.Integer, default=0, nullable=False)
    total_amount = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    
    # Metadata
    provider_metadata = db.Column(JSONB, nullable=True)
    meta_data = db.Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=db.func.now(), nullable=True)
    last_used_at = db.Column(db.DateTime(timezone=True), nullable=True)
    verified_at = db.Column(db.DateTime(timezone=True), nullable=True)
    deactivated_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='payout_destinations')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_payout_destinations_user_type', 'user_id', 'destination_type'),
        db.Index('idx_payout_destinations_country', 'country'),
        db.Index('idx_payout_destinations_verified', 'is_verified', 'is_active'),
        db.UniqueConstraint('user_id', 'masked_identifier', name='unique_user_payout_destination'),
    )
    
    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'destination_type': self.destination_type,
            'provider': self.provider.value if self.provider else None,
            'masked_identifier': self.masked_identifier,
            'account_name': self.account_name,
            'account_type': self.account_type,
            'country': self.country,
            'institution_name': self.institution_name,
            'institution_code': self.institution_code,
            'branch_code': self.branch_code,
            'is_verified': self.is_verified,
            'is_active': self.is_active,
            'verification_method': self.verification_method,
            'daily_limit': float(self.daily_limit) if self.daily_limit else None,
            'monthly_limit': float(self.monthly_limit) if self.monthly_limit else None,
            'total_payouts': self.total_payouts,
            'total_amount': float(self.total_amount),
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None
        }
        
        if include_sensitive and self.provider_metadata:
            data['provider_metadata'] = self.provider_metadata
        
        return data
    
    def __repr__(self):
        return f'<PayoutDestination user_id={self.user_id} type={self.destination_type} identifier={self.masked_identifier}>'
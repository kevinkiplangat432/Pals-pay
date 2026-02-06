# models/account.py - Legal entity separate from user
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from ..extensions import db


class Account(db.Model):
    __tablename__ = 'accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False, index=True)
    
    # Account type
    account_type = db.Column(db.String(20), nullable=False, default='individual')  # 'individual', 'business', 'trust'
    
    # Legal information
    legal_name = db.Column(db.String(200), nullable=False)
    trading_name = db.Column(db.String(200), nullable=True)
    registration_number = db.Column(db.String(50), nullable=True, index=True)
    tax_id = db.Column(db.String(50), nullable=True, index=True)
    
    # Incorporation details
    country_of_incorporation = db.Column(db.String(2), nullable=False)  # ISO 3166-1 alpha-2
    date_of_incorporation = db.Column(db.Date, nullable=True)
    business_type = db.Column(db.String(50), nullable=True)  # 'sole_proprietor', 'llc', 'corporation', etc.
    
    # Address
    registered_address = db.Column(db.Text, nullable=True)
    mailing_address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    postal_code = db.Column(db.String(20), nullable=True)
    
    # Contact information
    primary_email = db.Column(db.String(120), nullable=False, index=True)
    primary_phone = db.Column(db.String(20), nullable=False, index=True)
    website = db.Column(db.String(200), nullable=True)
    
    # Compliance
    kyc_status = db.Column(db.String(20), default='pending', nullable=False)  # 'pending', 'verified', 'rejected'
    kyc_level = db.Column(db.Integer, default=0, nullable=False)
    risk_score = db.Column(db.Integer, default=0, nullable=False)
    compliance_notes = db.Column(db.Text, nullable=True)
    
    # Retention policy
    retention_class = db.Column(db.String(20), default='financial', nullable=False)  # 'standard', 'financial', 'regulatory'
    
    # Metadata
    meta_data = db.Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=db.func.now(), nullable=True)
    verified_at = db.Column(db.DateTime(timezone=True), nullable=True)
    last_reviewed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Relationships
    users = db.relationship('UserAccount', backref='account', lazy='dynamic', cascade='all, delete-orphan')
    wallets = db.relationship('Wallet', backref='account', lazy='dynamic')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_accounts_country_type', 'country_of_incorporation', 'account_type'),
        db.Index('idx_accounts_kyc_status', 'kyc_status', 'kyc_level'),
        db.Index('idx_accounts_retention', 'retention_class'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'public_id': str(self.public_id),
            'account_type': self.account_type,
            'legal_name': self.legal_name,
            'trading_name': self.trading_name,
            'registration_number': self.registration_number,
            'tax_id': self.tax_id,
            'country_of_incorporation': self.country_of_incorporation,
            'date_of_incorporation': self.date_of_incorporation.isoformat() if self.date_of_incorporation else None,
            'business_type': self.business_type,
            'registered_address': self.registered_address,
            'mailing_address': self.mailing_address,
            'city': self.city,
            'postal_code': self.postal_code,
            'primary_email': self.primary_email,
            'primary_phone': self.primary_phone,
            'website': self.website,
            'kyc_status': self.kyc_status,
            'kyc_level': self.kyc_level,
            'risk_score': self.risk_score,
            'retention_class': self.retention_class,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'last_reviewed_at': self.last_reviewed_at.isoformat() if self.last_reviewed_at else None
        }
    
    def __repr__(self):
        return f'<Account {self.legal_name} ({self.account_type})>'
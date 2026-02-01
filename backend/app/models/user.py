
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.postgresql import UUID
import uuid
from extensions import db
from .enums import KYCStatus


class User(db.Model):
   
    __tablename__ = 'users'
    
    # Identity fields
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(
        UUID(as_uuid=True),
        unique=True,
        default=uuid.uuid4,
        nullable=False,
        index=True
    )
    
    # Contact information
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False, index=True)  # Primary identifier
    
    # Profile fields
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    
    # Security
    password_hash = db.Column(db.String(255), nullable=False)
    two_factor_enabled = db.Column(db.Boolean, default=False, nullable=False)
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Permissions & Status
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    
    # KYC Status (kept in sync with KYCVerification model)
    kyc_status = db.Column(
        db.Enum(KYCStatus, name="kyc_status_enum"),
        default=KYCStatus.unverified,
        nullable=False
    )
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=db.func.now(), nullable=True)
    
    # Relationships
    wallet = db.relationship('Wallet', backref='user', uselist=False, cascade='all, delete-orphan')
    kyc_verification = db.relationship('KYCVerification', backref='user', uselist=False, cascade='all, delete-orphan')
    payment_methods = db.relationship('PaymentMethod', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_users_phone_email', 'phone_number', 'email'),
        db.Index('idx_users_created_at', 'created_at'),
        db.Index('idx_users_kyc_status', 'kyc_status'),
    )
    
    def __init__(self, **kwargs):
        """Initialize user with default values"""
        super().__init__(**kwargs)
        # Create wallet automatically for new users
        if not self.wallet:
            from .wallet import Wallet
            self.wallet = Wallet()
        # Create KYC record
        if not self.kyc_verification:
            from .kyc import KYCVerification
            self.kyc_verification = KYCVerification()
    
    def set_password(self, password):
    
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def can_transact(self, amount=0):
        if not self.is_active:
            return {'allowed': False, 'reason': 'Account is inactive'}
        
        if self.kyc_status != KYCStatus.verified:
            return {'allowed': False, 'reason': 'KYC not verified'}
        
        if self.wallet and self.wallet.status.value == 'frozen':
            return {'allowed': False, 'reason': 'Wallet is frozen'}
        
        return {'allowed': True, 'reason': 'OK'}
    
    def to_dict(self, include_wallet=False, include_kyc=False):
        data = {
            'id': self.id,
            'public_id': str(self.public_id),
            'email': self.email,
            'username': self.username,
            'phone_number': self.phone_number,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'kyc_status': self.kyc_status.value,
            'two_factor_enabled': self.two_factor_enabled,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_wallet and self.wallet:
            data['wallet'] = self.wallet.to_dict()
            
        if include_kyc and self.kyc_verification:
            data['kyc'] = self.kyc_verification.to_dict()
            
        return data
    
    def __repr__(self):
        return f'<User {self.username} - {self.phone_number} - {self.kyc_status.value}>'
# models/user.py - Updated with international fields
from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.postgresql import UUID
import uuid
from ..extensions import db
from .enums import KYCStatus

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False, index=True)
    
    # Contact Information
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    phone_number = db.Column(db.String(20), nullable=False, index=True)
    phone_country_code = db.Column(db.String(5), default='+254', nullable=False)
    
    # Profile Information
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    
    # Location Information
    country_code = db.Column(db.String(2), default='KE', nullable=False)  # ISO 3166-1 alpha-2
    region = db.Column(db.String(20), default='east_africa', nullable=False)
    preferred_currency = db.Column(db.String(3), default='KES', nullable=False)
    language = db.Column(db.String(5), default='en', nullable=False)  # en, sw, fr, etc.
    timezone = db.Column(db.String(50), default='Africa/Nairobi', nullable=False)
    
    # Security
    password_hash = db.Column(db.String(255), nullable=False)
    
    # OTP fields
    otp_code = db.Column(db.String(6), nullable=True)
    otp_expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    otp_attempts = db.Column(db.Integer, default=0, nullable=False)
    otp_locked_until = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Permissions & Status
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    
    # KYC Status
    kyc_status = db.Column(db.Enum(KYCStatus, name="kyc_status_enum"), default=KYCStatus.unverified, nullable=False)
    kyc_level = db.Column(db.Integer, default=0, nullable=False)  # 0=basic, 1=verified, 2=enhanced
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=db.func.now(), nullable=True)
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)
    last_location_update = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Relationships
    wallet = db.relationship('Wallet', backref='user', uselist=False, cascade='all, delete-orphan')
    kyc_verification = db.relationship('KYCVerification', backref='user', uselist=False, cascade='all, delete-orphan')
    payment_methods = db.relationship('PaymentMethod', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_users_country_region', 'country_code', 'region'),
        db.Index('idx_users_phone_full', 'phone_country_code', 'phone_number'),
        db.Index('idx_users_language_currency', 'language', 'preferred_currency'),
    )
    
    def __init__(self, **kwargs):
        # Set default region based on country if not provided
        if 'country_code' in kwargs and 'region' not in kwargs:
            from app.services.region_service import RegionService
            kwargs['region'] = RegionService.get_region_by_country(kwargs['country_code'])
        
        # Set default currency based on region
        if 'region' in kwargs and 'preferred_currency' not in kwargs:
            from flask import current_app
            region_config = current_app.config['SUPPORTED_REGIONS'].get(kwargs['region'], {})
            kwargs['preferred_currency'] = region_config.get('default_currency', 'KES')
        
        super().__init__(**kwargs)
        
        # Create wallet automatically with region settings
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
    
    def get_full_phone_number(self):
        return f"{self.phone_country_code}{self.phone_number}"
    
    def can_transact(self, amount=0, target_country=None):
        """Enhanced transaction permission check with international support"""
        from app.services.region_service import RegionService
        
        if not self.is_active:
            return {'allowed': False, 'reason': 'Account is inactive'}
        
        if not self.is_verified:
            return {'allowed': False, 'reason': 'Account not verified'}
        
        # KYC check based on transaction size
        if amount > 10000 and self.kyc_status.value != 'verified':  # 10,000 in default currency
            return {'allowed': False, 'reason': 'KYC verification required for large transfers'}
        
        if self.wallet and self.wallet.status.value == 'frozen':
            return {'allowed': False, 'reason': 'Wallet is frozen'}
        
        # Check if cross-region transfer is allowed
        if target_country and target_country != self.country_code:
            from app.services.compliance_service import ComplianceService
            compliance_check = ComplianceService.check_cross_border_transfer(
                self.country_code, 
                target_country, 
                amount
            )
            if not compliance_check['allowed']:
                return compliance_check
        
        return {'allowed': True, 'reason': 'OK'}
    
    def update_location(self, country_code, ip_address=None):
        """Update user location based on IP or manual selection"""
        from app.services.region_service import RegionService
        
        region = RegionService.get_region_by_country(country_code)
        if region != self.region:
            self.region = region
            self.country_code = country_code
            
            # Update currency based on new region
            from flask import current_app
            region_config = current_app.config['SUPPORTED_REGIONS'].get(region, {})
            if self.preferred_currency not in region_config.get('currencies', []):
                self.preferred_currency = region_config.get('default_currency', 'KES')
            
            self.last_location_update = datetime.now(timezone.utc)
    
    def to_dict(self, include_wallet=False, include_kyc=False):
        data = {
            'id': self.id,
            'public_id': str(self.public_id),
            'email': self.email,
            'username': self.username,
            'phone_number': self.phone_number,
            'phone_country_code': self.phone_country_code,
            'full_phone': self.get_full_phone_number(),
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'country_code': self.country_code,
            'region': self.region,
            'preferred_currency': self.preferred_currency,
            'language': self.language,
            'timezone': self.timezone,
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'kyc_status': self.kyc_status.value,
            'kyc_level': self.kyc_level,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_wallet and self.wallet:
            data['wallet'] = self.wallet.to_dict()
            
        if include_kyc and self.kyc_verification:
            data['kyc'] = self.kyc_verification.to_dict()
            
        return data
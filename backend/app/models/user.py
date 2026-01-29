"""
User Model - Core user authentication and profile model
"""

from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class User(db.Model):
    """
    User model for authentication and profile management
    Phone number serves as the primary client identifier
    """
    __tablename__ = 'users'
    
    # Identity fields
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False, index=True)  # Client ID
    
    # Profile fields
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    
    # Security
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Permissions
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    wallet = db.relationship('Wallet', backref='user', uselist=False, cascade='all, delete-orphan')
    
    sent_transactions = db.relationship(
        'Transaction',
        foreign_keys='Transaction.sender_id',
        backref='sender',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    received_transactions = db.relationship(
        'Transaction',
        foreign_keys='Transaction.receiver_id',
        backref='receiver',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    beneficiaries = db.relationship(
        'Beneficiary',
        foreign_keys='Beneficiary.user_id',
        backref='user',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    def set_password(self, password):
        """
        Hashes and stores password securely using bcrypt
        
        Args:
            password (str): Plain text password
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """
        Validates login credentials
        
        Args:
            password (str): Plain text password to verify
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_wallet=False):
        """
        Serializes user data for API responses
        
        Args:
            include_wallet (bool): Whether to include wallet data
            
        Returns:
            dict: User data dictionary
        """
        data = {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'phone_number': self.phone_number,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': f"{self.first_name} {self.last_name}",
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_wallet and self.wallet:
            data['wallet'] = self.wallet.to_dict()
            
        return data
    
    def __repr__(self):
        return f'<User {self.username} - {self.phone_number}>'

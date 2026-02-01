from datetime import datetime, timezone
from extensions import db


class Beneficiary(db.Model):

    __tablename__ = 'beneficiaries'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relationship fields
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id', ondelete='CASCADE'), 
        nullable=False,
        index=True
    )
    beneficiary_wallet_id = db.Column(
        db.Integer, 
        db.ForeignKey('wallets.id', ondelete='CASCADE'), 
        nullable=False,
        index=True
    )
    
    # Metadata
    nickname = db.Column(db.String(50), nullable=True)
    category = db.Column(db.String(20), nullable=True)  # family, friend, business, etc.
    
    # Usage statistics (denormalized for performance)
    total_transfers = db.Column(db.Integer, default=0, nullable=False)
    total_amount = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    last_transfer_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Security limits
    daily_limit = db.Column(db.Numeric(12, 2), nullable=True)  # Custom daily limit for this beneficiary
    is_trusted = db.Column(db.Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=db.func.now(), nullable=True)
    
    # Relationships
    beneficiary_wallet = db.relationship(
        'Wallet',
        foreign_keys=[beneficiary_wallet_id],
        backref='beneficiary_for'
    )
    
    # Indexes
    __table_args__ = (
        db.UniqueConstraint('user_id', 'beneficiary_wallet_id', name='unique_user_beneficiary'),
        db.Index('idx_beneficiaries_user_category', 'user_id', 'category'),
        db.Index('idx_beneficiaries_last_transfer', 'last_transfer_at'),
        db.CheckConstraint('user_id != beneficiary_wallet.user_id', name='check_not_self_beneficiary'),
    )
    
    def update_statistics(self, amount):
        from decimal import Decimal
        
        self.total_transfers += 1
        self.total_amount += Decimal(str(amount))
        self.last_transfer_at = datetime.now(timezone.utc)
    
    def can_send(self, amount):
        from decimal import Decimal
        
        amount = Decimal(str(amount))
        
        # Check custom daily limit
        if self.daily_limit and amount > self.daily_limit:
            return {'allowed': False, 'reason': 'Exceeds beneficiary daily limit'}
        
        # For untrusted beneficiaries, apply lower limits
        if not self.is_trusted and amount > Decimal('50000.00'):
            return {'allowed': False, 'reason': 'Limit for untrusted beneficiaries is 50,000'}
        
        return {'allowed': True, 'reason': 'OK'}
    
    def to_dict(self, include_user=True):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'beneficiary_wallet_id': self.beneficiary_wallet_id,
            'nickname': self.nickname,
            'category': self.category,
            'total_transfers': self.total_transfers,
            'total_amount': float(self.total_amount),
            'last_transfer_at': self.last_transfer_at.isoformat() if self.last_transfer_at else None,
            'daily_limit': float(self.daily_limit) if self.daily_limit else None,
            'is_trusted': self.is_trusted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_user and self.beneficiary_wallet and self.beneficiary_wallet.user:
            user = self.beneficiary_wallet.user
            data['beneficiary'] = {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'phone_number': user.phone_number,
                'full_name': user.get_full_name(),
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        
        return data
    
    def __repr__(self):
        nickname_str = f" ({self.nickname})" if self.nickname else ""
        return f'<Beneficiary user_id={self.user_id} beneficiary_wallet_id={self.beneficiary_wallet_id}{nickname_str}>'
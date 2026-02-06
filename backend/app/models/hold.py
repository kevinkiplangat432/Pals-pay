# models/hold.py - Risk and compliance holds
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.dialects.postgresql import UUID
import uuid
from ..extensions import db


class Hold(db.Model):
    __tablename__ = 'holds'
    
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False, index=True)
    
    # Target
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallets.id', ondelete='CASCADE'), nullable=False, index=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id', ondelete='CASCADE'), nullable=True, index=True)
    
    # Hold details
    hold_type = db.Column(db.String(30), nullable=False)  # 'risk', 'compliance', 'fraud', 'user', 'dispute'
    reason = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(3), default='KES', nullable=False)
    
    # Status
    status = db.Column(db.String(20), default='active', nullable=False)  # 'active', 'released', 'expired'
    
    # Expiry
    expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    auto_release = db.Column(db.Boolean, default=False, nullable=False)
    
    # Resolution
    resolved_at = db.Column(db.DateTime(timezone=True), nullable=True)
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    resolution_reason = db.Column(db.Text, nullable=True)
    resolution_action = db.Column(db.String(50), nullable=True)  # 'release', 'refund', 'escalate'
    
    # Metadata
    reference = db.Column(db.String(100), nullable=True)
    meta_data = db.Column(db.JSON, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=db.func.now(), nullable=True)
    
    # Relationships
    wallet = db.relationship('Wallet', backref='holds')
    transaction = db.relationship('Transaction', backref='holds')
    resolver = db.relationship('User', foreign_keys=[resolved_by])
    
    # Indexes
    __table_args__ = (
        db.Index('idx_holds_wallet_status', 'wallet_id', 'status'),
        db.Index('idx_holds_type_status', 'hold_type', 'status'),
        db.Index('idx_holds_expiry', 'expires_at', 'status'),
        db.Index('idx_holds_created', 'created_at'),
    )
    
    def is_expired(self):
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    def release(self, resolved_by_user_id=None, reason=None):
        """Release the hold"""
        if self.status != 'active':
            return False
        
        self.status = 'released'
        self.resolved_at = datetime.now(timezone.utc)
        self.resolved_by = resolved_by_user_id
        self.resolution_reason = reason
        self.resolution_action = 'release'
        
        # Unlock funds in wallet
        if self.wallet:
            self.wallet.unlock_funds(self.amount, self.currency)
        
        return True
    
    def to_dict(self):
        return {
            'id': self.id,
            'public_id': str(self.public_id),
            'wallet_id': self.wallet_id,
            'transaction_id': self.transaction_id,
            'hold_type': self.hold_type,
            'reason': self.reason,
            'amount': float(self.amount),
            'currency': self.currency,
            'status': self.status,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'auto_release': self.auto_release,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by,
            'resolution_reason': self.resolution_reason,
            'resolution_action': self.resolution_action,
            'reference': self.reference,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_expired': self.is_expired()
        }
    
    def __repr__(self):
        return f'<Hold {self.public_id} type={self.hold_type} amount={self.amount} status={self.status}>'
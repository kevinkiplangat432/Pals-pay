# models/user_account.py - Link between users and accounts
from datetime import datetime, timezone
from ..extensions import db


class UserAccount(db.Model):
    __tablename__ = 'user_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Role and permissions
    role = db.Column(db.String(30), nullable=False, default='owner')  # 'owner', 'admin', 'viewer', 'approver'
    permissions = db.Column(db.JSON, default={}, nullable=True)  # Custom permissions
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_primary = db.Column(db.Boolean, default=False, nullable=False)
    
    # Verification
    verified_at = db.Column(db.DateTime(timezone=True), nullable=True)
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=db.func.now(), nullable=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='account_links')
    verifier = db.relationship('User', foreign_keys=[verified_by])
    
    # Indexes
    __table_args__ = (
        db.UniqueConstraint('user_id', 'account_id', name='unique_user_account'),
        db.Index('idx_user_accounts_role', 'account_id', 'role'),
        db.Index('idx_user_accounts_primary', 'user_id', 'is_primary'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'account_id': self.account_id,
            'role': self.role,
            'permissions': self.permissions,
            'is_active': self.is_active,
            'is_primary': self.is_primary,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'verified_by': self.verified_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<UserAccount user_id={self.user_id} account_id={self.account_id} role={self.role}>'
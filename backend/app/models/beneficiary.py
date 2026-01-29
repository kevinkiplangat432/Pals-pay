"""
Beneficiary Model - Saves frequent recipients for quick access
"""

from datetime import datetime
from extensions import db


class Beneficiary(db.Model):
    """
    Beneficiary model for saving frequent recipients
    Allows users to save contacts for quick transfers
    """
    __tablename__ = 'beneficiaries'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relationship fields
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    beneficiary_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Optional nickname
    nickname = db.Column(db.String(50), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    beneficiary_user = db.relationship(
        'User',
        foreign_keys=[beneficiary_id],
        backref='beneficiary_of'
    )
    
    # Unique constraint - prevent duplicate beneficiaries
    __table_args__ = (
        db.UniqueConstraint('user_id', 'beneficiary_id', name='unique_user_beneficiary'),
        db.CheckConstraint('user_id != beneficiary_id', name='check_not_self_beneficiary'),
    )
    
    def to_dict(self):
        """
        Returns beneficiary info with username, email, and full name
        
        Returns:
            dict: Beneficiary data dictionary
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'beneficiary_id': self.beneficiary_id,
            'nickname': self.nickname,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        # Include beneficiary user details
        if self.beneficiary_user:
            data['beneficiary'] = {
                'username': self.beneficiary_user.username,
                'email': self.beneficiary_user.email,
                'phone_number': self.beneficiary_user.phone_number,
                'full_name': f"{self.beneficiary_user.first_name} {self.beneficiary_user.last_name}",
                'first_name': self.beneficiary_user.first_name,
                'last_name': self.beneficiary_user.last_name
            }
        
        return data
    
    def __repr__(self):
        nickname_str = f" ({self.nickname})" if self.nickname else ""
        return f'<Beneficiary user_id={self.user_id} beneficiary_id={self.beneficiary_id}{nickname_str}>'

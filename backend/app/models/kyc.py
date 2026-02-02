from datetime import datetime, timezone
from ..extensions import db
from .enums import KYCStatus, DocumentType


class KYCVerification(db.Model):
    __tablename__ = 'kyc_verifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id', ondelete='CASCADE'), 
        unique=True,
        nullable=False,
        index=True
    )
    
    # Document information
    document_type = db.Column(
        db.Enum(DocumentType, name="document_type_enum"),
        nullable=True
    )
    document_number = db.Column(db.String(50), nullable=True, index=True)
    document_front_url = db.Column(db.String(500), nullable=True)
    document_back_url = db.Column(db.String(500), nullable=True)
    selfie_url = db.Column(db.String(500), nullable=True)
    
    # Verification details
    status = db.Column(
        db.Enum(KYCStatus, name="kyc_status_enum"),
        default=KYCStatus.unverified,
        nullable=False
    )
    
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    
    # Timestamps
    submitted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    verified_at = db.Column(db.DateTime(timezone=True), nullable=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=db.func.now(), nullable=True)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_kyc_status_submitted', 'status', 'submitted_at'),
        db.Index('idx_kyc_document_number', 'document_number'),
    )
    
    def submit_for_verification(self):
        """Mark KYC as submitted for verification"""
        self.status = KYCStatus.pending
        self.submitted_at = datetime.now(timezone.utc)
    
    def approve(self, verified_by_user_id):
        """Approve KYC verification"""
        self.status = KYCStatus.verified
        self.verified_by = verified_by_user_id
        self.verified_at = datetime.now(timezone.utc)
        self.rejection_reason = None
        # Set expiry to 1 year from now
        self.expires_at = datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year + 1)
        
        # Update user's KYC status
        if self.user:
            self.user.kyc_status = KYCStatus.verified
    
    def reject(self, reason):
        self.status = KYCStatus.rejected
        self.rejection_reason = reason
        self.verified_at = datetime.now(timezone.utc)
        
        # Update user's KYC status
        if self.user:
            self.user.kyc_status = KYCStatus.rejected
    
    def is_expired(self):
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'document_type': self.document_type.value if self.document_type else None,
            'document_number': self.document_number,
            'status': self.status.value,
            'rejection_reason': self.rejection_reason,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<KYCVerification user_id={self.user_id} status={self.status.value}>'
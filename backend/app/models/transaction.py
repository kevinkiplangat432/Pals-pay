
from datetime import datetime, timezone
from decimal import Decimal
import uuid
from sqlalchemy.dialects.postgresql import UUID
from extensions import db
from .enums import TransactionStatus, TransactionType, PaymentProvider


class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Participants - using wallet IDs for better accounting
    sender_wallet_id = db.Column(
        db.Integer, 
        db.ForeignKey('wallets.id', ondelete='SET NULL'), 
        nullable=True,
        index=True
    )
    receiver_wallet_id = db.Column(
        db.Integer, 
        db.ForeignKey('wallets.id', ondelete='SET NULL'), 
        nullable=True,
        index=True
    )
    
    # For non-wallet transactions (bank, mpesa)
    external_sender = db.Column(db.String(100), nullable=True)  # Phone number, account number
    external_receiver = db.Column(db.String(100), nullable=True)
    
    # Transaction details
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    fee = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    net_amount = db.Column(db.Numeric(12, 2), nullable=False)  # amount - fee
    
    # Enums for better performance and data integrity
    transaction_type = db.Column(
        db.Enum(TransactionType, name="transaction_type_enum"),
        nullable=False
    )
    
    status = db.Column(
        db.Enum(TransactionStatus, name="transaction_status_enum"),
        nullable=False,
        default=TransactionStatus.pending
    )
    
    provider = db.Column(
        db.Enum(PaymentProvider, name="payment_provider_enum"),
        nullable=False,
        default=PaymentProvider.internal
    )
    
    # Tracking and idempotency
    reference = db.Column(db.String(100), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    external_reference = db.Column(db.String(100), nullable=True, index=True)  # Daraja transaction ID
    idempotency_key = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    
    # Metadata
    description = db.Column(db.Text, nullable=True)
    metadata = db.Column(db.JSON, nullable=True)  # For storing provider-specific data
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    initiated_at = db.Column(db.DateTime(timezone=True), nullable=True)
    processed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    reversed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Relationships
    sender_wallet = db.relationship(
        'Wallet', 
        foreign_keys=[sender_wallet_id],
        backref='sent_transactions'
    )
    
    receiver_wallet = db.relationship(
        'Wallet', 
        foreign_keys=[receiver_wallet_id],
        backref='received_transactions'
    )
    
    ledger_entries = db.relationship(
        'LedgerEntry', 
        backref='transaction',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    # Indexes
    __table_args__ = (
        db.Index('idx_transactions_created_at', 'created_at'),
        db.Index('idx_transactions_status_type', 'status', 'transaction_type'),
        db.Index('idx_transactions_provider_ext', 'provider', 'external_reference'),
        db.Index('idx_transactions_sender_receiver', 'sender_wallet_id', 'receiver_wallet_id'),
        db.Index('idx_transactions_idempotency', 'idempotency_key'),
        db.CheckConstraint('amount > 0', name='check_positive_amount'),
        db.CheckConstraint('fee >= 0', name='check_non_negative_fee'),
        db.CheckConstraint('net_amount > 0', name='check_positive_net_amount'),
        db.CheckConstraint('net_amount = amount - fee', name='check_net_amount_calculation'),
    )
    
    def __init__(self, **kwargs):
        """Initialize with calculated net_amount"""
        super().__init__(**kwargs)
        if 'amount' in kwargs and 'fee' in kwargs:
            self.net_amount = Decimal(str(kwargs['amount'])) - Decimal(str(kwargs['fee']))
        elif 'amount' in kwargs and not hasattr(self, 'net_amount'):
            self.net_amount = Decimal(str(kwargs['amount']))
    
    @staticmethod
    def calculate_fee(amount, transaction_type='transfer'):
        amount = Decimal(str(amount))
        
        # Fee structure (customize as needed)
        if transaction_type == 'transfer':
            # 1% fee, minimum 10 KES, maximum 5000 KES
            fee = amount * Decimal('0.01')
            min_fee = Decimal('10.00')
            max_fee = Decimal('5000.00')
            fee = max(fee, min_fee)
            fee = min(fee, max_fee)
        elif transaction_type == 'withdrawal':
            # Fixed fee for withdrawals
            fee = Decimal('27.50')
        elif transaction_type == 'deposit':
            # No fee for deposits
            fee = Decimal('0.00')
        else:
            fee = Decimal('0.00')
        
        return fee.quantize(Decimal('0.01'))
    
    def update_status(self, new_status, metadata=None):
        valid_transitions = {
            TransactionStatus.pending: [TransactionStatus.processing, TransactionStatus.failed],
            TransactionStatus.processing: [TransactionStatus.completed, TransactionStatus.failed],
            TransactionStatus.completed: [TransactionStatus.reversed],
            TransactionStatus.failed: [TransactionStatus.pending],  # Retry
            TransactionStatus.reversed: []
        }
        
        if new_status not in valid_transitions.get(self.status, []):
            return False
        
        self.status = new_status
        now = datetime.now(timezone.utc)
        
        # Update timestamps based on status
        if new_status == TransactionStatus.processing:
            self.initiated_at = now
        elif new_status == TransactionStatus.completed:
            self.completed_at = now
            self.processed_at = now
        elif new_status == TransactionStatus.failed:
            self.processed_at = now
        elif new_status == TransactionStatus.reversed:
            self.reversed_at = now
        
        # Update metadata
        if metadata and self.metadata:
            self.metadata.update(metadata)
        elif metadata:
            self.metadata = metadata
        
        return True
    
    def to_dict(self, include_wallets=True, include_ledger=False):
        data = {
            'id': self.id,
            'sender_wallet_id': self.sender_wallet_id,
            'receiver_wallet_id': self.receiver_wallet_id,
            'external_sender': self.external_sender,
            'external_receiver': self.external_receiver,
            'amount': float(self.amount),
            'fee': float(self.fee),
            'net_amount': float(self.net_amount),
            'transaction_type': self.transaction_type.value,
            'status': self.status.value,
            'provider': self.provider.value,
            'reference': self.reference,
            'external_reference': self.external_reference,
            'idempotency_key': str(self.idempotency_key),
            'description': self.description,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'initiated_at': self.initiated_at.isoformat() if self.initiated_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'reversed_at': self.reversed_at.isoformat() if self.reversed_at else None
        }
        
        if include_wallets:
            if self.sender_wallet and self.sender_wallet.user:
                data['sender'] = {
                    'user_id': self.sender_wallet.user_id,
                    'username': self.sender_wallet.user.username,
                    'phone_number': self.sender_wallet.user.phone_number,
                    'full_name': self.sender_wallet.user.get_full_name()
                }
            
            if self.receiver_wallet and self.receiver_wallet.user:
                data['receiver'] = {
                    'user_id': self.receiver_wallet.user_id,
                    'username': self.receiver_wallet.user.username,
                    'phone_number': self.receiver_wallet.user.phone_number,
                    'full_name': self.receiver_wallet.user.get_full_name()
                }
        
        if include_ledger:
            data['ledger_entries'] = [
                entry.to_dict() for entry in self.ledger_entries.all()
            ]
        
        return data
    
    def __repr__(self):
        return f'<Transaction {self.reference} {self.transaction_type.value} {self.amount} {self.status.value}>'
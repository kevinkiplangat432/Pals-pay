from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import uuid
from sqlalchemy.dialects.postgresql import UUID, JSONB
from ..extensions import db
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
    
    # Currency and FX information
    source_currency = db.Column(db.String(3), nullable=False, default='KES')
    target_currency = db.Column(db.String(3), nullable=False, default='KES')
    fx_rate = db.Column(db.Numeric(10, 6), nullable=True)
    fx_provider = db.Column(db.String(50), nullable=True)
    fx_timestamp = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Country information for compliance
    source_country = db.Column(db.String(2), nullable=True)  # ISO 3166-1 alpha-2
    destination_country = db.Column(db.String(2), nullable=True)
    is_cross_border = db.Column(db.Boolean, default=False, nullable=False)
    
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
    
    # Additional status fields for partial success scenarios
    debit_status = db.Column(db.String(20), nullable=True)  # 'pending', 'completed', 'failed'
    credit_status = db.Column(db.String(20), nullable=True)  # 'pending', 'completed', 'failed'
    settlement_status = db.Column(db.String(20), nullable=True)  # 'pending', 'settled', 'failed'
    settlement_date = db.Column(db.DateTime(timezone=True), nullable=True)
    settlement_reference = db.Column(db.String(100), nullable=True)
    
    # Failure tracking
    failure_domain = db.Column(db.String(20), nullable=True)  # 'user', 'provider', 'system'
    failure_reason = db.Column(db.Text, nullable=True)
    failure_code = db.Column(db.String(50), nullable=True)
    
    # Compliance and reporting
    reporting_category = db.Column(db.String(50), nullable=True)
    is_reportable = db.Column(db.Boolean, default=False, nullable=False)
    reported_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Audit fields
    sequence_number = db.Column(db.Integer, nullable=True)  # For deterministic ordering
    meta_data = db.Column(JSONB, nullable=True)  # For storing provider-specific data
    
    # Channel information for velocity controls
    channel = db.Column(db.String(20), nullable=True)  # 'api', 'web', 'mobile'
    ip_address = db.Column(db.String(45), nullable=True)
    device_id = db.Column(db.String(100), nullable=True)
    
    # Reversal/Refund tracking
    original_transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=True)
    reversal_reason = db.Column(db.Text, nullable=True)
    refund_reason = db.Column(db.Text, nullable=True)
    is_reversal = db.Column(db.Boolean, default=False, nullable=False)
    is_refund = db.Column(db.Boolean, default=False, nullable=False)
    
    # Funding source and destination tracking
    funding_source_id = db.Column(db.Integer, db.ForeignKey('funding_sources.id'), nullable=True)
    payout_destination_id = db.Column(db.Integer, db.ForeignKey('payout_destinations.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    initiated_at = db.Column(db.DateTime(timezone=True), nullable=True)
    processed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    reversed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    expired_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
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
    
    original_transaction = db.relationship(
        'Transaction',
        remote_side=[id],
        backref='related_transactions'
    )
    
    # Indexes
    __table_args__ = (
        db.Index('idx_transactions_created_at', 'created_at'),
        db.Index('idx_transactions_status_type', 'status', 'transaction_type'),
        db.Index('idx_transactions_provider_ext', 'provider', 'external_reference'),
        db.Index('idx_transactions_sender_receiver', 'sender_wallet_id', 'receiver_wallet_id'),
        db.Index('idx_transactions_idempotency', 'idempotency_key'),
        db.Index('idx_transactions_sequence', 'sequence_number'),
        db.Index('idx_transactions_cross_border', 'is_cross_border'),
        db.Index('idx_transactions_source_dest', 'source_country', 'destination_country'),
        db.Index('idx_transactions_settlement', 'settlement_status', 'settlement_date'),
        db.Index('idx_transactions_original', 'original_transaction_id'),
        db.CheckConstraint('amount > 0', name='check_positive_amount'),
        db.CheckConstraint('fee >= 0', name='check_non_negative_fee'),
        db.CheckConstraint('net_amount > 0', name='check_positive_net_amount'),
        db.CheckConstraint('net_amount = amount - fee', name='check_net_amount_calculation'),
    )
    
    def __init__(self, **kwargs):
        """Initialize with calculated net_amount and FX information"""
        # Handle metadata separately to avoid issues
        metadata = kwargs.pop('metadata', None)
        
        super().__init__(**kwargs)
        
        # Set metadata after initialization
        if metadata:
            self.meta_data = metadata
        
        # Calculate net amount
        if 'amount' in kwargs and 'fee' in kwargs:
            self.net_amount = Decimal(str(kwargs['amount'])) - Decimal(str(kwargs['fee']))
        elif 'amount' in kwargs and not hasattr(self, 'net_amount'):
            self.net_amount = Decimal(str(kwargs['amount']))
        
        # Set cross-border flag
        if 'source_country' in kwargs and 'destination_country' in kwargs:
            self.is_cross_border = kwargs['source_country'] != kwargs['destination_country']
        
        # Set FX timestamp if rate provided
        if 'fx_rate' in kwargs and not self.fx_timestamp:
            self.fx_timestamp = datetime.now(timezone.utc)
    
    @staticmethod
    def calculate_fee(amount, transaction_type='transfer', is_cross_border=False):
        amount = Decimal(str(amount))
        
        # Fee structure based on transaction type and cross-border status
        if transaction_type == 'transfer':
            if is_cross_border:
                # Cross-border transfer fee: 2.5% with caps
                fee = amount * Decimal('0.025')
                min_fee = Decimal('50.00')
                max_fee = Decimal('10000.00')
            else:
                # Local transfer fee: 1% with caps
                fee = amount * Decimal('0.01')
                min_fee = Decimal('10.00')
                max_fee = Decimal('5000.00')
        elif transaction_type == 'withdrawal':
            # Fixed fee for withdrawals
            fee = Decimal('27.50')
        elif transaction_type == 'deposit':
            # No fee for deposits
            fee = Decimal('0.00')
        else:
            fee = Decimal('0.00')
        
        # Apply min/max caps
        fee = max(fee, min_fee)
        fee = min(fee, max_fee)
        
        return fee.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def update_status(self, new_status, metadata=None):
        valid_transitions = {
            TransactionStatus.pending: [TransactionStatus.processing, TransactionStatus.failed, TransactionStatus.expired],
            TransactionStatus.processing: [TransactionStatus.completed, TransactionStatus.failed],
            TransactionStatus.completed: [TransactionStatus.reversed],
            TransactionStatus.failed: [TransactionStatus.pending],  # Retry
            TransactionStatus.reversed: [],
            TransactionStatus.expired: []
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
        elif new_status == TransactionStatus.expired:
            self.expired_at = now
        
        # Update metadata
        if metadata:
            if self.metadata:
                self.metadata.update(metadata)
            else:
                self.metadata = metadata
        
        return True
    
    def create_reversal(self, reason, initiated_by):
        """Create a reversal transaction"""
        if self.status != TransactionStatus.completed:
            return None
        
        reversal = Transaction(
            original_transaction_id=self.id,
            is_reversal=True,
            reversal_reason=reason,
            
            # Reverse sender/receiver
            sender_wallet_id=self.receiver_wallet_id,
            receiver_wallet_id=self.sender_wallet_id,
            external_sender=self.external_receiver,
            external_receiver=self.external_sender,
            
            # Amount details
            amount=self.amount,
            fee=Decimal('0.00'),  # No fee for reversals
            net_amount=self.amount,
            
            # Currency and country
            source_currency=self.target_currency,
            target_currency=self.source_currency,
            source_country=self.destination_country,
            destination_country=self.source_country,
            is_cross_border=self.is_cross_border,
            
            # Transaction type
            transaction_type=TransactionType.transfer,
            status=TransactionStatus.pending,
            provider=self.provider,
            
            # Channel info
            channel='system',
            ip_address=None
        )
        
        # Log the reversal creation
        from .audit_log import AuditLog
        AuditLog.log_system_action(
            action='transaction_reversal_created',
            resource_type='transaction',
            resource_id=self.id,
            new_values={'reversal_id': reversal.id, 'reason': reason}
        )
        
        return reversal
    
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
            'source_currency': self.source_currency,
            'target_currency': self.target_currency,
            'fx_rate': float(self.fx_rate) if self.fx_rate else None,
            'fx_provider': self.fx_provider,
            'fx_timestamp': self.fx_timestamp.isoformat() if self.fx_timestamp else None,
            'source_country': self.source_country,
            'destination_country': self.destination_country,
            'is_cross_border': self.is_cross_border,
            'transaction_type': self.transaction_type.value,
            'status': self.status.value,
            'provider': self.provider.value,
            'reference': self.reference,
            'external_reference': self.external_reference,
            'idempotency_key': str(self.idempotency_key),
            'debit_status': self.debit_status,
            'credit_status': self.credit_status,
            'settlement_status': self.settlement_status,
            'settlement_date': self.settlement_date.isoformat() if self.settlement_date else None,
            'settlement_reference': self.settlement_reference,
            'failure_domain': self.failure_domain,
            'failure_reason': self.failure_reason,
            'failure_code': self.failure_code,
            'reporting_category': self.reporting_category,
            'is_reportable': self.is_reportable,
            'reported_at': self.reported_at.isoformat() if self.reported_at else None,
            'sequence_number': self.sequence_number,
            'metadata': self.meta_data,  # Fixed: use meta_data field
            'channel': self.channel,
            'ip_address': self.ip_address,
            'device_id': self.device_id,
            'original_transaction_id': self.original_transaction_id,
            'reversal_reason': self.reversal_reason,
            'refund_reason': self.refund_reason,
            'is_reversal': self.is_reversal,
            'is_refund': self.is_refund,
            'funding_source_id': self.funding_source_id,
            'payout_destination_id': self.payout_destination_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'initiated_at': self.initiated_at.isoformat() if self.initiated_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'reversed_at': self.reversed_at.isoformat() if self.reversed_at else None,
            'expired_at': self.expired_at.isoformat() if self.expired_at else None
        }
        
        if include_wallets:
            if self.sender_wallet and self.sender_wallet.user:
                data['sender'] = {
                    'user_id': self.sender_wallet.user_id,
                    'username': self.sender_wallet.user.username,
                    'phone_number': self.sender_wallet.user.phone_number,
                    'full_name': self.sender_wallet.user.get_full_name(),
                    'country_code': self.sender_wallet.user.country_code
                }
            
            if self.receiver_wallet and self.receiver_wallet.user:
                data['receiver'] = {
                    'user_id': self.receiver_wallet.user_id,
                    'username': self.receiver_wallet.user.username,
                    'phone_number': self.receiver_wallet.user.phone_number,
                    'full_name': self.receiver_wallet.user.get_full_name(),
                    'country_code': self.receiver_wallet.user.country_code
                }
        
        if include_ledger:
            data['ledger_entries'] = [
                entry.to_dict() for entry in self.ledger_entries.all()
            ]
        
        return data
    
    def __repr__(self):
        return f'<Transaction {self.reference} {self.transaction_type.value} {self.amount} {self.status.value}>'
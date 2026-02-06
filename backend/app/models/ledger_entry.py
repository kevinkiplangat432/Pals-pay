from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.dialects.postgresql import JSONB
from ..extensions import db


class LedgerEntry(db.Model):
    __tablename__ = 'ledger_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    wallet_id = db.Column(
        db.Integer, 
        db.ForeignKey('wallets.id', ondelete='CASCADE'), 
        nullable=False,
        index=True
    )
    transaction_id = db.Column(
        db.Integer, 
        db.ForeignKey('transactions.id', ondelete='CASCADE'), 
        nullable=False,
        index=True
    )
    
    # Accounting fields
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    balance_before = db.Column(db.Numeric(12, 2), nullable=False)
    balance_after = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Currency information
    currency = db.Column(db.String(3), nullable=False, default='KES', index=True)
    fx_rate = db.Column(db.Numeric(10, 6), nullable=True)
    fx_provider = db.Column(db.String(50), nullable=True)
    
    # Entry type and purpose
    entry_type = db.Column(db.String(10), nullable=False)  # 'debit' or 'credit'
    entry_subtype = db.Column(db.String(20), nullable=True)  # 'transfer', 'fee', 'refund', 'reversal'
    
    # Sequence for deterministic ordering
    sequence_number = db.Column(db.Integer, nullable=False)
    
    # Description and metadata
    description = db.Column(db.Text, nullable=True)
    meta_data = db.Column(JSONB, nullable=True)  # Additional context
    
    # Timestamps (immutable after creation)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_ledger_wallet_transaction', 'wallet_id', 'transaction_id'),
        db.Index('idx_ledger_created_at', 'created_at'),
        db.Index('idx_ledger_entry_type', 'entry_type'),
        db.Index('idx_ledger_currency', 'currency'),
        db.Index('idx_ledger_sequence', 'wallet_id', 'sequence_number', unique=True),
        db.Index('idx_ledger_wallet_date', 'wallet_id', 'created_at'),
        db.CheckConstraint("entry_type IN ('debit', 'credit')", name='check_entry_type'),
        db.CheckConstraint('balance_after = balance_before + amount', name='check_balance_calculation'),
    )
    
    @classmethod
    def get_next_sequence_number(cls, wallet_id):
        """Get next sequence number for wallet"""
        last_entry = cls.query.filter_by(wallet_id=wallet_id)\
            .order_by(cls.sequence_number.desc())\
            .first()
        
        return (last_entry.sequence_number + 1) if last_entry else 1
    
    @classmethod
    def create_entries(cls, transaction):
        """Create ledger entries for a transaction"""
        from .wallet import Wallet
        
        if not transaction.sender_wallet_id and not transaction.receiver_wallet_id:
            return []
        
        entries = []
        now = datetime.now(timezone.utc)
        
        # For sender (debit - amount leaves wallet)
        if transaction.sender_wallet_id and transaction.sender_wallet:
            sender_wallet = transaction.sender_wallet
            sequence_number = cls.get_next_sequence_number(sender_wallet.id)
            
            # Calculate total debit (amount + fee)
            total_debit = Decimal(str(transaction.amount)) + Decimal(str(transaction.fee))
            debit_amount = -total_debit  # Negative for debit
            
            # Create debit entry for principal
            principal_entry = cls(
                wallet_id=transaction.sender_wallet_id,
                transaction_id=transaction.id,
                amount=debit_amount,
                balance_before=sender_wallet.balance,
                balance_after=sender_wallet.balance + debit_amount,
                currency=transaction.source_currency,
                fx_rate=transaction.fx_rate,
                fx_provider=transaction.fx_provider,
                entry_type='debit',
                entry_subtype='transfer',
                sequence_number=sequence_number,
                description=f"Transfer to {transaction.external_receiver or f'wallet {transaction.receiver_wallet_id}'}",
                metadata={
                    'source_country': transaction.source_country,
                    'destination_country': transaction.destination_country,
                    'is_cross_border': transaction.is_cross_border,
                    'channel': transaction.channel
                }
            )
            entries.append(principal_entry)
            
            # Create separate fee entry if fee exists
            if transaction.fee > 0:
                fee_sequence = sequence_number + 1
                fee_entry = cls(
                    wallet_id=transaction.sender_wallet_id,
                    transaction_id=transaction.id,
                    amount=-Decimal(str(transaction.fee)),  # Negative for debit
                    balance_before=principal_entry.balance_after,
                    balance_after=principal_entry.balance_after - Decimal(str(transaction.fee)),
                    currency=transaction.source_currency,
                    entry_type='debit',
                    entry_subtype='fee',
                    sequence_number=fee_sequence,
                    description=f"Transaction fee for transfer {transaction.reference}",
                    metadata={
                        'fee_type': 'transfer_fee',
                        'is_cross_border': transaction.is_cross_border
                    }
                )
                entries.append(fee_entry)
                
                # Update wallet balances
                sender_wallet.balance = fee_entry.balance_after
                sender_wallet.available_balance = fee_entry.balance_after - sender_wallet.locked_balance
                sender_wallet.ledger_version = fee_sequence
            else:
                # Update wallet balances without fee
                sender_wallet.balance = principal_entry.balance_after
                sender_wallet.available_balance = principal_entry.balance_after - sender_wallet.locked_balance
                sender_wallet.ledger_version = sequence_number
        
        # For receiver (credit - amount enters wallet)
        if transaction.receiver_wallet_id and transaction.receiver_wallet:
            receiver_wallet = transaction.receiver_wallet
            sequence_number = cls.get_next_sequence_number(receiver_wallet.id)
            credit_amount = Decimal(str(transaction.net_amount))
            
            entry = cls(
                wallet_id=transaction.receiver_wallet_id,
                transaction_id=transaction.id,
                amount=credit_amount,
                balance_before=receiver_wallet.balance,
                balance_after=receiver_wallet.balance + credit_amount,
                currency=transaction.target_currency,
                fx_rate=transaction.fx_rate,
                fx_provider=transaction.fx_provider,
                entry_type='credit',
                entry_subtype='transfer',
                sequence_number=sequence_number,
                description=f"Transfer from {transaction.external_sender or f'wallet {transaction.sender_wallet_id}'}",
                metadata={
                    'source_country': transaction.source_country,
                    'destination_country': transaction.destination_country,
                    'is_cross_border': transaction.is_cross_border,
                    'channel': transaction.channel
                }
            )
            entries.append(entry)
            
            # Update wallet balance
            receiver_wallet.balance = entry.balance_after
            receiver_wallet.available_balance = entry.balance_after - receiver_wallet.locked_balance
            receiver_wallet.ledger_version = sequence_number
        
        # Record usage for limit tracking
        if transaction.sender_wallet:
            transaction.sender_wallet.record_usage(
                Decimal(str(transaction.amount)) + Decimal(str(transaction.fee)),
                transaction.is_cross_border
            )
        
        return entries
    
    @classmethod
    def get_wallet_usage(cls, wallet_id, start_date, end_date, is_cross_border=False):
        """Calculate wallet usage for a period"""
        query = cls.query.filter(
            cls.wallet_id == wallet_id,
            cls.created_at >= start_date,
            cls.created_at <= end_date,
            cls.entry_type == 'debit'
        )
        
        if is_cross_border:
            query = query.filter(cls.metadata['is_cross_border'].astext.cast(db.Boolean) == True)
        
        total_debit = query.with_entities(db.func.sum(-cls.amount)).scalar() or Decimal('0.00')
        
        return total_debit.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def to_dict(self):
        return {
            'id': self.id,
            'wallet_id': self.wallet_id,
            'transaction_id': self.transaction_id,
            'amount': float(self.amount),
            'balance_before': float(self.balance_before),
            'balance_after': float(self.balance_after),
            'currency': self.currency,
            'fx_rate': float(self.fx_rate) if self.fx_rate else None,
            'fx_provider': self.fx_provider,
            'entry_type': self.entry_type,
            'entry_subtype': self.entry_subtype,
            'sequence_number': self.sequence_number,
            'description': self.description,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<LedgerEntry wallet_id={self.wallet_id} amount={self.amount} type={self.entry_type} seq={self.sequence_number}>'
from datetime import datetime, timezone
from decimal import Decimal
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
    
    # Entry type: 'debit' for outgoing, 'credit' for incoming
    entry_type = db.Column(db.String(10), nullable=False)  # 'debit' or 'credit'
    
    # Description
    description = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_ledger_wallet_transaction', 'wallet_id', 'transaction_id'),
        db.Index('idx_ledger_created_at', 'created_at'),
        db.Index('idx_ledger_entry_type', 'entry_type'),
        db.CheckConstraint("entry_type IN ('debit', 'credit')", name='check_entry_type'),
        db.CheckConstraint('balance_after = balance_before + amount', name='check_balance_calculation'),
    )
    
    @classmethod
    def create_entries(cls, transaction):
        from .wallet import Wallet
        
        if not transaction.sender_wallet_id and not transaction.receiver_wallet_id:
            return None, None
        
        entries = []
        
        # For sender (debit - amount leaves wallet)
        if transaction.sender_wallet_id and transaction.sender_wallet:
            sender_wallet = transaction.sender_wallet
            debit_amount = -Decimal(str(transaction.amount)) - Decimal(str(transaction.fee))  
            
            entry = cls(
                wallet_id=transaction.sender_wallet_id,
                transaction_id=transaction.id,
                amount=debit_amount,
                balance_before=sender_wallet.balance,
                balance_after=sender_wallet.balance + debit_amount,
                entry_type='debit',
                description=f"Transfer to {transaction.external_receiver or f'wallet {transaction.receiver_wallet_id}'}"
            )
            entries.append(entry)
            
            # Update wallet balance
            sender_wallet.balance = entry.balance_after
            sender_wallet.available_balance = entry.balance_after - sender_wallet.locked_balance
        
        # For receiver (credit - amount enters wallet)
        if transaction.receiver_wallet_id and transaction.receiver_wallet:
            receiver_wallet = transaction.receiver_wallet
            credit_amount = Decimal(str(transaction.net_amount))
            
            entry = cls(
                wallet_id=transaction.receiver_wallet_id,
                transaction_id=transaction.id,
                amount=credit_amount,
                balance_before=receiver_wallet.balance,
                balance_after=receiver_wallet.balance + credit_amount,
                entry_type='credit',
                description=f"Transfer from {transaction.external_sender or f'wallet {transaction.sender_wallet_id}'}"
            )
            entries.append(entry)
            
            # Update wallet balance
            receiver_wallet.balance = entry.balance_after
            receiver_wallet.available_balance = entry.balance_after - receiver_wallet.locked_balance
        
        return entries
    
    def to_dict(self):
        return {
            'id': self.id,
            'wallet_id': self.wallet_id,
            'transaction_id': self.transaction_id,
            'amount': float(self.amount),
            'balance_before': float(self.balance_before),
            'balance_after': float(self.balance_after),
            'entry_type': self.entry_type,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<LedgerEntry wallet_id={self.wallet_id} amount={self.amount} type={self.entry_type}>'
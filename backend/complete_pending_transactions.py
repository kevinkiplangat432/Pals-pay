#!/usr/bin/env python3
"""
Manually complete pending M-Pesa transactions for testing
"""

from app import create_app, db
from app.models import Transaction, Wallet
from app.models.enums import TransactionStatus
from decimal import Decimal

app = create_app()

with app.app_context():
    # Get all pending deposit transactions
    pending = Transaction.query.filter_by(
        status=TransactionStatus.pending,
        transaction_type='deposit'
    ).all()
    
    print(f"Found {len(pending)} pending deposit transactions\n")
    
    for txn in pending:
        print(f"Transaction ID: {txn.id}")
        print(f"Amount: {txn.amount} KES")
        print(f"Receiver Wallet ID: {txn.receiver_wallet_id}")
        print(f"Created: {txn.created_at}")
        
        # Ask for confirmation
        response = input(f"\nComplete this transaction? (y/n): ")
        
        if response.lower() == 'y':
            try:
                # Update transaction status
                txn.status = TransactionStatus.completed
                txn.external_reference = 'TEST_MANUAL_COMPLETION'
                
                if txn.meta_data:
                    txn.meta_data['manually_completed'] = True
                else:
                    txn.meta_data = {'manually_completed': True}
                
                # Credit the wallet
                wallet = Wallet.query.get(txn.receiver_wallet_id)
                if wallet:
                    old_balance = wallet.balance
                    wallet.balance += txn.net_amount
                    wallet.available_balance += txn.net_amount
                    
                    db.session.commit()
                    
                    print(f"✅ Transaction completed!")
                    print(f"   Old balance: {old_balance} KES")
                    print(f"   New balance: {wallet.balance} KES")
                    print(f"   Added: {txn.net_amount} KES\n")
                else:
                    print(f"❌ Wallet not found!\n")
                    db.session.rollback()
            except Exception as e:
                print(f"❌ Error: {e}\n")
                db.session.rollback()
        else:
            print("Skipped\n")
    
    if not pending:
        print("No pending transactions found.")
        print("\nChecking recent transactions:")
        recent = Transaction.query.order_by(Transaction.created_at.desc()).limit(3).all()
        for txn in recent:
            print(f"  ID: {txn.id}, Amount: {txn.amount}, Status: {txn.status.value}, Type: {txn.transaction_type.value}")

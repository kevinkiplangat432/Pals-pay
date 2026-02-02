from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import and_, func
import uuid
from backend.app.extensions import db
from app.models import Transaction, Wallet, LedgerEntry, User, Beneficiary, AuditLog
from app.models.enums import TransactionStatus, TransactionType, PaymentProvider

class TransactionService:
    
    @staticmethod
    def create_transfer(sender_user_id, receiver_wallet_id, amount, description=None):
        """
        Create a transfer between wallets
        """
        from app.services.wallet_service import WalletService
        
        sender_wallet = Wallet.query.filter_by(user_id=sender_user_id).first()
        if not sender_wallet:
            return {'success': False, 'message': 'Sender wallet not found'}
        
        receiver_wallet = Wallet.query.get(receiver_wallet_id)
        if not receiver_wallet:
            return {'success': False, 'message': 'Receiver wallet not found'}
        
        # Check if sender is trying to send to themselves
        if sender_wallet.id == receiver_wallet.id:
            return {'success': False, 'message': 'Cannot send to yourself'}
        
        # Validate amount
        try:
            amount = Decimal(str(amount))
            if amount <= 0:
                return {'success': False, 'message': 'Amount must be positive'}
        except:
            return {'success': False, 'message': 'Invalid amount'}
        
        # Check sender permissions
        permission_check = sender_wallet.user.can_transact(amount)
        if not permission_check['allowed']:
            return {'success': False, 'message': permission_check['reason']}
        
        # Check wallet limits
        wallet_check = sender_wallet.can_withdraw(amount)
        if not wallet_check['allowed']:
            return {'success': False, 'message': wallet_check['reason']}
        
        # Calculate fee
        fee = Transaction.calculate_fee(amount, 'transfer')
        total_debit = amount + fee
        
        # Check beneficiary limits if exists
        beneficiary = Beneficiary.query.filter_by(
            user_id=sender_user_id,
            beneficiary_wallet_id=receiver_wallet_id
        ).first()
        
        if beneficiary:
            beneficiary_check = beneficiary.can_send(amount)
            if not beneficiary_check['allowed']:
                return {'success': False, 'message': beneficiary_check['reason']}
        
        try:
            with db.session.begin_nested():
                # Create transaction
                transaction = Transaction(
                    sender_wallet_id=sender_wallet.id,
                    receiver_wallet_id=receiver_wallet.id,
                    amount=amount,
                    fee=fee,
                    net_amount=amount,
                    transaction_type=TransactionType.transfer,
                    status=TransactionStatus.pending,
                    provider=PaymentProvider.internal,
                    description=description or f"Transfer to {receiver_wallet.user.get_full_name()}"
                )
                
                db.session.add(transaction)
                db.session.flush()
                
                # Create ledger entries
                entries = LedgerEntry.create_entries(transaction)
                for entry in entries:
                    db.session.add(entry)
                
                # Update beneficiary statistics if exists
                if beneficiary:
                    beneficiary.update_statistics(amount)
                
                # Update wallet last transaction timestamp
                sender_wallet.last_transaction_at = datetime.utcnow()
                receiver_wallet.last_transaction_at = datetime.utcnow()
                
                # Update transaction status
                transaction.update_status(TransactionStatus.completed)
                
                # Log the action
                AuditLog.log_user_action(
                    actor_id=sender_user_id,
                    action='transfer.create',
                    resource_type='transaction',
                    resource_id=transaction.id,
                    new_values={'amount': float(amount), 'fee': float(fee)},
                    status='success'
                )
            
            db.session.commit()
            
            return {
                'success': True,
                'transaction': transaction.to_dict(),
                'message': 'Transfer completed successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Transfer failed: {str(e)}'}
    
    @staticmethod
    def get_user_transactions(user_id, page=1, per_page=20, transaction_type=None):
        """
        Get paginated transactions for a user
        """
        user_wallet = Wallet.query.filter_by(user_id=user_id).first()
        if not user_wallet:
            return {'transactions': [], 'total': 0, 'pages': 0}
        
        # Get transactions where user is sender or receiver
        query = Transaction.query.filter(
            (Transaction.sender_wallet_id == user_wallet.id) |
            (Transaction.receiver_wallet_id == user_wallet.id)
        )
        
        if transaction_type:
            query = query.filter_by(transaction_type=transaction_type)
        
        query = query.order_by(Transaction.created_at.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'transactions': [tx.to_dict() for tx in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }
    
    @staticmethod
    def process_mpesa_deposit(user_id, amount, phone_number, mpesa_receipt):
        """
        Process MPesa deposit using Daraja API callback
        """
        user_wallet = Wallet.query.filter_by(user_id=user_id).first()
        if not user_wallet:
            return {'success': False, 'message': 'Wallet not found'}
        
        try:
            amount = Decimal(str(amount))
            
            with db.session.begin_nested():
                # Create deposit transaction
                transaction = Transaction(
                    sender_wallet_id=None,
                    receiver_wallet_id=user_wallet.id,
                    external_sender=phone_number,
                    amount=amount,
                    fee=Decimal('0.00'),
                    net_amount=amount,
                    transaction_type=TransactionType.deposit,
                    status=TransactionStatus.completed,
                    provider=PaymentProvider.mpesa,
                    external_reference=mpesa_receipt,
                    description=f"MPesa deposit from {phone_number}"
                )
                
                db.session.add(transaction)
                db.session.flush()
                
                # Create ledger entry for receiver
                ledger_entry = LedgerEntry(
                    wallet_id=user_wallet.id,
                    transaction_id=transaction.id,
                    amount=amount,
                    balance_before=user_wallet.balance,
                    balance_after=user_wallet.balance + amount,
                    entry_type='credit',
                    description=f"MPesa deposit from {phone_number}"
                )
                
                db.session.add(ledger_entry)
                
                # Update wallet balance
                user_wallet.balance += amount
                user_wallet.available_balance += amount
                user_wallet.last_transaction_at = datetime.utcnow()
                
                # Log the action
                AuditLog.log_system_action(
                    action='deposit.mpesa',
                    resource_type='transaction',
                    resource_id=transaction.id,
                    new_values={'amount': float(amount), 'phone': phone_number},
                    status='success'
                )
            
            db.session.commit()
            
            return {
                'success': True,
                'transaction': transaction.to_dict(),
                'message': 'Deposit processed successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Deposit failed: {str(e)}'}
    
    @staticmethod
    def get_transaction_summary(user_id, days=30):
        """
        Get transaction summary for a user
        """
        user_wallet = Wallet.query.filter_by(user_id=user_id).first()
        if not user_wallet:
            return {}
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get sent transactions
        sent_query = Transaction.query.filter(
            Transaction.sender_wallet_id == user_wallet.id,
            Transaction.status == TransactionStatus.completed,
            Transaction.created_at >= start_date
        )
        
        # Get received transactions
        received_query = Transaction.query.filter(
            Transaction.receiver_wallet_id == user_wallet.id,
            Transaction.status == TransactionStatus.completed,
            Transaction.created_at >= start_date
        )
        
        total_sent = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.sender_wallet_id == user_wallet.id,
            Transaction.status == TransactionStatus.completed,
            Transaction.created_at >= start_date
        ).scalar() or Decimal('0.00')
        
        total_received = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.receiver_wallet_id == user_wallet.id,
            Transaction.status == TransactionStatus.completed,
            Transaction.created_at >= start_date
        ).scalar() or Decimal('0.00')
        
        total_fees = db.session.query(func.sum(Transaction.fee)).filter(
            Transaction.sender_wallet_id == user_wallet.id,
            Transaction.status == TransactionStatus.completed,
            Transaction.created_at >= start_date
        ).scalar() or Decimal('0.00')
        
        return {
            'sent_count': sent_query.count(),
            'received_count': received_query.count(),
            'total_sent': float(total_sent),
            'total_received': float(total_received),
            'total_fees': float(total_fees),
            'period_days': days
        }
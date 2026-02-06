from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import and_, func
import uuid
from ..extensions import db
from app.models import Transaction, Wallet, LedgerEntry, User, Beneficiary, AuditLog
from app.models.enums import TransactionStatus, TransactionType, PaymentProvider
from app.services.currency_service import CurrencyService
from app.services.compliance_service import ComplianceService

class TransactionService:
    
    @staticmethod
    def create_transfer(sender_user_id, receiver_wallet_id, amount, currency='KES', description=None):
        """Create a transfer with currency support"""
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
        
        # Check cross-border compliance
        if sender_wallet.user.country_code != receiver_wallet.user.country_code:
            compliance_check = ComplianceService.check_cross_border_transfer(
                sender_wallet.user.country_code,
                receiver_wallet.user.country_code,
                amount
            )
            if not compliance_check['allowed']:
                return {'success': False, 'message': compliance_check['reason']}
        
        # Check sender permissions
        permission_check = sender_wallet.user.can_transact(amount, receiver_wallet.user.country_code)
        if not permission_check['allowed']:
            return {'success': False, 'message': permission_check['reason']}
        
        # Convert amount to sender's currency if needed
        if currency != sender_wallet.primary_currency:
            amount_in_sender_currency = CurrencyService.convert_amount(
                amount, currency, sender_wallet.primary_currency
            )
        else:
            amount_in_sender_currency = amount
        
        # Check wallet limits
        wallet_check = sender_wallet.can_withdraw(
            amount_in_sender_currency, 
            sender_wallet.primary_currency,
            receiver_wallet.user.country_code
        )
        if not wallet_check['allowed']:
            return {'success': False, 'message': wallet_check['reason']}
        
        # Calculate fee based on transfer type
        is_cross_border = sender_wallet.user.country_code != receiver_wallet.user.country_code
        is_cross_region = sender_wallet.user.region != receiver_wallet.user.region
        
        fee = TransactionService.calculate_fee(
            amount_in_sender_currency, 
            'transfer',
            is_cross_border=is_cross_border,
            is_cross_region=is_cross_region
        )
        
        total_debit = amount_in_sender_currency + fee
        
        # Convert to receiver's currency for credit
        if sender_wallet.primary_currency != receiver_wallet.primary_currency:
            amount_in_receiver_currency = CurrencyService.convert_amount(
                amount, currency, receiver_wallet.primary_currency
            )
        else:
            amount_in_receiver_currency = amount
        
        try:
            with db.session.begin_nested():
                # Create transaction with currency information
                transaction = Transaction(
                    sender_wallet_id=sender_wallet.id,
                    receiver_wallet_id=receiver_wallet.id,
                    amount=amount_in_sender_currency,
                    fee=fee,
                    net_amount=amount_in_sender_currency,
                    sender_currency=sender_wallet.primary_currency,
                    receiver_currency=receiver_wallet.primary_currency,
                    exchange_rate=CurrencyService.get_exchange_rate(
                        sender_wallet.primary_currency, 
                        receiver_wallet.primary_currency
                    ),
                    transaction_type=TransactionType.transfer,
                    status=TransactionStatus.pending,
                    provider=PaymentProvider.internal,
                    description=description or f"Transfer to {receiver_wallet.user.get_full_name()}",
                    metadata={
                        'is_cross_border': is_cross_border,
                        'is_cross_region': is_cross_region,
                        'sender_country': sender_wallet.user.country_code,
                        'receiver_country': receiver_wallet.user.country_code
                    }
                )
                
                db.session.add(transaction)
                db.session.flush()
                
                # Create ledger entries with currency conversion
                from app.models import LedgerEntry
                
                # Sender entry (debit)
                sender_entry = LedgerEntry(
                    wallet_id=sender_wallet.id,
                    transaction_id=transaction.id,
                    amount=-total_debit,
                    balance_before=sender_wallet.balance,
                    balance_after=sender_wallet.balance - total_debit,
                    currency=sender_wallet.primary_currency,
                    entry_type='debit',
                    description=f"Transfer to {receiver_wallet.user.get_full_name()} ({receiver_wallet.user.country_code})"
                )
                db.session.add(sender_entry)
                
                # Update sender wallet
                sender_wallet.balance -= total_debit
                sender_wallet.available_balance -= total_debit
                sender_wallet.last_transaction_at = datetime.utcnow()
                
                # Receiver entry (credit)
                receiver_entry = LedgerEntry(
                    wallet_id=receiver_wallet.id,
                    transaction_id=transaction.id,
                    amount=amount_in_receiver_currency,
                    balance_before=receiver_wallet.balance,
                    balance_after=receiver_wallet.balance + amount_in_receiver_currency,
                    currency=receiver_wallet.primary_currency,
                    entry_type='credit',
                    description=f"Transfer from {sender_wallet.user.get_full_name()} ({sender_wallet.user.country_code})"
                )
                db.session.add(receiver_entry)
                
                # Update receiver wallet
                receiver_wallet.balance += amount_in_receiver_currency
                receiver_wallet.available_balance += amount_in_receiver_currency
                receiver_wallet.last_transaction_at = datetime.utcnow()
                
                # Update transaction status
                transaction.update_status(TransactionStatus.completed)
                
                # Log the action
                AuditLog.log_user_action(
                    actor_id=sender_user_id,
                    action='transfer.create',
                    resource_type='transaction',
                    resource_id=transaction.id,
                    new_values={
                        'amount': float(amount_in_sender_currency),
                        'fee': float(fee),
                        'sender_currency': sender_wallet.primary_currency,
                        'receiver_currency': receiver_wallet.primary_currency,
                        'is_cross_border': is_cross_border
                    },
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
    def calculate_fee(amount, transaction_type='transfer', is_cross_border=False, is_cross_region=False):
        """Calculate fees with international support"""
        from flask import current_app
        
        amount = Decimal(str(amount))
        fee_structure = current_app.config['FEE_STRUCTURE']
        
        if is_cross_border:
            # International transfer fee
            fee_config = fee_structure.get('international', {})
        elif is_cross_region:
            # Cross-region transfer fee
            fee_config = fee_structure.get('cross_region', {})
        else:
            # Local transfer fee
            fee_config = fee_structure.get('local_transfer', {}).get('default', {})
        
        # Calculate percentage fee
        percentage_fee = amount * fee_config.get('percentage', Decimal('0.01'))
        
        # Add fixed fee
        fixed_fee = fee_config.get('fixed', Decimal('10.00'))
        total_fee = percentage_fee + fixed_fee
        
        # Apply minimum and maximum fees
        min_fee = fee_config.get('min_fee', Decimal('0.00'))
        max_fee = fee_config.get('max_fee', Decimal('5000.00'))
        
        total_fee = max(total_fee, min_fee)
        total_fee = min(total_fee, max_fee)
        
        return total_fee.quantize(Decimal('0.01'))

    
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
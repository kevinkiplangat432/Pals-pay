from decimal import Decimal
from datetime import datetime, timezone
import uuid
from flask import current_app

from ..extensions import db
from ..models import Transaction, Wallet, Beneficiary, User, ExchangeRate, Fee, Hold, AuditLog
from ..models.enums import TransactionStatus, TransactionType, PaymentProvider
from .currency_service import CurrencyService
from .compliance_service import ComplianceService
from .otp_services import OTPService
from .notification_service import NotificationService

class TransferService:
    
    @staticmethod
    def get_local_transfer_quote(sender_wallet_id, amount, currency='KES', receiver_wallet_id=None, receiver_phone=None):
        sender_wallet = Wallet.query.get(sender_wallet_id)
        if not sender_wallet:
            return {'success': False, 'message': 'Sender wallet not found'}
        
        if receiver_wallet_id:
            receiver_wallet = Wallet.query.get(receiver_wallet_id)
            if not receiver_wallet:
                return {'success': False, 'message': 'Receiver wallet not found'}
        elif receiver_phone:
            user = User.query.filter_by(phone_number=receiver_phone, is_active=True).first()
            if not user:
                return {'success': False, 'message': 'Receiver not found'}
            receiver_wallet = Wallet.query.filter_by(user_id=user.id).first()
            if not receiver_wallet:
                return {'success': False, 'message': 'Receiver wallet not found'}
        else:
            return {'success': False, 'message': 'Receiver not specified'}
        
        try:
            amount_decimal = Decimal(str(amount))
            if amount_decimal <= 0:
                return {'success': False, 'message': 'Amount must be positive'}
        except:
            return {'success': False, 'message': 'Invalid amount'}
        
        if amount_decimal > Decimal('250000'):
            return {'success': False, 'message': 'Amount exceeds per-transaction limit (250,000 KES)'}
        
        if sender_wallet.primary_currency != currency:
            converted_amount = CurrencyService.convert_amount(amount_decimal, currency, sender_wallet.primary_currency)
        else:
            converted_amount = amount_decimal
        
        check_result = sender_wallet.can_withdraw(converted_amount, sender_wallet.primary_currency)
        if not check_result['allowed']:
            return {'success': False, 'message': check_result['reason']}
        
        is_cross_border = sender_wallet.user.country_code != receiver_wallet.user.country_code
        
        if is_cross_border:
            cross_border_check = ComplianceService.check_cross_border_transfer(
                sender_country=sender_wallet.user.country_code,
                receiver_country=receiver_wallet.user.country_code,
                amount=converted_amount
            )
            if not cross_border_check['allowed']:
                return {'success': False, 'message': cross_border_check['reason']}
        
        fee = TransferService.calculate_transfer_fee(
            amount=converted_amount,
            is_cross_border=is_cross_border,
            is_cross_region=sender_wallet.user.region != receiver_wallet.user.region
        )
        
        total_amount = converted_amount + fee
        
        if sender_wallet.available_balance < total_amount:
            return {'success': False, 'message': 'Insufficient balance to cover amount and fee'}
        
        exchange_rate = None
        receiver_amount = amount_decimal
        
        if sender_wallet.primary_currency != receiver_wallet.primary_currency:
            exchange_rate = CurrencyService.get_exchange_rate(
                sender_wallet.primary_currency,
                receiver_wallet.primary_currency
            )
            receiver_amount = converted_amount * exchange_rate
        
        return {
            'success': True,
            'quote_id': str(uuid.uuid4()),
            'amount': float(amount_decimal),
            'currency': currency,
            'converted_amount': float(converted_amount),
            'sender_currency': sender_wallet.primary_currency,
            'receiver_amount': float(receiver_amount),
            'receiver_currency': receiver_wallet.primary_currency,
            'fee': float(fee),
            'total_amount': float(total_amount),
            'exchange_rate': float(exchange_rate) if exchange_rate else None,
            'is_cross_border': is_cross_border,
            'estimated_settlement': 'Instant',
            'expires_at': (datetime.now(timezone.utc) + current_app.config['QUOTE_EXPIRY']).isoformat()
        }
    
    @staticmethod
    def initiate_local_transfer(sender_user_id, amount, currency='KES', receiver_wallet_id=None, receiver_phone=None, description=None):
        sender_wallet = Wallet.query.filter_by(user_id=sender_user_id).first()
        if not sender_wallet:
            return {'success': False, 'message': 'Sender wallet not found'}
        
        if receiver_wallet_id:
            receiver_wallet = Wallet.query.get(receiver_wallet_id)
            if not receiver_wallet:
                return {'success': False, 'message': 'Receiver wallet not found'}
        elif receiver_phone:
            user = User.query.filter_by(phone_number=receiver_phone, is_active=True).first()
            if not user:
                return {'success': False, 'message': 'Receiver not found'}
            receiver_wallet = Wallet.query.filter_by(user_id=user.id).first()
            if not receiver_wallet:
                return {'success': False, 'message': 'Receiver wallet not found'}
        else:
            return {'success': False, 'message': 'Receiver not specified'}
        
        try:
            amount_decimal = Decimal(str(amount))
            if amount_decimal <= 0:
                return {'success': False, 'message': 'Amount must be positive'}
        except:
            return {'success': False, 'message': 'Invalid amount'}
        
        if sender_wallet.primary_currency != currency:
            converted_amount = CurrencyService.convert_amount(amount_decimal, currency, sender_wallet.primary_currency)
        else:
            converted_amount = amount_decimal
        
        check_result = sender_wallet.can_withdraw(converted_amount, sender_wallet.primary_currency, receiver_wallet.user.country_code)
        if not check_result['allowed']:
            return {'success': False, 'message': check_result['reason']}
        
        is_cross_border = sender_wallet.user.country_code != receiver_wallet.user.country_code
        
        if is_cross_border:
            cross_border_check = ComplianceService.check_cross_border_transfer(
                sender_country=sender_wallet.user.country_code,
                receiver_country=receiver_wallet.user.country_code,
                amount=converted_amount
            )
            if not cross_border_check['allowed']:
                return {'success': False, 'message': cross_border_check['reason']}
        
        fee = TransferService.calculate_transfer_fee(
            amount=converted_amount,
            is_cross_border=is_cross_border,
            is_cross_region=sender_wallet.user.region != receiver_wallet.user.region
        )
        
        total_amount = converted_amount + fee
        
        if sender_wallet.available_balance < total_amount:
            return {'success': False, 'message': 'Insufficient balance to cover amount and fee'}
        
        try:
            with db.session.begin_nested():
                if not sender_wallet.lock_funds(total_amount, sender_wallet.primary_currency):
                    return {'success': False, 'message': 'Failed to lock funds'}
                
                exchange_rate = None
                receiver_amount = amount_decimal
                
                if sender_wallet.primary_currency != receiver_wallet.primary_currency:
                    exchange_rate_record = ExchangeRate.query.filter_by(
                        base_currency=sender_wallet.primary_currency,
                        target_currency=receiver_wallet.primary_currency
                    ).first()
                    
                    if not exchange_rate_record:
                        exchange_rate_record = CurrencyService.update_exchange_rate(
                            sender_wallet.primary_currency,
                            receiver_wallet.primary_currency
                        )
                    
                    exchange_rate = exchange_rate_record.rate
                    receiver_amount = converted_amount * exchange_rate
                
                transaction = Transaction(
                    sender_wallet_id=sender_wallet.id,
                    receiver_wallet_id=receiver_wallet.id,
                    amount=converted_amount,
                    fee=fee,
                    net_amount=converted_amount,
                    source_currency=sender_wallet.primary_currency,
                    target_currency=receiver_wallet.primary_currency,
                    fx_rate=exchange_rate,
                    fx_provider='internal',
                    fx_timestamp=datetime.now(timezone.utc) if exchange_rate else None,
                    source_country=sender_wallet.user.country_code,
                    destination_country=receiver_wallet.user.country_code,
                    is_cross_border=is_cross_border,
                    transaction_type=TransactionType.transfer,
                    status=TransactionStatus.processing,
                    provider=PaymentProvider.internal,
                    description=description or f"Transfer to {receiver_wallet.user.get_full_name()}",
                    metadata={
                        'sender_ip': '',
                        'sender_device': '',
                        'is_cross_border': is_cross_border,
                        'fx_rate_snapshot': float(exchange_rate) if exchange_rate else None
                    }
                )
                
                db.session.add(transaction)
                db.session.flush()
                
                from ..models import LedgerEntry
                sender_sequence = LedgerEntry.get_next_sequence_number(sender_wallet.id)
                
                sender_entry = LedgerEntry(
                    wallet_id=sender_wallet.id,
                    transaction_id=transaction.id,
                    amount=-total_amount,
                    balance_before=sender_wallet.balance,
                    balance_after=sender_wallet.balance - total_amount,
                    currency=sender_wallet.primary_currency,
                    fx_rate=exchange_rate,
                    fx_provider='internal',
                    entry_type='debit',
                    entry_subtype='transfer',
                    sequence_number=sender_sequence,
                    description=f"Transfer to {receiver_wallet.user.get_full_name()}",
                    metadata={
                        'is_cross_border': is_cross_border,
                        'receiver_country': receiver_wallet.user.country_code
                    }
                )
                db.session.add(sender_entry)
                
                sender_wallet.balance = sender_entry.balance_after
                sender_wallet.locked_balance -= total_amount
                sender_wallet.last_transaction_at = datetime.now(timezone.utc)
                
                receiver_sequence = LedgerEntry.get_next_sequence_number(receiver_wallet.id)
                
                receiver_entry = LedgerEntry(
                    wallet_id=receiver_wallet.id,
                    transaction_id=transaction.id,
                    amount=receiver_amount,
                    balance_before=receiver_wallet.balance,
                    balance_after=receiver_wallet.balance + receiver_amount,
                    currency=receiver_wallet.primary_currency,
                    fx_rate=exchange_rate,
                    fx_provider='internal',
                    entry_type='credit',
                    entry_subtype='transfer',
                    sequence_number=receiver_sequence,
                    description=f"Transfer from {sender_wallet.user.get_full_name()}",
                    metadata={
                        'is_cross_border': is_cross_border,
                        'sender_country': sender_wallet.user.country_code
                    }
                )
                db.session.add(receiver_entry)
                
                receiver_wallet.balance = receiver_entry.balance_after
                receiver_wallet.available_balance = receiver_entry.balance_after - receiver_wallet.locked_balance
                receiver_wallet.last_transaction_at = datetime.now(timezone.utc)
                
                transaction.update_status(TransactionStatus.completed)
                
                if is_cross_border:
                    sender_wallet.record_usage(converted_amount, is_cross_border=True)
                else:
                    sender_wallet.record_usage(converted_amount, is_cross_border=False)
                
                AuditLog.log_user_action(
                    actor_id=sender_user_id,
                    action='transfer.completed',
                    resource_type='transaction',
                    resource_id=transaction.id,
                    metadata={
                        'amount': float(converted_amount),
                        'fee': float(fee),
                        'is_cross_border': is_cross_border,
                        'receiver_id': receiver_wallet.user_id
                    },
                    status='success'
                )
                
                NotificationService.send_transfer_notification(
                    sender_user_id=sender_user_id,
                    receiver_user_id=receiver_wallet.user_id,
                    amount=float(converted_amount),
                    currency=sender_wallet.primary_currency,
                    transaction_id=transaction.id,
                    is_cross_border=is_cross_border
                )
            
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Transfer completed successfully',
                'transaction_id': transaction.id,
                'reference': transaction.reference,
                'amount': float(converted_amount),
                'fee': float(fee),
                'total': float(total_amount),
                'new_balance': float(sender_wallet.balance),
                'receiver_amount': float(receiver_amount),
                'receiver_currency': receiver_wallet.primary_currency
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Transfer failed: {str(e)}'}
    
    @staticmethod
    def get_international_transfer_quote(sender_user_id, amount, source_currency, target_currency, destination_country, receiver_details):
        sender_wallet = Wallet.query.filter_by(user_id=sender_user_id).first()
        if not sender_wallet:
            return {'success': False, 'message': 'Sender wallet not found'}
        
        try:
            amount_decimal = Decimal(str(amount))
            if amount_decimal <= 0:
                return {'success': False, 'message': 'Amount must be positive'}
        except:
            return {'success': False, 'message': 'Invalid amount'}
        
        if source_currency != sender_wallet.primary_currency:
            converted_amount = CurrencyService.convert_amount(amount_decimal, source_currency, sender_wallet.primary_currency)
        else:
            converted_amount = amount_decimal
        
        if converted_amount > Decimal('250000'):
            return {'success': False, 'message': 'Amount exceeds per-transaction limit (250,000 KES equivalent)'}
        
        check_result = sender_wallet.can_withdraw(
            converted_amount, 
            sender_wallet.primary_currency,
            destination_country
        )
        if not check_result['allowed']:
            return {'success': False, 'message': check_result['reason']}
        
        compliance_check = ComplianceService.check_international_transfer(
            source_country=sender_wallet.user.country_code,
            destination_country=destination_country,
            amount=converted_amount,
            currency=sender_wallet.primary_currency
        )
        
        if not compliance_check['allowed']:
            return {'success': False, 'message': compliance_check['reason']}
        
        exchange_rate_record = ExchangeRate.query.filter_by(
            base_currency=source_currency,
            target_currency=target_currency
        ).first()
        
        if not exchange_rate_record:
            exchange_rate_record = CurrencyService.update_exchange_rate(source_currency, target_currency)
        
        exchange_rate = exchange_rate_record.rate
        
        target_amount = amount_decimal * exchange_rate
        
        fee = TransferService.calculate_international_fee(
            amount=converted_amount,
            source_country=sender_wallet.user.country_code,
            destination_country=destination_country,
            target_currency=target_currency
        )
        
        total_amount = converted_amount + fee
        
        if sender_wallet.available_balance < total_amount:
            return {'success': False, 'message': 'Insufficient balance to cover amount and fee'}
        
        estimated_settlement = TransferService.get_estimated_settlement_time(
            source_country=sender_wallet.user.country_code,
            destination_country=destination_country,
            target_currency=target_currency
        )
        
        return {
            'success': True,
            'quote_id': str(uuid.uuid4()),
            'amount': float(amount_decimal),
            'source_currency': source_currency,
            'target_amount': float(target_amount),
            'target_currency': target_currency,
            'exchange_rate': float(exchange_rate),
            'fx_provider': exchange_rate_record.fx_provider if hasattr(exchange_rate_record, 'fx_provider') else 'internal',
            'fx_timestamp': exchange_rate_record.last_updated.isoformat() if exchange_rate_record.last_updated else None,
            'fee': float(fee),
            'total_amount': float(total_amount),
            'source_country': sender_wallet.user.country_code,
            'destination_country': destination_country,
            'estimated_settlement': estimated_settlement,
            'compliance_required': compliance_check.get('compliance_required', []),
            'receiver_requirements': compliance_check.get('receiver_requirements', {}),
            'expires_at': (datetime.now(timezone.utc) + current_app.config['INTERNATIONAL_QUOTE_EXPIRY']).isoformat()
        }
    
    @staticmethod
    def initiate_international_transfer(sender_user_id, quote_id, receiver_details, funding_source_id=None, ip_address=None, user_agent=None):
        return {'success': False, 'message': 'International transfers coming soon'}
    
    @staticmethod
    def calculate_transfer_fee(amount, is_cross_border=False, is_cross_region=False):
        fee_config = current_app.config['FEE_STRUCTURE']
        
        if is_cross_border:
            fee_type = 'international'
        elif is_cross_region:
            fee_type = 'cross_region'
        else:
            fee_type = 'local_transfer'
        
        config = fee_config.get(fee_type, {})
        
        if isinstance(config, dict) and 'percentage' in config:
            percentage_fee = amount * (config['percentage'] / Decimal('100'))
            fixed_fee = config.get('fixed', Decimal('0'))
            fee = percentage_fee + fixed_fee
            
            min_fee = config.get('min_fee', Decimal('0'))
            max_fee = config.get('max_fee', Decimal('10000'))
            
            fee = max(fee, min_fee)
            fee = min(fee, max_fee)
        else:
            fee = Decimal('10.00')
        
        return fee.quantize(Decimal('0.01'))
    
    @staticmethod
    def calculate_international_fee(amount, source_country, destination_country, target_currency):
        fee_config = current_app.config['INTERNATIONAL_FEE_STRUCTURE']
        
        route_key = f"{source_country}_{destination_country}"
        
        if route_key in fee_config:
            config = fee_config[route_key]
        else:
            config = fee_config.get('default', {})
        
        percentage_fee = amount * (config.get('percentage', Decimal('5')) / Decimal('100'))
        fixed_fee = config.get('fixed', Decimal('500'))
        fee = percentage_fee + fixed_fee
        
        min_fee = config.get('min_fee', Decimal('1000'))
        max_fee = config.get('max_fee', Decimal('10000'))
        
        fee = max(fee, min_fee)
        fee = min(fee, max_fee)
        
        return fee.quantize(Decimal('0.01'))
    
    @staticmethod
    def get_estimated_settlement_time(source_country, destination_country, target_currency):
        settlement_times = current_app.config['SETTLEMENT_TIMES']
        
        route_key = f"{source_country}_{destination_country}"
        
        if route_key in settlement_times:
            return settlement_times[route_key]
        
        if source_country == destination_country:
            return 'Instant'
        
        region_pairs = current_app.config.get('SETTLEMENT_REGIONS', {})
        for region_pair, time in region_pairs.items():
            if source_country in region_pair.split('_')[0] and destination_country in region_pair.split('_')[1]:
                return time
        
        return '1-3 business days'
    
    @staticmethod
    def get_transfer_status(transaction_id):
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return {'success': False, 'message': 'Transaction not found'}
        
        return {
            'success': True,
            'transaction_id': transaction.id,
            'status': transaction.status.value,
            'amount': float(transaction.amount),
            'currency': transaction.source_currency,
            'fee': float(transaction.fee),
            'net_amount': float(transaction.net_amount),
            'reference': transaction.reference,
            'external_reference': transaction.external_reference,
            'created_at': transaction.created_at.isoformat() if transaction.created_at else None,
            'completed_at': transaction.completed_at.isoformat() if transaction.completed_at else None,
            'settlement_status': transaction.settlement_status,
            'settlement_date': transaction.settlement_date.isoformat() if transaction.settlement_date else None,
            'is_cross_border': transaction.is_cross_border,
            'source_country': transaction.source_country,
            'destination_country': transaction.destination_country
        }
    
    @staticmethod
    def cancel_transfer(transaction_id, cancelled_by):
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return {'success': False, 'message': 'Transaction not found'}
        
        if transaction.status != TransactionStatus.pending:
            return {'success': False, 'message': 'Only pending transactions can be cancelled'}
        
        try:
            with db.session.begin_nested():
                sender_wallet = transaction.sender_wallet
                if sender_wallet:
                    amount_to_unlock = transaction.amount + transaction.fee
                    sender_wallet.unlock_funds(amount_to_unlock, sender_wallet.primary_currency)
                
                transaction.update_status(TransactionStatus.failed)
                transaction.metadata = {
                    **transaction.metadata,
                    'cancelled_by': cancelled_by,
                    'cancelled_at': datetime.now(timezone.utc).isoformat(),
                    'cancellation_reason': 'User cancelled'
                }
                
                AuditLog.log_user_action(
                    actor_id=cancelled_by,
                    action='transfer.cancelled',
                    resource_type='transaction',
                    resource_id=transaction.id,
                    metadata={'transaction_id': transaction_id},
                    status='success'
                )
            
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Transfer cancelled successfully',
                'transaction_id': transaction_id,
                'amount_refunded': float(transaction.amount + transaction.fee)
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Failed to cancel transfer: {str(e)}'}
    
    @staticmethod
    def get_user_transfer_summary(user_id, days=30):
        wallet = Wallet.query.filter_by(user_id=user_id).first()
        if not wallet:
            return {'total_transfers': 0, 'total_amount': 0, 'total_fees': 0}
        
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        sent_query = db.session.query(
            func.count(Transaction.id),
            func.sum(Transaction.amount),
            func.sum(Transaction.fee)
        ).filter(
            Transaction.sender_wallet_id == wallet.id,
            Transaction.status == TransactionStatus.completed,
            Transaction.created_at >= start_date
        ).first()
        
        sent_count = sent_query[0] or 0
        sent_amount = sent_query[1] or Decimal('0')
        sent_fees = sent_query[2] or Decimal('0')
        
        received_query = db.session.query(
            func.count(Transaction.id),
            func.sum(Transaction.amount)
        ).filter(
            Transaction.receiver_wallet_id == wallet.id,
            Transaction.status == TransactionStatus.completed,
            Transaction.created_at >= start_date
        ).first()
        
        received_count = received_query[0] or 0
        received_amount = received_query[1] or Decimal('0')
        
        return {
            'period_days': days,
            'sent': {
                'count': sent_count,
                'amount': float(sent_amount),
                'fees': float(sent_fees)
            },
            'received': {
                'count': received_count,
                'amount': float(received_amount)
            },
            'total_transfers': sent_count + received_count,
            'total_amount': float(sent_amount + received_amount),
            'total_fees': float(sent_fees)
        }
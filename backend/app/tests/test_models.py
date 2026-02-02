import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from app.models import User, Wallet, Transaction, Beneficiary, KYCVerification, PaymentMethod, LedgerEntry, AuditLog
from app.models.enums import TransactionStatus, TransactionType, KYCStatus, WalletStatus, PaymentProvider, DocumentType

class TestUserModel:
    """Test User model"""
    
    def test_create_user(self, db_session):
        """Test creating a new user"""
        user = User(
            email='test@example.com',
            username='testuser',
            phone_number='+254700000000',
            first_name='Test',
            last_name='User'
        )
        user.set_password('password123')
        
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.public_id is not None
        assert user.check_password('password123')
        assert user.is_admin == False
        assert user.is_active == True
        assert user.wallet is not None  # Wallet created automatically
    
    def test_user_full_name(self, db_session):
        """Test user full name property"""
        user = User(
            email='test@example.com',
            username='testuser',
            phone_number='+254700000000',
            first_name='John',
            last_name='Doe'
        )
        
        assert user.get_full_name() == 'John Doe'
    
    def test_user_can_transact(self, db_session):
        """Test user transaction permissions"""
        user = User(
            email='test@example.com',
            username='testuser',
            phone_number='+254700000000',
            first_name='Test',
            last_name='User',
            kyc_status=KYCStatus.verified
        )
        user.set_password('password123')
        db_session.add(user)
        db_session.commit()
        
        # Active, verified user can transact
        result = user.can_transact()
        assert result['allowed'] == True
        
        # Inactive user cannot transact
        user.is_active = False
        result = user.can_transact()
        assert result['allowed'] == False
        
        # Unverified KYC cannot transact
        user.is_active = True
        user.kyc_status = KYCStatus.unverified
        result = user.can_transact()
        assert result['allowed'] == False

class TestWalletModel:
    """Test Wallet model"""
    
    def test_create_wallet(self, db_session, regular_user):
        """Test creating a wallet"""
        wallet = Wallet(
            user_id=regular_user.id,
            balance=Decimal('1000.00'),
            available_balance=Decimal('900.00'),
            locked_balance=Decimal('100.00')
        )
        
        db_session.add(wallet)
        db_session.commit()
        
        assert wallet.id is not None
        assert wallet.currency == 'KES'
        assert wallet.status == WalletStatus.active
    
    def test_wallet_can_withdraw(self, db_session, regular_user):
        """Test wallet withdrawal permissions"""
        wallet = regular_user.wallet
        wallet.balance = Decimal('1000.00')
        wallet.available_balance = Decimal('1000.00')
        wallet.daily_limit = Decimal('5000.00')
        
        # Can withdraw valid amount
        result = wallet.can_withdraw(Decimal('500.00'))
        assert result['allowed'] == True
        
        # Cannot withdraw more than balance
        result = wallet.can_withdraw(Decimal('1500.00'))
        assert result['allowed'] == False
        
        # Cannot withdraw negative amount
        result = wallet.can_withdraw(Decimal('-100.00'))
        assert result['allowed'] == False
        
        # Cannot withdraw zero
        result = wallet.can_withdraw(Decimal('0.00'))
        assert result['allowed'] == False
        
        # Cannot withdraw if frozen
        wallet.status = WalletStatus.frozen
        result = wallet.can_withdraw(Decimal('100.00'))
        assert result['allowed'] == False
    
    def test_wallet_lock_funds(self, db_session, regular_user):
        """Test locking funds in wallet"""
        wallet = regular_user.wallet
        wallet.balance = Decimal('1000.00')
        wallet.available_balance = Decimal('1000.00')
        wallet.locked_balance = Decimal('0.00')
        
        # Lock funds
        result = wallet.lock_funds(Decimal('300.00'))
        assert result == True
        assert wallet.available_balance == Decimal('700.00')
        assert wallet.locked_balance == Decimal('300.00')
        assert wallet.balance == Decimal('1000.00')  # Total unchanged
        
        # Cannot lock more than available
        result = wallet.lock_funds(Decimal('800.00'))
        assert result == False
        
        # Unlock funds
        result = wallet.unlock_funds(Decimal('200.00'))
        assert result == True
        assert wallet.available_balance == Decimal('900.00')
        assert wallet.locked_balance == Decimal('100.00')
        
        # Cannot unlock more than locked
        result = wallet.unlock_funds(Decimal('200.00'))
        assert result == False

class TestTransactionModel:
    """Test Transaction model"""
    
    def test_create_transaction(self, db_session, regular_user, second_user):
        """Test creating a transaction"""
        transaction = Transaction(
            sender_wallet_id=regular_user.wallet.id,
            receiver_wallet_id=second_user.wallet.id,
            amount=Decimal('1000.00'),
            fee=Decimal('10.00'),
            net_amount=Decimal('990.00'),
            transaction_type=TransactionType.transfer,
            status=TransactionStatus.pending,
            provider=PaymentProvider.internal,
            description='Test transaction'
        )
        
        db_session.add(transaction)
        db_session.commit()
        
        assert transaction.id is not None
        assert transaction.reference is not None
        assert transaction.idempotency_key is not None
        assert transaction.created_at is not None
    
    def test_transaction_fee_calculation(self):
        """Test transaction fee calculation"""
        # Transfer fee
        fee = Transaction.calculate_fee(Decimal('1000.00'), 'transfer')
        assert fee == Decimal('10.00')  # 1% of 1000, min 10
        
        fee = Transaction.calculate_fee(Decimal('100.00'), 'transfer')
        assert fee == Decimal('10.00')  # Minimum fee
        
        fee = Transaction.calculate_fee(Decimal('100000.00'), 'transfer')
        assert fee == Decimal('1000.00')  # 1% of 100000 = 1000
        
        # Withdrawal fee
        fee = Transaction.calculate_fee(Decimal('1000.00'), 'withdrawal')
        assert fee == Decimal('27.50')  # Fixed fee
        
        # Deposit fee
        fee = Transaction.calculate_fee(Decimal('1000.00'), 'deposit')
        assert fee == Decimal('0.00')  # No fee
    
    def test_transaction_status_updates(self, db_session):
        """Test transaction status updates"""
        transaction = Transaction(
            amount=Decimal('100.00'),
            transaction_type=TransactionType.transfer,
            status=TransactionStatus.pending
        )
        
        # Valid transition: pending -> processing
        result = transaction.update_status(TransactionStatus.processing)
        assert result == True
        assert transaction.status == TransactionStatus.processing
        assert transaction.initiated_at is not None
        
        # Valid transition: processing -> completed
        result = transaction.update_status(TransactionStatus.completed)
        assert result == True
        assert transaction.status == TransactionStatus.completed
        assert transaction.completed_at is not None
        
        # Invalid transition: completed -> processing
        result = transaction.update_status(TransactionStatus.processing)
        assert result == False
        
        # Valid transition: completed -> reversed
        result = transaction.update_status(TransactionStatus.reversed)
        assert result == True
        assert transaction.status == TransactionStatus.reversed
        assert transaction.reversed_at is not None

class TestBeneficiaryModel:
    """Test Beneficiary model"""
    
    def test_create_beneficiary(self, db_session, regular_user, second_user):
        """Test creating a beneficiary"""
        beneficiary = Beneficiary(
            user_id=regular_user.id,
            beneficiary_wallet_id=second_user.wallet.id,
            nickname='Test Friend',
            category='friend'
        )
        
        db_session.add(beneficiary)
        db_session.commit()
        
        assert beneficiary.id is not None
        assert beneficiary.total_transfers == 0
        assert beneficiary.total_amount == Decimal('0.00')
        assert beneficiary.is_trusted == False
    
    def test_beneficiary_can_send(self, db_session, regular_user, second_user):
        """Test beneficiary sending limits"""
        beneficiary = Beneficiary(
            user_id=regular_user.id,
            beneficiary_wallet_id=second_user.wallet.id
        )
        
        # Untrusted beneficiary has lower limits
        result = beneficiary.can_send(Decimal('10000.00'))
        assert result['allowed'] == True
        
        result = beneficiary.can_send(Decimal('60000.00'))  # Above untrusted limit
        assert result['allowed'] == False
        
        # Trusted beneficiary can send more
        beneficiary.is_trusted = True
        result = beneficiary.can_send(Decimal('60000.00'))
        assert result['allowed'] == True
        
        # Custom daily limit
        beneficiary.daily_limit = Decimal('20000.00')
        result = beneficiary.can_send(Decimal('25000.00'))
        assert result['allowed'] == False
    
    def test_beneficiary_statistics_update(self, db_session, regular_user, second_user):
        """Test updating beneficiary statistics"""
        beneficiary = Beneficiary(
            user_id=regular_user.id,
            beneficiary_wallet_id=second_user.wallet.id
        )
        db_session.add(beneficiary)
        db_session.commit()
        
        assert beneficiary.total_transfers == 0
        assert beneficiary.total_amount == Decimal('0.00')
        assert beneficiary.last_transfer_at is None
        
        # Update statistics
        beneficiary.update_statistics(Decimal('5000.00'))
        
        assert beneficiary.total_transfers == 1
        assert beneficiary.total_amount == Decimal('5000.00')
        assert beneficiary.last_transfer_at is not None

class TestLedgerEntryModel:
    """Test LedgerEntry model"""
    
    def test_create_ledger_entry(self, db_session, regular_user, sample_transaction):
        """Test creating a ledger entry"""
        ledger = LedgerEntry(
            wallet_id=regular_user.wallet.id,
            transaction_id=sample_transaction.id,
            amount=Decimal('-1000.00'),
            balance_before=Decimal('5000.00'),
            balance_after=Decimal('4000.00'),
            entry_type='debit',
            description='Test debit'
        )
        
        db_session.add(ledger)
        db_session.commit()
        
        assert ledger.id is not None
        assert ledger.created_at is not None
    
    def test_ledger_balance_validation(self):
        """Test ledger balance calculation validation"""
        # This would fail due to check constraint
        # Should be tested at database level
        
        # balance_after should equal balance_before + amount
        # Negative test case would be trying to create with invalid calculation
        pass

class TestAuditLogModel:
    """Test AuditLog model"""
    
    def test_create_audit_log(self, db_session, regular_user):
        """Test creating an audit log"""
        audit_log = AuditLog.log_user_action(
            actor_id=regular_user.id,
            action='test.action',
            resource_type='user',
            resource_id=regular_user.id,
            old_values={'name': 'old'},
            new_values={'name': 'new'},
            status='success'
        )
        
        db_session.commit()
        
        assert audit_log.id is not None
        assert audit_log.actor_type == 'user'
        assert audit_log.created_at is not None
    
    def test_audit_log_types(self, db_session, regular_user, admin_user):
        """Test different types of audit logs"""
        # User action
        user_log = AuditLog.log_user_action(
            actor_id=regular_user.id,
            action='user.login',
            resource_type='user',
            resource_id=regular_user.id
        )
        assert user_log.actor_type == 'user'
        
        # Admin action
        admin_log = AuditLog.log_admin_action(
            actor_id=admin_user.id,
            action='admin.verify',
            resource_type='kyc',
            resource_id=1
        )
        assert admin_log.actor_type == 'admin'
        
        # System action
        system_log = AuditLog.log_system_action(
            action='system.cleanup',
            resource_type='transaction',
            resource_id=1
        )
        assert system_log.actor_type == 'system'
        
        db_session.commit()
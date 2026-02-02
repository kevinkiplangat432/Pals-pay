import pytest
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal

# Add the app directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, Wallet, Transaction, Beneficiary, KYCVerification, PaymentMethod
from app.models.enums import TransactionStatus, TransactionType, KYCStatus, PaymentProvider
from flask_jwt_extended import create_access_token

@pytest.fixture(scope='session')
def app():
    """Create and configure a test app instance"""
    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'postgresql://postgres:password@localhost/money_transfer_test',
        'WTF_CSRF_ENABLED': False,
    })
    
    with app.app_context():
        yield app

@pytest.fixture(scope='session')
def client(app):
    """Create a test client"""
    return app.test_client()

@pytest.fixture(scope='session')
def database(app):
    """Create test database"""
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()

@pytest.fixture
def db_session(database):
    """Create a fresh database session for each test"""
    connection = database.engine.connect()
    transaction = connection.begin()
    
    options = dict(bind=connection, binds={})
    session = database.create_scoped_session(options=options)
    
    database.session = session
    
    yield session
    
    transaction.rollback()
    connection.close()
    session.remove()

@pytest.fixture
def regular_user(db_session):
    """Create a regular user for testing"""
    user = User(
        email='user@test.com',
        username='testuser',
        phone_number='+254700000001',
        first_name='Test',
        last_name='User',
        is_active=True,
        is_verified=True,
        kyc_status=KYCStatus.verified
    )
    user.set_password('password123')
    db_session.add(user)
    db_session.commit()
    
    # Ensure wallet exists
    if not user.wallet:
        wallet = Wallet(user_id=user.id, balance=Decimal('100000'))
        db_session.add(wallet)
        db_session.commit()
    
    return user

@pytest.fixture
def admin_user(db_session):
    """Create an admin user for testing"""
    admin = User(
        email='admin@test.com',
        username='adminuser',
        phone_number='+254700000002',
        first_name='Admin',
        last_name='User',
        is_admin=True,
        is_active=True,
        is_verified=True,
        kyc_status=KYCStatus.verified
    )
    admin.set_password('password123')
    db_session.add(admin)
    db_session.commit()
    
    # Ensure wallet exists
    if not admin.wallet:
        wallet = Wallet(user_id=admin.id, balance=Decimal('50000'))
        db_session.add(wallet)
        db_session.commit()
    
    return admin

@pytest.fixture
def second_user(db_session):
    """Create a second user for beneficiary testing"""
    user = User(
        email='second@test.com',
        username='seconduser',
        phone_number='+254700000003',
        first_name='Second',
        last_name='User',
        is_active=True,
        is_verified=True,
        kyc_status=KYCStatus.verified
    )
    user.set_password('password123')
    db_session.add(user)
    db_session.commit()
    
    # Ensure wallet exists
    if not user.wallet:
        wallet = Wallet(user_id=user.id, balance=Decimal('50000'))
        db_session.add(wallet)
        db_session.commit()
    
    return user

@pytest.fixture
def unverified_user(db_session):
    """Create an unverified user for KYC testing"""
    user = User(
        email='unverified@test.com',
        username='unverifieduser',
        phone_number='+254700000004',
        first_name='Unverified',
        last_name='User',
        is_active=True,
        is_verified=False,
        kyc_status=KYCStatus.unverified
    )
    user.set_password('password123')
    db_session.add(user)
    db_session.commit()
    
    return user

@pytest.fixture
def auth_headers(regular_user):
    """Generate authentication headers for regular user"""
    token = create_access_token(identity=regular_user.id)
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def admin_headers(admin_user):
    """Generate authentication headers for admin user"""
    token = create_access_token(identity=admin_user.id)
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def beneficiary(regular_user, second_user, db_session):
    """Create a beneficiary for testing"""
    beneficiary = Beneficiary(
        user_id=regular_user.id,
        beneficiary_wallet_id=second_user.wallet.id,
        nickname='Test Friend',
        category='friend',
        is_trusted=True
    )
    db_session.add(beneficiary)
    db_session.commit()
    return beneficiary

@pytest.fixture
def sample_transaction(regular_user, second_user, db_session):
    """Create a sample transaction for testing"""
    transaction = Transaction(
        sender_wallet_id=regular_user.wallet.id,
        receiver_wallet_id=second_user.wallet.id,
        amount=Decimal('1000.00'),
        fee=Decimal('10.00'),
        net_amount=Decimal('990.00'),
        transaction_type=TransactionType.transfer,
        status=TransactionStatus.completed,
        provider=PaymentProvider.internal,
        description='Test transfer'
    )
    db_session.add(transaction)
    db_session.commit()
    return transaction

@pytest.fixture
def payment_method(regular_user, db_session):
    """Create a payment method for testing"""
    pm = PaymentMethod(
        user_id=regular_user.id,
        provider=PaymentProvider.mpesa,
        account_reference='+254700000001',
        account_name='Test User',
        is_verified=True,
        is_default=True
    )
    db_session.add(pm)
    db_session.commit()
    return pm
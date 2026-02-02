import json
import pytest
from decimal import Decimal

class TestWalletRoutes:
    """Test wallet operations"""
    
    def test_wallet_summary(self, client, auth_headers, regular_user):
        """Test getting wallet summary"""
        response = client.get('/api/wallet/summary',
                            headers=auth_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        
        assert 'balance' in response_data
        assert 'available_balance' in response_data
        assert 'currency' in response_data
        assert response_data['currency'] == 'KES'
    
    def test_wallet_analytics(self, client, auth_headers):
        """Test getting wallet analytics"""
        response = client.get('/api/wallet/analytics',
                            headers=auth_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        
        assert 'wallet_summary' in response_data
        assert 'today' in response_data
        assert 'this_month' in response_data
        assert 'overall' in response_data
    
    def test_wallet_summary_requires_auth(self, client):
        """Test wallet summary requires authentication"""
        response = client.get('/api/wallet/summary')
        assert response.status_code == 401
    
    def test_transfer_to_beneficiary_success(self, client, auth_headers, beneficiary, regular_user, second_user, db_session):
        """Test successful transfer to beneficiary"""
        # Get initial balances
        initial_sender_balance = regular_user.wallet.balance
        initial_receiver_balance = second_user.wallet.balance
        
        data = {
            'beneficiary_wallet_id': beneficiary.beneficiary_wallet_id,
            'amount': 1000.00,
            'description': 'Test transfer'
        }
        
        response = client.post('/api/wallet/transfer',
                             headers=auth_headers,
                             json=data)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] == True
        
        # Verify balances updated correctly
        db_session.refresh(regular_user.wallet)
        db_session.refresh(second_user.wallet)
        
        # Sender pays amount + fee
        expected_fee = Decimal('10.00')  # 1% of 1000, min 10
        expected_sender_deduction = Decimal('1010.00')
        assert regular_user.wallet.balance == initial_sender_balance - expected_sender_deduction
        
        # Receiver gets amount - fee
        expected_receiver_gain = Decimal('990.00')
        assert second_user.wallet.balance == initial_receiver_balance + expected_receiver_gain
    
    def test_transfer_insufficient_balance(self, client, auth_headers, beneficiary, regular_user, db_session):
        """Test transfer with insufficient balance"""
        # Set low balance
        regular_user.wallet.balance = Decimal('100.00')
        regular_user.wallet.available_balance = Decimal('100.00')
        db_session.commit()
        
        data = {
            'beneficiary_wallet_id': beneficiary.beneficiary_wallet_id,
            'amount': 1000.00
        }
        
        response = client.post('/api/wallet/transfer',
                             headers=auth_headers,
                             json=data)
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert 'Insufficient' in response_data['message']
    
    def test_transfer_to_self(self, client, auth_headers, regular_user):
        """Test transfer to self should fail"""
        data = {
            'beneficiary_wallet_id': regular_user.wallet.id,  # Self transfer
            'amount': 100.00
        }
        
        response = client.post('/api/wallet/transfer',
                             headers=auth_headers,
                             json=data)
        
        assert response.status_code == 400
    
    def test_transfer_requires_kyc(self, client, unverified_user, db_session):
        """Test transfer requires KYC verification"""
        # Create token for unverified user
        from flask_jwt_extended import create_access_token
        token = create_access_token(identity=unverified_user.id)
        headers = {'Authorization': f'Bearer {token}'}
        
        # Create wallet for unverified user
        from app.models import Wallet
        wallet = Wallet(user_id=unverified_user.id, balance=Decimal('10000'))
        db_session.add(wallet)
        db_session.commit()
        
        data = {
            'beneficiary_wallet_id': 1,  # Any wallet
            'amount': 100.00
        }
        
        response = client.post('/api/wallet/transfer',
                             headers=headers,
                             json=data)
        
        assert response.status_code == 403
    
    def test_transfer_to_phone_success(self, client, auth_headers, second_user, regular_user, db_session):
        """Test transfer to phone number"""
        initial_sender_balance = regular_user.wallet.balance
        initial_receiver_balance = second_user.wallet.balance
        
        data = {
            'phone_number': second_user.phone_number,
            'amount': 500.00
        }
        
        response = client.post('/api/wallet/transfer/phone',
                             headers=auth_headers,
                             json=data)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] == True
        
        # Verify balances updated
        db_session.refresh(regular_user.wallet)
        db_session.refresh(second_user.wallet)
        
        assert regular_user.wallet.balance < initial_sender_balance
        assert second_user.wallet.balance > initial_receiver_balance
    
    def test_transfer_to_nonexistent_phone(self, client, auth_headers):
        """Test transfer to non-existent phone number"""
        data = {
            'phone_number': '+254799999999',
            'amount': 100.00
        }
        
        response = client.post('/api/wallet/transfer/phone',
                             headers=auth_headers,
                             json=data)
        
        assert response.status_code == 404
    
    def test_withdraw_funds_success(self, client, auth_headers, payment_method, regular_user, db_session):
        """Test successful withdrawal"""
        initial_balance = regular_user.wallet.balance
        
        data = {
            'amount': 1000.00,
            'payment_method_id': payment_method.id
        }
        
        response = client.post('/api/wallet/withdraw',
                             headers=auth_headers,
                             json=data)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] == True
        
        # Verify balance reduced by amount + fee
        db_session.refresh(regular_user.wallet)
        expected_fee = Decimal('27.50')  # Fixed withdrawal fee
        expected_total = Decimal('1027.50')
        assert regular_user.wallet.balance == initial_balance - expected_total
    
    def test_withdraw_insufficient_balance(self, client, auth_headers, payment_method, regular_user, db_session):
        """Test withdrawal with insufficient balance"""
        regular_user.wallet.balance = Decimal('100.00')
        regular_user.wallet.available_balance = Decimal('100.00')
        db_session.commit()
        
        data = {
            'amount': 1000.00,
            'payment_method_id': payment_method.id
        }
        
        response = client.post('/api/wallet/withdraw',
                             headers=auth_headers,
                             json=data)
        
        assert response.status_code == 400
    
    def test_withdraw_unverified_payment_method(self, client, auth_headers, regular_user, db_session):
        """Test withdrawal with unverified payment method"""
        from app.models import PaymentMethod
        unverified_pm = PaymentMethod(
            user_id=regular_user.id,
            provider='bank',
            account_reference='123456',
            is_verified=False
        )
        db_session.add(unverified_pm)
        db_session.commit()
        
        data = {
            'amount': 100.00,
            'payment_method_id': unverified_pm.id
        }
        
        response = client.post('/api/wallet/withdraw',
                             headers=auth_headers,
                             json=data)
        
        assert response.status_code == 404  # Not found because is_verified=False
    
    def test_transaction_summary(self, client, auth_headers):
        """Test getting transaction summary"""
        response = client.get('/api/wallet/transactions/summary',
                            headers=auth_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        
        assert 'sent_count' in response_data
        assert 'received_count' in response_data
        assert 'total_sent' in response_data
        assert 'total_received' in response_data
        assert 'period_days' in response_data
    
    def test_deposit_mpesa_requires_kyc(self, client, unverified_user, db_session):
        """Test MPesa deposit requires KYC"""
        from flask_jwt_extended import create_access_token
        token = create_access_token(identity=unverified_user.id)
        headers = {'Authorization': f'Bearer {token}'}
        
        data = {
            'amount': 1000.00,
            'phone_number': '+254700000000'
        }
        
        response = client.post('/api/wallet/deposit/mpesa',
                             headers=headers,
                             json=data)
        
        assert response.status_code == 403
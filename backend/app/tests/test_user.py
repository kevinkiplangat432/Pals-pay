import json
import pytest

class TestUserRoutes:
    """Test user profile and related endpoints"""
    
    def test_get_user_profile(self, client, auth_headers, regular_user):
        """Test getting detailed user profile"""
        response = client.get('/api/user/profile',
                            headers=auth_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        
        assert response_data['email'] == regular_user.email
        assert response_data['username'] == regular_user.username
        assert 'wallet' in response_data
        assert 'kyc' in response_data
    
    def test_update_user_profile_success(self, client, auth_headers, regular_user, db_session):
        """Test updating user profile"""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '+254711111111'
        }
        
        response = client.put('/api/user/profile',
                            headers=auth_headers,
                            json=data)
        
        assert response.status_code == 200
        
        # Verify updates
        db_session.refresh(regular_user)
        assert regular_user.first_name == 'John'
        assert regular_user.last_name == 'Doe'
        assert regular_user.phone_number == '+254711111111'
    
    def test_update_profile_invalid_phone(self, client, auth_headers):
        """Test updating profile with invalid phone number"""
        data = {
            'phone_number': 'invalid'
        }
        
        response = client.put('/api/user/profile',
                            headers=auth_headers,
                            json=data)
        
        assert response.status_code == 400
    
    def test_get_kyc_status(self, client, auth_headers, regular_user):
        """Test getting KYC status"""
        response = client.get('/api/user/kyc/status',
                            headers=auth_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert 'status' in response_data
        assert response_data['status'] == regular_user.kyc_status.value
    
    def test_get_payment_methods(self, client, auth_headers, payment_method):
        """Test getting user payment methods"""
        response = client.get('/api/user/payment-methods',
                            headers=auth_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert 'payment_methods' in response_data
        assert len(response_data['payment_methods']) > 0
    
    def test_add_payment_method_success(self, client, auth_headers, regular_user, db_session):
        """Test adding a new payment method"""
        data = {
            'provider': 'bank',
            'account_reference': '1234567890',
            'account_name': 'Test Bank Account',
            'is_default': False
        }
        
        response = client.post('/api/user/payment-methods',
                             headers=auth_headers,
                             json=data)
        
        assert response.status_code == 201
        
        # Verify creation
        from app.models import PaymentMethod
        payment_method = PaymentMethod.query.filter_by(
            user_id=regular_user.id,
            account_reference='1234567890'
        ).first()
        assert payment_method is not None
    
    def test_add_payment_method_duplicate(self, client, auth_headers, payment_method):
        """Test adding duplicate payment method"""
        data = {
            'provider': payment_method.provider.value,
            'account_reference': payment_method.account_reference,
            'account_name': 'Duplicate'
        }
        
        response = client.post('/api/user/payment-methods',
                             headers=auth_headers,
                             json=data)
        
        assert response.status_code == 400
    
    def test_delete_payment_method(self, client, auth_headers, payment_method, db_session):
        """Test deleting a payment method"""
        # First, ensure it's not default
        payment_method.is_default = False
        db_session.commit()
        
        response = client.delete(f'/api/user/payment-methods/{payment_method.id}',
                               headers=auth_headers)
        
        assert response.status_code == 200
        
        # Verify deletion
        db_session.refresh(payment_method)
        assert payment_method not in db_session
    
    def test_delete_default_payment_method(self, client, auth_headers, payment_method):
        """Test trying to delete default payment method"""
        response = client.delete(f'/api/user/payment-methods/{payment_method.id}',
                               headers=auth_headers)
        
        assert response.status_code == 400
    
    def test_set_default_payment_method(self, client, auth_headers, regular_user, db_session):
        """Test setting default payment method"""
        # Create a second payment method
        from app.models import PaymentMethod
        second_pm = PaymentMethod(
            user_id=regular_user.id,
            provider='bank',
            account_reference='0987654321',
            account_name='Second Account',
            is_default=False,
            is_verified=True
        )
        db_session.add(second_pm)
        db_session.commit()
        
        response = client.put(f'/api/user/payment-methods/{second_pm.id}/default',
                            headers=auth_headers)
        
        assert response.status_code == 200
        
        # Verify it's now default and the other is not
        db_session.refresh(second_pm)
        assert second_pm.is_default == True
    
    def test_get_transaction_history(self, client, auth_headers, sample_transaction):
        """Test getting transaction history"""
        response = client.get('/api/user/transactions',
                            headers=auth_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert 'transactions' in response_data
        assert 'total' in response_data
    
    def test_get_transaction_history_paginated(self, client, auth_headers):
        """Test paginated transaction history"""
        response = client.get('/api/user/transactions?page=1&per_page=10',
                            headers=auth_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert 'current_page' in response_data
        assert response_data['current_page'] == 1
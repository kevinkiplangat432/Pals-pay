import json
from decimal import Decimal
import pytest

class TestAuthRoutes:
    """Test authentication endpoints"""
    
    def test_register_success(self, client, db_session):
        """Test successful user registration"""
        data = {
            'username': 'newuser',
            'email': 'new@test.com',
            'phone_number': '+254700000099',
            'password': 'password123',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        response = client.post('/api/auth/register', 
                             json=data,
                             content_type='application/json')
        
        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert response_data['message'] == 'User registered successfully'
        assert 'user' in response_data
        
        # Verify user was created
        from app.models import User
        user = User.query.filter_by(email='new@test.com').first()
        assert user is not None
        assert user.username == 'newuser'
        assert user.wallet is not None
    
    def test_register_missing_fields(self, client):
        """Test registration with missing required fields"""
        data = {
            'username': 'newuser',
            'email': 'new@test.com'
            # Missing other required fields
        }
        
        response = client.post('/api/auth/register', json=data)
        assert response.status_code == 400
    
    def test_register_duplicate_email(self, client, regular_user):
        """Test registration with duplicate email"""
        data = {
            'username': 'differentuser',
            'email': regular_user.email,  # Duplicate email
            'phone_number': '+254700000088',
            'password': 'password123',
            'first_name': 'Different',
            'last_name': 'User'
        }
        
        response = client.post('/api/auth/register', json=data)
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert 'already registered' in response_data['message']
    
    def test_login_success(self, client, regular_user):
        """Test successful login"""
        data = {
            'identifier': regular_user.email,
            'password': 'password123'
        }
        
        response = client.post('/api/auth/login', json=data)
        assert response.status_code == 200
        
        response_data = json.loads(response.data)
        assert 'access_token' in response_data
        assert 'refresh_token' in response_data
        assert 'user' in response_data
        assert response_data['user']['email'] == regular_user.email
    
    def test_login_with_username(self, client, regular_user):
        """Test login with username"""
        data = {
            'identifier': regular_user.username,
            'password': 'password123'
        }
        
        response = client.post('/api/auth/login', json=data)
        assert response.status_code == 200
    
    def test_login_with_phone(self, client, regular_user):
        """Test login with phone number"""
        data = {
            'identifier': regular_user.phone_number,
            'password': 'password123'
        }
        
        response = client.post('/api/auth/login', json=data)
        assert response.status_code == 200
    
    def test_login_invalid_credentials(self, client, regular_user):
        """Test login with invalid credentials"""
        data = {
            'identifier': regular_user.email,
            'password': 'wrongpassword'
        }
        
        response = client.post('/api/auth/login', json=data)
        assert response.status_code == 401
    
    def test_login_inactive_account(self, client, db_session, regular_user):
        """Test login with inactive account"""
        regular_user.is_active = False
        db_session.commit()
        
        data = {
            'identifier': regular_user.email,
            'password': 'password123'
        }
        
        response = client.post('/api/auth/login', json=data)
        assert response.status_code == 403
    
    def test_refresh_token(self, client, auth_headers):
        """Test token refresh"""
        response = client.post('/api/auth/refresh',
                             headers=auth_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert 'access_token' in response_data
    
    def test_refresh_token_no_auth(self, client):
        """Test token refresh without authentication"""
        response = client.post('/api/auth/refresh')
        assert response.status_code == 401
    
    def test_profile_requires_auth(self, client):
        """Test profile endpoint requires authentication"""
        response = client.get('/api/auth/profile')
        assert response.status_code == 401
    
    def test_profile_success(self, client, auth_headers, regular_user):
        """Test getting user profile"""
        response = client.get('/api/auth/profile',
                            headers=auth_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['email'] == regular_user.email
        assert response_data['username'] == regular_user.username
    
    def test_update_profile_success(self, client, auth_headers, regular_user, db_session):
        """Test updating user profile"""
        data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        
        response = client.put('/api/auth/profile',
                            headers=auth_headers,
                            json=data)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['message'] == 'Profile updated successfully'
        
        # Verify update in database
        db_session.refresh(regular_user)
        assert regular_user.first_name == 'Updated'
        assert regular_user.last_name == 'Name'
    
    def test_update_profile_duplicate_email(self, client, auth_headers, second_user, regular_user):
        """Test updating profile with duplicate email"""
        data = {
            'email': second_user.email  # Already taken by another user
        }
        
        response = client.put('/api/auth/profile',
                            headers=auth_headers,
                            json=data)
        
        assert response.status_code == 400
    
    def test_change_password_success(self, client, auth_headers, regular_user, db_session):
        """Test changing password successfully"""
        data = {
            'current_password': 'password123',
            'new_password': 'newpassword456'
        }
        
        response = client.put('/api/auth/change-password',
                            headers=auth_headers,
                            json=data)
        
        assert response.status_code == 200
        
        # Verify new password works
        db_session.refresh(regular_user)
        assert regular_user.check_password('newpassword456')
    
    def test_change_password_wrong_current(self, client, auth_headers):
        """Test changing password with wrong current password"""
        data = {
            'current_password': 'wrongpassword',
            'new_password': 'newpassword456'
        }
        
        response = client.put('/api/auth/change-password',
                            headers=auth_headers,
                            json=data)
        
        assert response.status_code == 400
    
    def test_change_password_short_new(self, client, auth_headers):
        """Test changing password with too short new password"""
        data = {
            'current_password': 'password123',
            'new_password': '123'  # Too short
        }
        
        response = client.put('/api/auth/change-password',
                            headers=auth_headers,
                            json=data)
        
        assert response.status_code == 400
    
    def test_logout(self, client, auth_headers):
        """Test logout endpoint"""
        response = client.post('/api/auth/logout',
                             headers=auth_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['message'] == 'Logged out successfully'
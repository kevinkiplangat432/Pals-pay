import json
import pytest

class TestBeneficiaryRoutes:
    """Test beneficiary management endpoints"""
    
    def test_get_beneficiaries(self, client, auth_headers, beneficiary):
        """Test getting user's beneficiaries"""
        response = client.get('/api/beneficiaries/',
                            headers=auth_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert 'beneficiaries' in response_data
        assert 'count' in response_data
        assert response_data['count'] > 0
    
    def test_get_beneficiaries_requires_auth(self, client):
        """Test beneficiaries endpoint requires authentication"""
        response = client.get('/api/beneficiaries/')
        assert response.status_code == 401
    
    def test_add_beneficiary_success(self, client, auth_headers, second_user, regular_user, db_session):
        """Test adding a new beneficiary"""
        data = {
            'beneficiary_user_id': second_user.id,
            'nickname': 'My Friend',
            'category': 'friend',
            'is_trusted': True
        }
        
        response = client.post('/api/beneficiaries/',
                             headers=auth_headers,
                             json=data)
        
        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert 'beneficiary' in response_data
        
        # Verify beneficiary was created
        from app.models import Beneficiary
        beneficiary = Beneficiary.query.filter_by(
            user_id=regular_user.id,
            beneficiary_wallet_id=second_user.wallet.id
        ).first()
        assert beneficiary is not None
        assert beneficiary.nickname == 'My Friend'
    
    def test_add_self_as_beneficiary(self, client, auth_headers, regular_user):
        """Test adding self as beneficiary should fail"""
        data = {
            'beneficiary_user_id': regular_user.id
        }
        
        response = client.post('/api/beneficiaries/',
                             headers=auth_headers,
                             json=data)
        
        assert response.status_code == 400
    
    def test_add_duplicate_beneficiary(self, client, auth_headers, beneficiary):
        """Test adding duplicate beneficiary"""
        data = {
            'beneficiary_wallet_id': beneficiary.beneficiary_wallet_id,
            'nickname': 'Duplicate'
        }
        
        response = client.post('/api/beneficiaries/',
                             headers=auth_headers,
                             json=data)
        
        assert response.status_code == 400
    
    def test_update_beneficiary(self, client, auth_headers, beneficiary, db_session):
        """Test updating beneficiary"""
        data = {
            'nickname': 'Updated Nickname',
            'daily_limit': 50000.00,
            'is_trusted': False
        }
        
        response = client.put(f'/api/beneficiaries/{beneficiary.id}',
                            headers=auth_headers,
                            json=data)
        
        assert response.status_code == 200
        
        # Verify updates
        db_session.refresh(beneficiary)
        assert beneficiary.nickname == 'Updated Nickname'
        assert beneficiary.daily_limit == 50000.00
        assert beneficiary.is_trusted == False
    
    def test_update_nonexistent_beneficiary(self, client, auth_headers):
        """Test updating non-existent beneficiary"""
        response = client.put('/api/beneficiaries/999',
                            headers=auth_headers,
                            json={'nickname': 'Test'})
        
        assert response.status_code == 404
    
    def test_update_other_users_beneficiary(self, client, auth_headers, beneficiary, second_user, db_session):
        """Test updating another user's beneficiary should fail"""
        # Create token for second user
        from flask_jwt_extended import create_access_token
        token = create_access_token(identity=second_user.id)
        headers = {'Authorization': f'Bearer {token}'}
        
        response = client.put(f'/api/beneficiaries/{beneficiary.id}',
                            headers=headers,
                            json={'nickname': 'Hacked'})
        
        assert response.status_code == 404
    
    def test_delete_beneficiary(self, client, auth_headers, beneficiary, db_session):
        """Test deleting beneficiary"""
        response = client.delete(f'/api/beneficiaries/{beneficiary.id}',
                               headers=auth_headers)
        
        assert response.status_code == 200
        
        # Verify deletion
        from app.models import Beneficiary
        deleted = Beneficiary.query.get(beneficiary.id)
        assert deleted is None
    
    def test_delete_nonexistent_beneficiary(self, client, auth_headers):
        """Test deleting non-existent beneficiary"""
        response = client.delete('/api/beneficiaries/999',
                               headers=auth_headers)
        
        assert response.status_code == 404
    
    def test_search_users_for_beneficiary(self, client, auth_headers, second_user):
        """Test searching users to add as beneficiaries"""
        response = client.get('/api/beneficiaries/search?q=second',
                            headers=auth_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert 'users' in response_data
        assert len(response_data['users']) > 0
    
    def test_search_requires_query(self, client, auth_headers):
        """Test search requires query parameter"""
        response = client.get('/api/beneficiaries/search',
                            headers=auth_headers)
        
        assert response.status_code == 400
    
    def test_search_min_length(self, client, auth_headers):
        """Test search requires minimum query length"""
        response = client.get('/api/beneficiaries/search?q=ab',
                            headers=auth_headers)
        
        assert response.status_code == 400
    
    def test_beneficiary_statistics_update(self, client, auth_headers, beneficiary, regular_user, second_user, db_session):
        """Test beneficiary statistics update after transfer"""
        initial_transfers = beneficiary.total_transfers
        initial_amount = beneficiary.total_amount
        
        # Make a transfer
        data = {
            'beneficiary_wallet_id': beneficiary.beneficiary_wallet_id,
            'amount': 1000.00
        }
        
        response = client.post('/api/wallet/transfer',
                             headers=auth_headers,
                             json=data)
        
        assert response.status_code == 200
        
        # Verify statistics updated
        db_session.refresh(beneficiary)
        assert beneficiary.total_transfers == initial_transfers + 1
        assert beneficiary.total_amount > initial_amount
        assert beneficiary.last_transfer_at is not None
    
    def test_beneficiary_daily_limit(self, client, auth_headers, beneficiary, db_session):
        """Test beneficiary daily limit enforcement"""
        beneficiary.daily_limit = 1000.00
        db_session.commit()
        
        data = {
            'beneficiary_wallet_id': beneficiary.beneficiary_wallet_id,
            'amount': 1500.00  # Exceeds daily limit
        }
        
        response = client.post('/api/wallet/transfer',
                             headers=auth_headers,
                             json=data)
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert 'daily limit' in response_data['message'].lower()
import json
import pytest
from decimal import Decimal
from datetime import datetime, timedelta

class TestAdminRoutes:
    """Test admin-specific endpoints"""
    
    def test_get_all_users_requires_admin(self, client, auth_headers):
        """Test get all users requires admin role"""
        response = client.get('/api/admin/users',
                            headers=auth_headers)
        
        # Regular user should get 403
        assert response.status_code == 403
    
    def test_get_all_users_admin_success(self, client, admin_headers, regular_user):
        """Test admin can get all users"""
        response = client.get('/api/admin/users',
                            headers=admin_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert 'users' in response_data
        assert 'total' in response_data
        assert 'pages' in response_data
    
    def test_toggle_user_status_admin(self, client, admin_headers, regular_user, db_session):
        """Test admin can toggle user status"""
        data = {'is_active': False}
        
        response = client.put(f'/api/admin/users/{regular_user.id}/status',
                            headers=admin_headers,
                            json=data)
        
        assert response.status_code == 200
        
        # Verify status changed
        db_session.refresh(regular_user)
        assert regular_user.is_active == False
    
    def test_toggle_user_status_regular_user(self, client, auth_headers):
        """Test regular user cannot toggle status"""
        response = client.put('/api/admin/users/1/status',
                            headers=auth_headers,
                            json={'is_active': False})
        
        assert response.status_code == 403
    
    def test_get_all_wallets_admin(self, client, admin_headers):
        """Test admin can get all wallets"""
        response = client.get('/api/admin/wallets',
                            headers=admin_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert 'wallets' in response_data
    
    def test_get_all_transactions_admin(self, client, admin_headers, sample_transaction):
        """Test admin can get all transactions"""
        response = client.get('/api/admin/transactions',
                            headers=admin_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert 'transactions' in response_data
    
    def test_get_system_stats_admin(self, client, admin_headers):
        """Test admin can get system statistics"""
        response = client.get('/api/admin/stats',
                            headers=admin_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        
        # Check expected stats fields
        assert 'users' in response_data
        assert 'wallets' in response_data
        assert 'transactions' in response_data
    
    def test_reverse_transaction_admin(self, client, admin_headers, sample_transaction, db_session):
        """Test admin can reverse transaction"""
        # Get initial balances
        from app.models import Wallet
        sender_wallet = Wallet.query.get(sample_transaction.sender_wallet_id)
        receiver_wallet = Wallet.query.get(sample_transaction.receiver_wallet_id)
        
        initial_sender_balance = sender_wallet.balance
        initial_receiver_balance = receiver_wallet.balance
        
        response = client.post(f'/api/admin/transactions/{sample_transaction.id}/reverse',
                             headers=admin_headers)
        
        assert response.status_code == 200
        
        # Verify balances reversed
        db_session.refresh(sender_wallet)
        db_session.refresh(receiver_wallet)
        
        # Sender should get amount back
        assert sender_wallet.balance > initial_sender_balance
        # Receiver should lose amount
        assert receiver_wallet.balance < initial_receiver_balance
    
    def test_reverse_already_reversed(self, client, admin_headers, sample_transaction, db_session):
        """Test cannot reverse already reversed transaction"""
        from app.models.enums import TransactionStatus
        sample_transaction.status = TransactionStatus.reversed
        db_session.commit()
        
        response = client.post(f'/api/admin/transactions/{sample_transaction.id}/reverse',
                             headers=admin_headers)
        
        assert response.status_code == 400
    
    def test_get_suspicious_activities_admin(self, client, admin_headers):
        """Test admin can get suspicious activities"""
        response = client.get('/api/admin/suspicious-activities',
                            headers=admin_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert 'large_transactions' in response_data
        assert 'suspicious_users' in response_data
        assert 'failed_logins' in response_data
    
    def test_get_pending_kyc_admin(self, client, admin_headers, unverified_user, db_session):
        """Test admin can get pending KYC"""
        # Create pending KYC
        from app.models import KYCVerification
        from app.models.enums import KYCStatus
        
        kyc = KYCVerification(
            user_id=unverified_user.id,
            status=KYCStatus.pending,
            submitted_at=datetime.utcnow()
        )
        db_session.add(kyc)
        db_session.commit()
        
        response = client.get('/api/admin/kyc/pending',
                            headers=admin_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert 'kyc_verifications' in response_data
    
    def test_verify_kyc_admin(self, client, admin_headers, unverified_user, db_session):
        """Test admin can verify KYC"""
        from app.models import KYCVerification
        from app.models.enums import KYCStatus
        
        kyc = KYCVerification(
            user_id=unverified_user.id,
            status=KYCStatus.pending,
            submitted_at=datetime.utcnow()
        )
        db_session.add(kyc)
        db_session.commit()
        
        data = {'approved': True}
        
        response = client.post(f'/api/admin/kyc/{kyc.id}/verify',
                             headers=admin_headers,
                             json=data)
        
        assert response.status_code == 200
        
        # Verify KYC is now verified
        db_session.refresh(kyc)
        assert kyc.status == KYCStatus.verified
        assert kyc.verified_at is not None
        assert kyc.verified_by == admin_user.id  # Needs admin_user fixture
    
    def test_reject_kyc_admin(self, client, admin_headers, unverified_user, db_session):
        """Test admin can reject KYC"""
        from app.models import KYCVerification
        from app.models.enums import KYCStatus
        
        kyc = KYCVerification(
            user_id=unverified_user.id,
            status=KYCStatus.pending,
            submitted_at=datetime.utcnow()
        )
        db_session.add(kyc)
        db_session.commit()
        
        data = {
            'approved': False,
            'rejection_reason': 'Document blurry'
        }
        
        response = client.post(f'/api/admin/kyc/{kyc.id}/verify',
                             headers=admin_headers,
                             json=data)
        
        assert response.status_code == 200
        
        db_session.refresh(kyc)
        assert kyc.status == KYCStatus.rejected
        assert kyc.rejection_reason == 'Document blurry'
    
    def test_get_profit_trends_admin(self, client, admin_headers):
        """Test admin can get profit trends"""
        response = client.get('/api/admin/analytics/profit-trends',
                            headers=admin_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert 'daily_trends' in response_data
        assert 'by_transaction_type' in response_data
        assert 'top_users' in response_data
    
    def test_get_audit_logs_admin(self, client, admin_headers):
        """Test admin can get audit logs"""
        response = client.get('/api/admin/audit-logs',
                            headers=admin_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert 'audit_logs' in response_data
    
    def test_admin_endpoints_require_auth(self, client):
        """Test all admin endpoints require authentication"""
        endpoints = [
            '/api/admin/users',
            '/api/admin/wallets',
            '/api/admin/transactions',
            '/api/admin/stats',
            '/api/admin/suspicious-activities'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401
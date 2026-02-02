import json
import pytest
from io import BytesIO

class TestKYCRoutes:
    """Test KYC verification endpoints"""
    
    def test_get_kyc_status(self, client, auth_headers, regular_user):
        """Test getting KYC status"""
        response = client.get('/api/user/kyc/status',
                            headers=auth_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['status'] == regular_user.kyc_status.value
    
    def test_submit_kyc_success(self, client, auth_headers, unverified_user, db_session):
        """Test submitting KYC documents"""
        # Create token for unverified user
        from flask_jwt_extended import create_access_token
        token = create_access_token(identity=unverified_user.id)
        headers = {'Authorization': f'Bearer {token}'}
        
        # Create mock file uploads
        data = {
            'document_type': 'national_id',
            'document_number': '12345678'
        }
        
        files = {
            'front_document': (BytesIO(b'front image'), 'front.jpg'),
            'back_document': (BytesIO(b'back image'), 'back.jpg'),
            'selfie': (BytesIO(b'selfie image'), 'selfie.jpg')
        }
        
        response = client.post('/api/user/kyc/submit',
                             headers=headers,
                             data={**data, **files},
                             content_type='multipart/form-data')
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] == True
        
        # Verify KYC status changed to pending
        db_session.refresh(unverified_user)
        from app.models.enums import KYCStatus
        assert unverified_user.kyc_status == KYCStatus.pending
    
    def test_submit_kyc_missing_document(self, client, auth_headers, unverified_user):
        """Test submitting KYC without required documents"""
        from flask_jwt_extended import create_access_token
        token = create_access_token(identity=unverified_user.id)
        headers = {'Authorization': f'Bearer {token}'}
        
        data = {
            'document_type': 'national_id',
            'document_number': '12345678'
        }
        # No files attached
        
        response = client.post('/api/user/kyc/submit',
                             headers=headers,
                             data=data)
        
        assert response.status_code == 400
    
    def test_submit_kyc_already_verified(self, client, auth_headers, regular_user):
        """Test submitting KYC when already verified"""
        data = {
            'document_type': 'national_id',
            'document_number': '12345678'
        }
        
        response = client.post('/api/user/kyc/submit',
                             headers=auth_headers,
                             data=data)
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert 'already' in response_data['message'].lower()
    
    def test_submit_kyc_already_pending(self, client, unverified_user, db_session):
        """Test submitting KYC when already pending"""
        from flask_jwt_extended import create_access_token
        token = create_access_token(identity=unverified_user.id)
        headers = {'Authorization': f'Bearer {token}'}
        
        # Set KYC to pending
        from app.models.enums import KYCStatus
        unverified_user.kyc_status = KYCStatus.pending
        db_session.commit()
        
        response = client.post('/api/user/kyc/submit',
                             headers=headers,
                             data={'document_type': 'national_id'})
        
        assert response.status_code == 400
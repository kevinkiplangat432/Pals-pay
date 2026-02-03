import os
from datetime import datetime
from werkzeug.utils import secure_filename
from ..extensions import db
from app.models import KYCVerification, AuditLog, User
from app.models.enums import KYCStatus, DocumentType

class KYCService:
    
    @staticmethod
    def allowed_file(filename):
        """
        Check if file extension is allowed
        """
        allowed_extensions = {'png', 'jpg', 'jpeg', 'pdf'}
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in allowed_extensions
    
    @staticmethod
    def save_kyc_document(file, user_id, document_type):
        """
        Save KYC document to server
        """
        if file and KYCService.allowed_file(file.filename):
            filename = secure_filename(f"{user_id}_{document_type}_{datetime.utcnow().timestamp()}.{file.filename.split('.')[-1]}")
            upload_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads', 'kyc')
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            return file_path
        return None
    
    @staticmethod
    def submit_kyc(user_id, document_type, document_number, front_doc, back_doc=None, selfie=None):
        """
        Submit KYC documents for verification
        """
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'message': 'User not found'}
        
        kyc = KYCVerification.query.filter_by(user_id=user_id).first()
        if not kyc:
            kyc = KYCVerification(user_id=user_id)
        
        # Save documents
        front_url = KYCService.save_kyc_document(front_doc, user_id, f"{document_type}_front")
        if not front_url:
            return {'success': False, 'message': 'Invalid front document'}
        
        back_url = KYCService.save_kyc_document(back_doc, user_id, f"{document_type}_back") if back_doc else None
        selfie_url = KYCService.save_kyc_document(selfie, user_id, "selfie") if selfie else None
        
        try:
            # Update KYC record
            kyc.document_type = DocumentType(document_type)
            kyc.document_number = document_number
            kyc.document_front_url = front_url
            kyc.document_back_url = back_url
            kyc.selfie_url = selfie_url
            kyc.submit_for_verification()
            
            if kyc.id is None:
                db.session.add(kyc)
            
            # Update user KYC status
            user.kyc_status = KYCStatus.pending
            
            db.session.commit()
            
            # Log the action
            AuditLog.log_user_action(
                actor_id=user_id,
                action='kyc.submit',
                resource_type='kyc',
                resource_id=kyc.id,
                status='success'
            )
            
            return {
                'success': True,
                'message': 'KYC documents submitted for verification',
                'kyc_id': kyc.id
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Failed to submit KYC: {str(e)}'}
    
    @staticmethod
    def verify_kyc(kyc_id, admin_id, approved=True, rejection_reason=None):
        """
        Verify KYC documents (admin only)
        """
        kyc = KYCVerification.query.get(kyc_id)
        if not kyc:
            return {'success': False, 'message': 'KYC record not found'}
        
        try:
            if approved:
                kyc.approve(admin_id)
            else:
                if not rejection_reason:
                    return {'success': False, 'message': 'Rejection reason required'}
                kyc.reject(rejection_reason)
            
            db.session.commit()
            
            # Log the action
            AuditLog.log_admin_action(
                actor_id=admin_id,
                action='kyc.verify',
                resource_type='kyc',
                resource_id=kyc.id,
                new_values={'status': kyc.status.value, 'approved': approved},
                status='success'
            )
            
            return {
                'success': True,
                'message': f'KYC {"approved" if approved else "rejected"}',
                'kyc': kyc.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Failed to verify KYC: {str(e)}'}
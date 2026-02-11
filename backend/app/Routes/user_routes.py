from flask import Blueprint, request, jsonify
import re
from datetime import datetime
from ..extensions import db
from ..models import User, KYCVerification, PaymentMethod, AuditLog
from ..models.enums import KYCStatus, PaymentProvider
from ..auth.decorators import token_required , kyc_required, otp_required
from ..services.kyc_service import KYCService
from werkzeug.security import generate_password_hash

user_bp = Blueprint('user', __name__, url_prefix='/api/v1/user')

# Phone number regex
PHONE_REGEX = r'^\+?[1-9]\d{1,14}$'  # E.164 format

# Get user profile
@user_bp.route('/profile', methods=['GET'])
@token_required
def get_user_profile():
    user = request.current_user
    return jsonify(user.to_dict(include_wallet=True, include_kyc=True)), 200

# Update user profile
@user_bp.route('/profile', methods=['PUT'])
@token_required
def update_user_profile():
    user = request.current_user
    data = request.get_json()
    
    changes = {}
    
    # Update first name
    if 'first_name' in data and data['first_name']:
        changes['first_name'] = user.first_name
        user.first_name = data['first_name']
    
    # Update last name
    if 'last_name' in data and data['last_name']:
        changes['last_name'] = user.last_name
        user.last_name = data['last_name']
    
    # Update phone number
    if 'phone_number' in data and data['phone_number']:
        phone_number = data['phone_number'].strip()
        
        # Validate phone format
        if not re.match(PHONE_REGEX, phone_number):
            return jsonify({'message': 'Invalid phone number format. Use international format (+254...)'}), 400
        
        # Check if phone already exists
        existing = User.query.filter(
            User.phone_number == phone_number,
            User.id != user.id
        ).first()
        
        if existing:
            return jsonify({'message': 'Phone number already registered'}), 400
        
        changes['phone_number'] = user.phone_number
        user.phone_number = phone_number
    
    # Update date of birth
    if 'date_of_birth' in data:
        try:
            dob = datetime.fromisoformat(data['date_of_birth'].replace('Z', '+00:00')).date()
            changes['date_of_birth'] = user.date_of_birth
            user.date_of_birth = dob
        except (ValueError, AttributeError):
            return jsonify({'message': 'Invalid date format. Use ISO format (YYYY-MM-DD)'}), 400
    
    # Update two-factor authentication setting
    if 'two_factor_enabled' in data:
        changes['two_factor_enabled'] = user.two_factor_enabled
        user.two_factor_enabled = bool(data['two_factor_enabled'])
    
    try:
        db.session.commit()
        
        # Log profile update
        if changes:
            AuditLog.log_user_action(
                actor_id=user.id,
                action='profile.update',
                resource_type='user',
                resource_id=user.id,
                old_values=changes,
                new_values={k: getattr(user, k) for k in changes.keys()},
                status='success'
            )
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Failed to update profile: {str(e)}'}), 500
    

# Change password
@user_bp.route('/change-password', methods=['PUT'])
@token_required
@otp_required('change_password')
def change_password(current_user):
    """Change password with OTP verification"""
    data = request.get_json()
    
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'message': 'Current password and new password are required'}), 400
    
    # Verify current password
    if not current_user.check_password(current_password):
        return jsonify({'message': 'Current password is incorrect'}), 400
    
    # Validate new password strength
    if len(new_password) < 6:
        return jsonify({'message': 'New password must be at least 6 characters'}), 400
    
    # Set new password
    current_user.set_password(new_password)
    
    try:
        db.session.commit()
        
        # Log password change
        from app.models import AuditLog
        AuditLog.log_user_action(
            actor_id=current_user.id,
            action='password.change',
            resource_type='user',
            resource_id=current_user.id,
            status='success'
        )
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Failed to change password: {str(e)}'}), 500

# Get KYC status
@user_bp.route('/kyc/status', methods=['GET'])
@token_required
def get_kyc_status():
    user = request.current_user
    
    kyc = KYCVerification.query.filter_by(user_id=user.id).first()
    
    if not kyc:
        return jsonify({
            'status': user.kyc_status.value,
            'submitted': False,
            'message': 'KYC not submitted'
        }), 200
    
    kyc_data = kyc.to_dict()
    kyc_data['is_expired'] = kyc.is_expired()
    
    return jsonify(kyc_data), 200

# Submit KYC documents
@user_bp.route('/kyc/submit', methods=['POST'])
@token_required
def submit_kyc():
    user = request.current_user
    
    # Check if already verified
    if user.kyc_status == KYCStatus.verified:
        return jsonify({'message': 'KYC already verified'}), 400
    
    # Check if pending
    if user.kyc_status == KYCStatus.pending:
        return jsonify({'message': 'KYC verification already pending'}), 400
    
    # Get form data
    document_type = request.form.get('document_type')
    document_number = request.form.get('document_number')
    
    if not document_type or not document_number:
        return jsonify({'message': 'Document type and number are required'}), 400
    
    # Get files
    front_doc = request.files.get('front_document')
    back_doc = request.files.get('back_document')
    selfie = request.files.get('selfie')
    
    if not front_doc:
        return jsonify({'message': 'Front document is required'}), 400
    
    # Submit KYC
    result = KYCService.submit_kyc(
        user_id=user.id,
        document_type=document_type,
        document_number=document_number,
        front_doc=front_doc,
        back_doc=back_doc,
        selfie=selfie
    )
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400

# Get payment methods
@user_bp.route('/payment-methods', methods=['GET'])
@token_required
@kyc_required
def get_payment_methods():
    user = request.current_user
    
    payment_methods = PaymentMethod.query.filter_by(
        user_id=user.id,
        is_active=True
    ).order_by(PaymentMethod.is_default.desc()).all()
    
    return jsonify({
        'payment_methods': [pm.to_dict() for pm in payment_methods]
    }), 200

# Add payment method
@user_bp.route('/payment-methods', methods=['POST'])
@token_required
@kyc_required
def add_payment_method():
    user = request.current_user
    data = request.get_json()
    
    provider = data.get('provider')
    account_reference = data.get('account_reference')
    account_name = data.get('account_name')
    
    if not provider or not account_reference:
        return jsonify({'message': 'Provider and account reference are required'}), 400
    
    # Validate provider
    try:
        provider_enum = PaymentProvider(provider)
    except ValueError:
        return jsonify({'message': 'Invalid provider'}), 400
    
    # Check if already exists
    existing = PaymentMethod.query.filter_by(
        user_id=user.id,
        provider=provider_enum,
        account_reference=account_reference
    ).first()
    
    if existing:
        return jsonify({'message': 'Payment method already exists'}), 400
    
    # Create new payment method
    payment_method = PaymentMethod(
        user_id=user.id,
        provider=provider_enum,
        account_reference=account_reference,
        account_name=account_name,
        is_default=data.get('is_default', False),
        provider_metadata=data.get('metadata')
    )
    
    # If setting as default, unset others
    if payment_method.is_default:
        PaymentMethod.query.filter_by(
            user_id=user.id,
            is_default=True
        ).update({'is_default': False})
    
    try:
        db.session.add(payment_method)
        db.session.commit()
        
        return jsonify({
            'message': 'Payment method added successfully',
            'payment_method': payment_method.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Failed to add payment method: {str(e)}'}), 500

# Delete payment method
@user_bp.route('/payment-methods/<int:payment_method_id>', methods=['DELETE'])
@token_required
def delete_payment_method(payment_method_id):
    user = request.current_user
    
    payment_method = PaymentMethod.query.filter_by(
        id=payment_method_id,
        user_id=user.id
    ).first_or_404()
    
    # Check if it's the default
    if payment_method.is_default:
        return jsonify({'message': 'Cannot delete default payment method'}), 400
    
    try:
        db.session.delete(payment_method)
        db.session.commit()
        
        return jsonify({'message': 'Payment method deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Failed to delete payment method: {str(e)}'}), 500

# Set default payment method
@user_bp.route('/payment-methods/<int:payment_method_id>/default', methods=['PUT'])
@token_required
def set_default_payment_method(payment_method_id):
    user = request.current_user
    
    payment_method = PaymentMethod.query.filter_by(
        id=payment_method_id,
        user_id=user.id
    ).first_or_404()
    
    try:
        # Unset all defaults
        PaymentMethod.query.filter_by(
            user_id=user.id,
            is_default=True
        ).update({'is_default': False})
        
        # Set new default
        payment_method.is_default = True
        db.session.commit()
        
        return jsonify({
            'message': 'Default payment method updated',
            'payment_method': payment_method.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Failed to update default payment method: {str(e)}'}), 500

# Verify payment method (for MPesa - send verification code)
@user_bp.route('/payment-methods/<int:payment_method_id>/verify', methods=['POST'])
@token_required
def verify_payment_method(payment_method_id):
    user = request.current_user
    
    payment_method = PaymentMethod.query.filter_by(
        id=payment_method_id,
        user_id=user.id
    ).first_or_404()
    
    data = request.get_json()
    verification_token = data.get('verification_token')
    
    if not verification_token:
        return jsonify({'message': 'Verification token required'}), 400
    
    # Verify the token (in real implementation, send SMS and verify)
    if payment_method.verify(verification_token):
        db.session.commit()
        return jsonify({'message': 'Payment method verified successfully'}), 200
    else:
        return jsonify({'message': 'Invalid verification token'}), 400

# Get transaction history
@user_bp.route('/transactions', methods=['GET'])
@token_required
def get_transaction_history():
    user = request.current_user
    
    from app.services.transaction_service import TransactionService
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    transaction_type = request.args.get('type')
    
    result = TransactionService.get_user_transactions(
        user_id=user.id,
        page=page,
        per_page=per_page,
        transaction_type=transaction_type
    )
    
    return jsonify(result), 200
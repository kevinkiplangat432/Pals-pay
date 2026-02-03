from flask import Blueprint, request, jsonify
from app.auth.decorators import token_required
from app.services.otp_service import OTPService

otp_bp = Blueprint('otp', __name__, url_prefix='/api/otp')


@otp_bp.route('/send', methods=['POST'])
@token_required
def send_otp(current_user):
    """Send OTP for operation verification"""
    data = request.get_json()
    
    operation_type = data.get('operation_type')
    metadata = data.get('metadata', {})
    
    if not operation_type:
        return jsonify({'message': 'Operation type is required'}), 400
    
    # Check if user is verified
    if not current_user.is_verified and operation_type != 'account_verification':
        return jsonify({'message': 'Account not verified'}), 403
    
    # Send OTP
    result = OTPService.send_otp_via_sms(
        user_id=current_user.id,
        operation_type=operation_type,
        metadata=metadata
    )
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@otp_bp.route('/verify', methods=['POST'])
@token_required
def verify_otp(current_user):
    """Verify OTP code"""
    data = request.get_json()
    
    otp_code = data.get('otp_code')
    operation_type = data.get('operation_type')
    
    if not otp_code or not operation_type:
        return jsonify({'message': 'OTP code and operation type are required'}), 400
    
    # Verify OTP
    result = OTPService.verify_user_otp(
        user_id=current_user.id,
        otp_code=otp_code,
        operation_type=operation_type
    )
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@otp_bp.route('/check-requirement', methods=['POST'])
@token_required
def check_otp_requirement(current_user):
    """Check if OTP is required for an operation"""
    data = request.get_json()
    
    operation_type = data.get('operation_type')
    amount = data.get('amount')
    
    if not operation_type:
        return jsonify({'message': 'Operation type is required'}), 400
    
    requires_otp = OTPService.is_otp_required_for_operation(
        operation_type=operation_type,
        amount=amount
    )
    
    return jsonify({
        'requires_otp': requires_otp,
        'operation_type': operation_type,
        'amount': amount
    }), 200
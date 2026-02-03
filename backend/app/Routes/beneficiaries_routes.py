from flask import Blueprint, request, jsonify
from ..extensions import db
from app.models import Beneficiary, User, Wallet
from app.auth.decorators import token_required, kyc_required, otp_required

beneficiaries_bp = Blueprint('beneficiaries', __name__, url_prefix='/api/beneficiaries')


# Add a new beneficiary (REQUIRES OTP)
@beneficiaries_bp.route('/', methods=['POST'])
@token_required
@kyc_required
@otp_required('add_beneficiary')
def create_beneficiary(current_user):
    """Add beneficiary with OTP verification"""
    user = request.current_user
    data = request.get_json()
    
    
# Get all beneficiaries for current user
@beneficiaries_bp.route('/', methods=['GET'])
@token_required
def get_beneficiaries():
    user = request.current_user
    
    # Get query parameters
    category = request.args.get('category')
    is_trusted = request.args.get('is_trusted', type=lambda v: v.lower() == 'true')
    
    query = Beneficiary.query.filter_by(user_id=user.id)
    
    if category:
        query = query.filter_by(category=category)
    
    if is_trusted is not None:
        query = query.filter_by(is_trusted=is_trusted)
    
    beneficiaries = query.order_by(Beneficiary.last_transfer_at.desc()).all()
    
    return jsonify({
        'beneficiaries': [b.to_dict(include_user=True) for b in beneficiaries],
        'count': len(beneficiaries)
    }), 200

# Add a new beneficiary
@beneficiaries_bp.route('/', methods=['POST'])
@token_required
@kyc_required
def create_beneficiary():
    user = request.current_user
    data = request.get_json()
    
    # Get beneficiary wallet ID or user ID
    beneficiary_wallet_id = data.get('beneficiary_wallet_id')
    beneficiary_user_id = data.get('beneficiary_user_id')
    
    if not beneficiary_wallet_id and not beneficiary_user_id:
        return jsonify({'message': 'Either beneficiary_wallet_id or beneficiary_user_id is required'}), 400
    
    # If user ID provided, get their wallet
    if beneficiary_user_id:
        beneficiary_wallet = Wallet.query.filter_by(user_id=beneficiary_user_id).first()
        if not beneficiary_wallet:
            return jsonify({'message': 'Beneficiary user not found or has no wallet'}), 404
        beneficiary_wallet_id = beneficiary_wallet.id
    
    # Check if beneficiary exists
    beneficiary_wallet = Wallet.query.get(beneficiary_wallet_id)
    if not beneficiary_wallet:
        return jsonify({'message': 'Beneficiary wallet not found'}), 404
    
    # Check if trying to add self as beneficiary
    if beneficiary_wallet.user_id == user.id:
        return jsonify({'message': 'Cannot add yourself as a beneficiary'}), 400
    
    # Check if beneficiary already exists
    existing = Beneficiary.query.filter_by(
        user_id=user.id,
        beneficiary_wallet_id=beneficiary_wallet_id
    ).first()
    
    if existing:
        return jsonify({'message': 'Beneficiary already exists'}), 400
    
    # Create new beneficiary
    beneficiary = Beneficiary(
        user_id=user.id,
        beneficiary_wallet_id=beneficiary_wallet_id,
        nickname=data.get('nickname'),
        category=data.get('category'),
        daily_limit=data.get('daily_limit'),
        is_trusted=data.get('is_trusted', False)
    )
    
    try:
        db.session.add(beneficiary)
        db.session.commit()
        
        return jsonify({
            'message': 'Beneficiary added successfully',
            'beneficiary': beneficiary.to_dict(include_user=True)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Failed to add beneficiary: {str(e)}'}), 500

# Update beneficiary
@beneficiaries_bp.route('/<int:beneficiary_id>', methods=['PUT'])
@token_required
def update_beneficiary(beneficiary_id):
    user = request.current_user
    beneficiary = Beneficiary.query.filter_by(
        id=beneficiary_id,
        user_id=user.id
    ).first_or_404()
    
    data = request.get_json()
    
    # Update fields if provided
    if 'nickname' in data:
        beneficiary.nickname = data['nickname']
    
    if 'category' in data:
        beneficiary.category = data['category']
    
    if 'daily_limit' in data:
        beneficiary.daily_limit = data['daily_limit']
    
    if 'is_trusted' in data:
        beneficiary.is_trusted = data['is_trusted']
    
    try:
        db.session.commit()
        
        return jsonify({
            'message': 'Beneficiary updated successfully',
            'beneficiary': beneficiary.to_dict(include_user=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Failed to update beneficiary: {str(e)}'}), 500

# Delete beneficiary
@beneficiaries_bp.route('/<int:beneficiary_id>', methods=['DELETE'])
@token_required
def delete_beneficiary(beneficiary_id):
    user = request.current_user
    beneficiary = Beneficiary.query.filter_by(
        id=beneficiary_id,
        user_id=user.id
    ).first_or_404()
    
    try:
        db.session.delete(beneficiary)
        db.session.commit()
        
        return jsonify({'message': 'Beneficiary deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Failed to delete beneficiary: {str(e)}'}), 500

# Search for users to add as beneficiaries
@beneficiaries_bp.route('/search', methods=['GET'])
@token_required
def search_users():
    user = request.current_user
    query = request.args.get('q', '').strip()
    
    if len(query) < 3:
        return jsonify({'message': 'Search query must be at least 3 characters'}), 400
    
    # Search by phone, email, username, or name
    users = User.query.filter(
        User.is_active == True,
        User.id != user.id,
        (
            (User.phone_number.ilike(f'%{query}%')) |
            (User.email.ilike(f'%{query}%')) |
            (User.username.ilike(f'%{query}%')) |
            (User.first_name.ilike(f'%{query}%')) |
            (User.last_name.ilike(f'%{query}%'))
        )
    ).limit(20).all()
    
    result = []
    for user_result in users:
        wallet = Wallet.query.filter_by(user_id=user_result.id).first()
        if wallet:
            result.append({
                'user_id': user_result.id,
                'username': user_result.username,
                'email': user_result.email,
                'phone_number': user_result.phone_number,
                'full_name': user_result.get_full_name(),
                'wallet_id': wallet.id,
                'is_already_beneficiary': Beneficiary.query.filter_by(
                    user_id=user.id,
                    beneficiary_wallet_id=wallet.id
                ).first() is not None
            })
    
    return jsonify({
        'users': result,
        'count': len(result)
    }), 200
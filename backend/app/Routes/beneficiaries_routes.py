from flask import Blueprint, request, jsonify
from sqlalchemy import func
from backend.extensions import db
from app.models import User, Beneficiary
from app.auth import token_required


beneficiaries_bp = Blueprint('beneficiaries_bp', __name__, url_prefix='/api/beneficiaries')


@beneficiaries_bp.route('/user/beneficiaries', methods=['GET'])
@token_required
def get_beneficiaries():
    user = request.current_user
    beneficiaries = Beneficiary.query.filter_by(user_id=user.id).all()
    return jsonify([b.to_dict() for b in beneficiaries]), 200

@beneficiaries_bp.route('/user/beneficiaries', methods=['POST'])
@token_required
def create_beneficiary():
    user = request.current_user
    data = request.get_json()

    beneficiary_id = data.get('beneficiary_id')
    nickname = data.get('nickname')

    if beneficiary_id is None:
        return jsonify({'message': 'beneficiary_id is required'}), 400
    
    if int(beneficiary_id) == user.id:
        return jsonify({'message': 'Cannot add yourself as a beneficiary'}), 400
    
    beneficiary_user = User.query.get(beneficiary_id)
    if not beneficiary_user:
        return jsonify({'message': 'Beneficiary user not found'}), 404

    beneficiary = Beneficiary(
        user_id=user.id,
        beneficiary_id=beneficiary_id,
        nickname=nickname

        )
    
    db.session.add(beneficiary)

    try:
        db.session.commit()
        return jsonify({'message': 'Beneficiary added successfully', 'beneficiary': beneficiary.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'An error occurred while adding beneficiary', 'error': str(e)}), 500

    
@beneficiaries_bp.route('/user/beneficiaries/<int:beneficiary_record_id>', methods=['PUT'])
@token_required
def update_beneficiary(beneficiary_record_id):
    
    user = request.current_user
    beneficiary = Beneficiary.query.filter_by(id=beneficiary_record_id, user_id=user.id).first()

    if not beneficiary:
        return jsonify({ 'error': 'Beneficiary not found' }), 404
    
    data = request.get_json()

    if 'nickname' in data:
        beneficiary.nickname = data['nickname']

    try:
        db.session.commit()
        return jsonify({'message': 'Beneficiary updated successfully', 'beneficiary': beneficiary.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'An error occurred while updating beneficiary', 'error': str(e)}), 500
    
@beneficiaries_bp.route('/user/beneficiaries/<int:beneficiary_record_id>', methods=['DELETE'])
@token_required
def delete_beneficiary(beneficiary_record_id):
    user = request.current_user
    beneficiary = Beneficiary.query.filter_by(id=beneficiary_id, user_id=user.id).first()
    if not beneficiary:
        return jsonify({ 'error': 'Beneficiary not found' }), 404

    db.session.delete(beneficiary)
    db.session.commit()

    return jsonify({'message': 'Beneficiary deleted successfully'}), 200
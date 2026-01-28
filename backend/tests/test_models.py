"""
Test Models
Simple tests to verify model functionality
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models import User, Wallet, Transaction, Beneficiary
from decimal import Decimal


def test_models():
    """Test all models"""
    app = create_app('testing')
    
    with app.app_context():
        # Create tables
        db.drop_all()
        db.create_all()
        
        print("Testing Models...\n")
        
        # Test User Model
        print("1. Testing User Model...")
        user1 = User(
            email='test@example.com',
            username='testuser',
            phone_number='+254700000000',
            first_name='Test',
            last_name='User'
        )
        user1.set_password('testpass123')
        db.session.add(user1)
        db.session.commit()
        
        # Verify password hashing
        assert user1.check_password('testpass123'), "Password check failed"
        assert not user1.check_password('wrongpass'), "Wrong password accepted"
        print("   ✓ User creation and password hashing works")
        print(f"   ✓ User representation: {user1}")
        
        # Test Wallet Model
        print("\n2. Testing Wallet Model...")
        wallet = Wallet(user_id=user1.id, balance=Decimal('100.50'))
        db.session.add(wallet)
        db.session.commit()
        
        assert wallet.balance == Decimal('100.50'), "Wallet balance incorrect"
        print(f"   ✓ Wallet created: {wallet}")
        
        # Test analytics
        analytics = wallet.get_analytics()
        assert analytics['current_balance'] == 100.50, "Analytics balance incorrect"
        print("   ✓ Wallet analytics working")
        
        # Test Transaction Model
        print("\n3. Testing Transaction Model...")
        
        # Create second user for transfers
        user2 = User(
            email='test2@example.com',
            username='testuser2',
            phone_number='+254700000001',
            first_name='Test2',
            last_name='User2'
        )
        user2.set_password('testpass123')
        db.session.add(user2)
        
        wallet2 = Wallet(user_id=user2.id, balance=Decimal('50.00'))
        db.session.add(wallet2)
        db.session.commit()
        
        # Test fee calculation
        fee = Transaction.calculate_fee(100)
        assert fee == Decimal('1.00'), "Fee calculation incorrect for $100"
        
        fee_min = Transaction.calculate_fee(10)
        assert fee_min == Decimal('0.50'), "Minimum fee not applied"
        print("   ✓ Fee calculation working")
        
        # Create transaction
        transaction = Transaction(
            sender_id=user1.id,
            receiver_id=user2.id,
            amount=Decimal('25.00'),
            transaction_type='transfer',
            status='completed',
            transaction_fee=Transaction.calculate_fee(25),
            description='Test transfer'
        )
        db.session.add(transaction)
        db.session.commit()
        
        print(f"   ✓ Transaction created: {transaction}")
        
        # Test to_dict with user details
        trans_dict = transaction.to_dict()
        assert 'sender_username' in trans_dict, "Sender username not in dict"
        assert trans_dict['sender_phone'] == user1.phone_number, "Phone number mismatch"
        print("   ✓ Transaction serialization working")
        
        # Test Beneficiary Model
        print("\n4. Testing Beneficiary Model...")
        beneficiary = Beneficiary(
            user_id=user1.id,
            beneficiary_id=user2.id,
            nickname='Friend'
        )
        db.session.add(beneficiary)
        db.session.commit()
        
        ben_dict = beneficiary.to_dict()
        assert ben_dict['nickname'] == 'Friend', "Nickname not saved"
        assert 'beneficiary' in ben_dict, "Beneficiary details missing"
        print(f"   ✓ Beneficiary created: {beneficiary}")
        print("   ✓ Beneficiary serialization working")
        
        # Test relationships
        print("\n5. Testing Relationships...")
        assert user1.wallet == wallet, "User-Wallet relationship broken"
        assert user1.sent_transactions.count() == 1, "Sent transactions relationship broken"
        assert user2.received_transactions.count() == 1, "Received transactions relationship broken"
        assert user1.beneficiaries.count() == 1, "Beneficiaries relationship broken"
        print("   ✓ All relationships working correctly")
        
        # Test cascade delete
        print("\n6. Testing Cascade Delete...")
        user_id = user1.id
        db.session.delete(user1)
        db.session.commit()
        
        # Verify wallet was deleted
        deleted_wallet = Wallet.query.filter_by(user_id=user_id).first()
        assert deleted_wallet is None, "Wallet not cascade deleted"
        print("   ✓ Cascade delete working")
        
        print("\n✅ All tests passed!\n")
        
        # Cleanup
        db.drop_all()


if __name__ == '__main__':
    test_models()

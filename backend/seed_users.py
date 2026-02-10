#!/usr/bin/env python3
from app import create_app, db
from app.models.user import User
from app.models.wallet import Wallet
from app.models.enums import KYCStatus
from werkzeug.security import generate_password_hash

app = create_app()

users_data = [
    {"username": "john_doe", "email": "john.doe@example.com", "first_name": "John", "last_name": "Doe", "phone": "+254712345001"},
    {"username": "jane_smith", "email": "jane.smith@example.com", "first_name": "Jane", "last_name": "Smith", "phone": "+254712345002"},
    {"username": "mike_wilson", "email": "mike.wilson@example.com", "first_name": "Mike", "last_name": "Wilson", "phone": "+254712345003"},
    {"username": "sarah_jones", "email": "sarah.jones@example.com", "first_name": "Sarah", "last_name": "Jones", "phone": "+254712345004"},
    {"username": "david_brown", "email": "david.brown@example.com", "first_name": "David", "last_name": "Brown", "phone": "+254712345005"},
    {"username": "emma_davis", "email": "emma.davis@example.com", "first_name": "Emma", "last_name": "Davis", "phone": "+254712345006"},
    {"username": "james_miller", "email": "james.miller@example.com", "first_name": "James", "last_name": "Miller", "phone": "+254712345007"},
    {"username": "olivia_garcia", "email": "olivia.garcia@example.com", "first_name": "Olivia", "last_name": "Garcia", "phone": "+254712345008"},
    {"username": "william_martinez", "email": "william.martinez@example.com", "first_name": "William", "last_name": "Martinez", "phone": "+254712345009"},
    {"username": "sophia_rodriguez", "email": "sophia.rodriguez@example.com", "first_name": "Sophia", "last_name": "Rodriguez", "phone": "+254712345010"},
]

with app.app_context():
    print("Seeding 10 users...")
    
    for user_data in users_data:
        existing = User.query.filter_by(email=user_data["email"]).first()
        if existing:
            print(f"User {user_data['email']} already exists, skipping...")
            continue
        
        try:
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                password_hash=generate_password_hash("Password123!"),
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                phone_number=user_data["phone"],
                is_active=True,
                is_verified=True,
                kyc_status=KYCStatus.verified,
                kyc_level=1
            )
            
            db.session.add(user)
            db.session.flush()
            
            wallet = Wallet(
                user_id=user.id,
                primary_currency="KES",
                balance=10000.00,
                available_balance=10000.00,
                locked_balance=0.00
            )
            
            db.session.add(wallet)
            db.session.commit()
            print(f"✓ Created user: {user.email} with wallet (10,000 KES)")
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error creating {user_data['email']}: {str(e)}")
    
    print("\n✓ Seeding complete!")

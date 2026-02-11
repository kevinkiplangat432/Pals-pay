#!/usr/bin/env python3
from app import create_app, db
from app.models.user import User
from app.models.enums import KYCStatus

app = create_app()

with app.app_context():
    email = input("Enter user email to update KYC: ")
    user = User.query.filter_by(email=email).first()
    
    if not user:
        print(f"✗ User with email {email} not found")
    else:
        user.kyc_status = KYCStatus.verified
        user.kyc_level = 1
        db.session.commit()
        print(f"✓ Updated {user.email} - KYC Status: verified, Level: 1")

#!/usr/bin/env python3
"""
Seed script to create initial admin user for production deployment
"""
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.enums import KYCStatus

def seed_admin():
    """Create admin user if it doesn't exist"""
    app = create_app(os.getenv('FLASK_ENV', 'production'))
    
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(email='kiplangatkevin335@gmail.com').first()
        
        if admin:
            print("✓ Admin user already exists")
            return
        
        # Create admin user
        admin = User(
            email='kiplangatkevin335@gmail.com',
            username='kevinkiplangat',
            first_name='Kevin',
            last_name='Kiplangat',
            phone_number='708374149',
            phone_country_code='+254',
            country_code='KE',
            region='east_africa',
            preferred_currency='KES',
            is_admin=True,
            is_active=True,
            is_verified=True,
            kyc_status=KYCStatus.verified,
            kyc_level=2
        )
        
        admin.set_password('bd2876qwac')
        
        db.session.add(admin)
        db.session.commit()
        
        print(f"✓ Admin user created successfully")
        print(f"  Email: {admin.email}")
        print(f"  Username: {admin.username}")
        print(f"  Wallet ID: {admin.wallet.id if admin.wallet else 'N/A'}")

if __name__ == '__main__':
    try:
        seed_admin()
    except Exception as e:
        print(f"✗ Error creating admin user: {str(e)}")
        sys.exit(1)

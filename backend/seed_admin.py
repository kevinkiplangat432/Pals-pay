#!/usr/bin/env python3
"""
Seed Admin User
Creates an admin user for accessing the admin dashboard
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models import User, Account, UserAccount, Wallet
from datetime import datetime, timezone

def seed_admin():
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("Creating Admin User")
        print("=" * 60)
        
        # Admin credentials
        admin_email = "admin@palspay.com"
        admin_password = "Admin@123"
        admin_name = "Admin"
        admin_phone = "+254700000000"
        
        # Check if admin already exists
        existing_admin = User.query.filter_by(email=admin_email).first()
        if existing_admin:
            print(f"\n✗ Admin user already exists: {admin_email}")
            print(f"  User ID: {existing_admin.id}")
            print(f"  Is Admin: {existing_admin.is_admin}")
            return
        
        try:
            # Create admin user
            print(f"\n1. Creating admin user...")
            admin_user = User(
                first_name=admin_name,
                last_name="User",
                email=admin_email,
                username="admin",
                phone_number=admin_phone,
                country_code="KE",
                region="east_africa",
                is_active=True,
                is_verified=True,
                is_admin=True,
                kyc_status="verified",
                kyc_level=3
            )
            admin_user.set_password(admin_password)
            db.session.add(admin_user)
            db.session.flush()
            print(f"   ✓ Admin user created (ID: {admin_user.id})")
            
            # Create account
            print(f"\n2. Creating admin account...")
            admin_account = Account(
                account_type="individual",
                legal_name=f"{admin_name} User",
                primary_email=admin_email,
                primary_phone=admin_phone,
                country_of_incorporation="KE",
                kyc_status="verified"
            )
            db.session.add(admin_account)
            db.session.flush()
            print(f"   ✓ Account created (ID: {admin_account.id})")
            
            # Link user to account
            print(f"\n3. Linking user to account...")
            user_account = UserAccount(
                user_id=admin_user.id,
                account_id=admin_account.id,
                role="owner",
                is_primary=True,
                is_active=True
            )
            db.session.add(user_account)
            print(f"   ✓ User linked to account")
            
            # Create wallet
            print(f"\n4. Creating admin wallet...")
            admin_wallet = Wallet(
                user_id=admin_user.id,
                primary_currency="KES"
            )
            db.session.add(admin_wallet)
            db.session.flush()
            print(f"   ✓ Wallet created (ID: {admin_wallet.id})")
            
            # Commit all changes
            db.session.commit()
            
            print("\n" + "=" * 60)
            print("✓ ADMIN USER CREATED SUCCESSFULLY!")
            print("=" * 60)
            print(f"\nLogin Credentials:")
            print(f"  Email:    {admin_email}")
            print(f"  Password: {admin_password}")
            print(f"\nUser Details:")
            print(f"  User ID:  {admin_user.id}")
            print(f"  Is Admin: {admin_user.is_admin}")
            print(f"  Verified: {admin_user.is_verified}")
            print(f"  KYC:      {admin_user.kyc_status}")
            print("\n" + "=" * 60)
            
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ Error creating admin user!")
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    seed_admin()

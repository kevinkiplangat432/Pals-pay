#!/usr/bin/env python3
from app import create_app, db
from app.models.user import User

app = create_app()

with app.app_context():
    email = input("Enter your email to become admin: ")
    user = User.query.filter_by(email=email).first()
    
    if not user:
        print(f"✗ User with email {email} not found")
    else:
        user.is_admin = True
        db.session.commit()
        print(f"✓ {user.email} is now an admin!")

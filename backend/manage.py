# manage.py - Complete version
import os
from flask_script import Manager, Shell
from flask_migrate import MigrateCommand
from app import create_app, db
from app.models import User, Wallet, Transaction, Beneficiary, KYCVerification, PaymentMethod, LedgerEntry, AuditLog

app = create_app(os.environ.get('FLASK_ENV', 'default'))
manager = Manager(app)

def make_shell_context():
    return dict(
        app=app,
        db=db,
        User=User,
        Wallet=Wallet,
        Transaction=Transaction,
        Beneficiary=Beneficiary,
        KYCVerification=KYCVerification,
        PaymentMethod=PaymentMethod,
        LedgerEntry=LedgerEntry,
        AuditLog=AuditLog
    )

manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)

@manager.command
def test():
    """Run unit tests"""
    import unittest
    tests = unittest.TestLoader().discover('app.tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

@manager.command
def create_admin():
    """Create an admin user"""
    from werkzeug.security import generate_password_hash
    
    email = input("Email: ")
    username = input("Username: ")
    phone_number = input("Phone number: ")
    first_name = input("First name: ")
    last_name = input("Last name: ")
    password = input("Password: ")
    
    admin = User(
        email=email,
        username=username,
        phone_number=phone_number,
        first_name=first_name,
        last_name=last_name,
        is_admin=True,
        is_active=True,
        is_verified=True
    )
    admin.set_password(password)
    
    db.session.add(admin)
    db.session.commit()
    
    print(f"Admin user {username} created successfully!")

@manager.command
def seed_data():
    """Seed the database with sample data"""
    from werkzeug.security import generate_password_hash
    from decimal import Decimal
    
    print("Seeding database...")
    
    # Create some users
    users = [
        User(
            email='user1@example.com',
            username='user1',
            phone_number='+254711111111',
            first_name='John',
            last_name='Doe',
            is_admin=False,
            is_active=True,
            is_verified=True
        ),
        User(
            email='user2@example.com',
            username='user2',
            phone_number='+254722222222',
            first_name='Jane',
            last_name='Smith',
            is_admin=False,
            is_active=True,
            is_verified=True
        ),
        User(
            email='user3@example.com',
            username='user3',
            phone_number='+254733333333',
            first_name='Bob',
            last_name='Johnson',
            is_admin=False,
            is_active=True,
            is_verified=True
        )
    ]
    
    for user in users:
        user.set_password('password123')
        db.session.add(user)
    
    db.session.commit()
    print("Sample users created!")
    
    # Create wallets with balances
    for i, user in enumerate(users):
        wallet = Wallet.query.filter_by(user_id=user.id).first()
        if wallet:
            wallet.balance = Decimal('10000') * (i + 1)
            wallet.available_balance = Decimal('10000') * (i + 1)
        else:
            wallet = Wallet(
                user_id=user.id,
                balance=Decimal('10000') * (i + 1),
                available_balance=Decimal('10000') * (i + 1)
            )
            db.session.add(wallet)
    
    db.session.commit()
    print("Wallets seeded with balances!")
    
    print("Database seeding completed!")

if __name__ == '__main__':
    manager.run()
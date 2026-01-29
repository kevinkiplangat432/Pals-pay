t #!/usr/bin/env python3
"""
Database management CLI
Usage: python manage.py [command]
Commands:
    init    - Create database tables
    drop    - Drop all tables
    reset   - Drop and recreate all tables
    seed    - Seed database with sample data
"""

import sys
from app import create_app
from database import init_db, drop_db, reset_db
from extensions import db
from models import User, Wallet


def seed_db():
    """Seed database with sample data"""
    app = create_app()
    with app.app_context():
        # Create sample users
        user1 = User(
            email='john@example.com',
            username='johndoe',
            phone_number='+254712345678',
            first_name='John',
            last_name='Doe'
        )
        user1.set_password('password123')
        
        user2 = User(
            email='jane@example.com',
            username='janedoe',
            phone_number='+254723456789',
            first_name='Jane',
            last_name='Doe'
        )
        user2.set_password('password123')
        
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        
        # Create wallets
        wallet1 = Wallet(user_id=user1.id, balance=1000.00)
        wallet2 = Wallet(user_id=user2.id, balance=500.00)
        
        db.session.add(wallet1)
        db.session.add(wallet2)
        db.session.commit()
        
        print("✓ Database seeded with sample data!")
        print(f"  User 1: {user1.username} ({user1.phone_number}) - Wallet: ${wallet1.balance}")
        print(f"  User 2: {user2.username} ({user2.phone_number}) - Wallet: ${wallet2.balance}")


def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    app = create_app()
    
    commands = {
        'init': lambda: init_db(app),
        'drop': lambda: drop_db(app),
        'reset': lambda: reset_db(app),
        'seed': seed_db
    }
    
    if command in commands:
        commands[command]()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()

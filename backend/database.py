"""
Database utilities and initialization
"""

from extensions import db
from models import User, Wallet, Transaction, Beneficiary


def init_db(app):
    """
    Initialize the database with the Flask app
    
    Args:
        app: Flask application instance
    """
    with app.app_context():
        db.create_all()
        print("✓ Database tables created successfully!")


def drop_db(app):
    """
    Drop all database tables
    
    Args:
        app: Flask application instance
    """
    with app.app_context():
        db.drop_all()
        print("✓ Database tables dropped successfully!")


def reset_db(app):
    """
    Reset database (drop and recreate all tables)
    
    Args:
        app: Flask application instance
    """
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("✓ Database reset successfully!")

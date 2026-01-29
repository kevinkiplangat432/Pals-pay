"""
Pulse-pay Backend Application
==============================

A Flask-based payment application API with PostgreSQL database.

Project Structure
-----------------
backend/
├── models/              # Database models (User, Wallet, Transaction, Beneficiary)
│   ├── __init__.py      # Model exports
│   ├── user.py          # User authentication and profiles
│   ├── wallet.py        # User wallet and balance management
│   ├── transaction.py   # Money transfer records
│   └── beneficiary.py   # Saved recipients
├── tests/               # Test suite
│   ├── __init__.py
│   └── test_models.py   # Model tests
├── app.py               # Flask application factory
├── config.py            # Application configuration
├── database.py          # Database utilities
├── extensions.py        # Flask extensions (SQLAlchemy)
├── manage.py            # CLI for database management
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
└── README.md            # Documentation

Database Models
---------------

User:
    - Identity: id, email, username, phone_number (client ID)
    - Profile: first_name, last_name
    - Security: password_hash
    - Permissions: is_admin, is_active
    - Methods: set_password(), check_password(), to_dict()

Wallet:
    - Fields: user_id, balance, currency
    - Methods: to_dict(), get_analytics()
    - One-to-one relationship with User

Transaction:
    - Fields: sender_id, receiver_id, amount, type, status, fee
    - Types: transfer, deposit, withdrawal
    - Status: pending, completed, failed
    - Methods: calculate_fee(), to_dict()
    - Fee: 1% of amount, minimum $0.50

Beneficiary:
    - Fields: user_id, beneficiary_id, nickname
    - Prevents duplicates and self-referencing
    - Methods: to_dict()

Key Features
------------
- PostgreSQL database with SQLAlchemy ORM
- Phone number as primary client identifier
- Secure password hashing with bcrypt
- Cascade deletes for data integrity
- Comprehensive analytics for wallets
- Transaction fee calculation
- Database indexes for performance
- JSON serialization for API responses

Quick Start
-----------
1. Set up virtual environment:
   python3 -m venv venv && source venv/bin/activate

2. Install dependencies:
   pip install -r requirements.txt

3. Initialize database:
   python manage.py init

4. Run application:
   python app.py

CLI Commands
------------
python manage.py init   - Create database tables
python manage.py drop   - Drop all tables
python manage.py reset  - Reset database
python manage.py seed   - Add sample data

Testing
-------
python tests/test_models.py

API Endpoints
-------------
GET  /          - API status
GET  /health    - Health check with database connection test

Database Configuration
---------------------
URL: postgresql://palsuser:palspassword@localhost:5432/pals_db

Environment Variables
--------------------
DATABASE_URL    - PostgreSQL connection string
SECRET_KEY      - Flask secret key
FLASK_ENV       - development, production, or testing

Author: Pulse-pay Development Team
License: MIT
"""

__version__ = '1.0.0'
__author__ = 'Pulse-pay Development Team'

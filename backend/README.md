# Pulse-pay Backend

A comprehensive Flask-based payment API with PostgreSQL database integration. This backend provides user authentication, wallet management, transaction processing, and beneficiary features for the Pulse-pay payment application.

---

## 📁 Project Structure

```
backend/
├── models/                  # Database models (SQLAlchemy ORM)
│   ├── __init__.py         # Model exports and package initialization
│   ├── user.py             # User authentication and profile model
│   ├── wallet.py           # Wallet and balance management model
│   ├── transaction.py      # Transaction recording model
│   └── beneficiary.py      # Saved recipients model
├── tests/                   # Test suite
│   ├── __init__.py         # Test package initialization
│   └── test_models.py      # Comprehensive model tests
├── __init__.py             # Backend package documentation
├── app.py                  # Flask application factory
├── config.py               # Application and database configuration
├── database.py             # Database utility functions
├── extensions.py           # Flask extensions (SQLAlchemy instance)
├── manage.py               # CLI for database management
├── validate.py             # Python syntax validation script
├── setup.sh                # Automated setup script
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules
├── CODE_REVIEW.md          # Code quality review summary
├── README.md               # This file
└── venv/                   # Virtual environment (not in git)
```

---

## 📄 Detailed File Descriptions

### Core Application Files

#### `app.py` - Flask Application Factory

The main application entry point using the application factory pattern.

**Key Features:**
- Creates and configures Flask application
- Initializes database connection with PostgreSQL
- Sets up CORS for cross-origin requests
- Auto-creates database tables on startup
- Registers API routes and blueprints
- Provides health check endpoint

**Routes:**
- `GET /` - Returns API status and information
- `GET /health` - Database connection health check

**Functions:**
- `create_app(config_name='development')` - Creates configured Flask app instance
  - Args: `config_name` - 'development', 'production', or 'testing'
  - Returns: Configured Flask application

**Usage:**
```python
from app import create_app

app = create_app('development')
app.run(debug=True)
```

**Command Line:**
```bash
python app.py  # Runs on http://localhost:5000
```

---

#### `config.py` - Application Configuration

Contains all configuration classes for different environments.

**Configuration Classes:**

**1. `Config` (Base Configuration)**
- `SQLALCHEMY_DATABASE_URI` - PostgreSQL connection string
- `SQLALCHEMY_TRACK_MODIFICATIONS` - Disabled for performance
- `SQLALCHEMY_ECHO` - SQL query logging (False by default)
- `SECRET_KEY` - Flask secret key for sessions
- `JSON_SORT_KEYS` - Disable JSON key sorting

**2. `DevelopmentConfig`**
- Inherits from `Config`
- `DEBUG = True` - Enable Flask debug mode
- `SQLALCHEMY_ECHO = True` - Log all SQL queries

**3. `ProductionConfig`**
- Inherits from `Config`
- `DEBUG = False` - Disable debug mode
- `SQLALCHEMY_ECHO = False` - No SQL logging

**4. `TestingConfig`**
- Inherits from `Config`
- `TESTING = True` - Enable testing mode
- Uses separate test database: `pals_db_test`

**Database URLs:**
- Development/Production: `postgresql://palsuser:palspassword@localhost:5432/pals_db`
- Testing: `postgresql://palsuser:palspassword@localhost:5432/pals_db_test`

**Usage:**
```python
from config import config

# Access specific config
dev_config = config['development']
prod_config = config['production']
```

---

#### `extensions.py` - Flask Extensions

Centralizes Flask extension initialization to avoid circular imports.

**Contents:**
- `db` - SQLAlchemy instance for database operations

**Why This File Exists:**
- Prevents circular import issues
- All models import `db` from here
- Single source of truth for database instance

**Usage:**
```python
from extensions import db

# In models
class User(db.Model):
    pass

# In app.py
db.init_app(app)
```

---

#### `database.py` - Database Utilities

Provides helper functions for database management.

**Functions:**

**1. `init_db(app)`**
- Creates all database tables
- Uses models registered with SQLAlchemy
- Prints success message

**2. `drop_db(app)`**
- Drops all database tables
- Warning: Deletes all data
- Prints confirmation message

**3. `reset_db(app)`**
- Drops all tables then recreates them
- Useful for development/testing
- Combines drop_db() and init_db()

**Usage:**
```python
from app import create_app
from database import init_db, drop_db, reset_db

app = create_app()

init_db(app)   # Create tables
drop_db(app)   # Drop all tables
reset_db(app)  # Reset database
```

---

#### `manage.py` - Database Management CLI

Command-line interface for database operations.

**Available Commands:**

**1. `init`** - Create database tables
```bash
python manage.py init
```
Creates all tables defined in models. Safe to run multiple times.

**2. `drop`** - Drop all tables
```bash
python manage.py drop
```
⚠️ Warning: Deletes all data permanently.

**3. `reset`** - Reset database
```bash
python manage.py reset
```
Drops and recreates all tables. Useful for development.

**4. `seed`** - Seed sample data
```bash
python manage.py seed
```
Creates two sample users with wallets:
- User 1: johndoe (+254712345678) - $1000
- User 2: janedoe (+254723456789) - $500

**Functions:**
- `seed_db()` - Creates sample users and wallets
- `main()` - CLI entry point

**Usage Example:**
```bash
# Fresh start
python manage.py reset
python manage.py seed
```

---

### Database Models (`models/` directory)

#### `models/__init__.py` - Model Package

Exports all models for easy importing throughout the application.

**Exports:**
- `User` - User model
- `Wallet` - Wallet model
- `Transaction` - Transaction model
- `Beneficiary` - Beneficiary model

**Usage:**
```python
# Instead of:
from models.user import User
from models.wallet import Wallet

# You can do:
from models import User, Wallet, Transaction, Beneficiary
```

---

#### `models/user.py` - User Model

Core user authentication and profile management model.

**Purpose:**
Handles user accounts with phone number as the primary client identifier.

**Database Table:** `users`

**Fields:**

**Identity Fields:**
- `id` (Integer, Primary Key) - Unique user ID
- `email` (String(120), Unique, Indexed) - User email address
- `username` (String(80), Unique, Indexed) - Username
- `phone_number` (String(20), Unique, Indexed) - **Client ID** 🔑

**Profile Fields:**
- `first_name` (String(50)) - User's first name
- `last_name` (String(50)) - User's last name

**Security:**
- `password_hash` (String(255)) - Hashed password (bcrypt)

**Permissions:**
- `is_admin` (Boolean, default=False) - Admin flag
- `is_active` (Boolean, default=True) - Account active status

**Timestamps:**
- `created_at` (DateTime, Indexed) - Account creation date
- `updated_at` (DateTime) - Last update timestamp

**Relationships:**
- `wallet` - One-to-one with Wallet (cascade delete)
- `sent_transactions` - All transactions sent by this user
- `received_transactions` - All transactions received by this user
- `beneficiaries` - Saved recipients for quick transfers

**Methods:**

**1. `set_password(password)`**
- Hashes and stores password securely
- Uses Werkzeug's `generate_password_hash()`
- Args: `password` (str) - Plain text password
- Returns: None

**2. `check_password(password)`**
- Validates login credentials
- Uses Werkzeug's `check_password_hash()`
- Args: `password` (str) - Plain text password to verify
- Returns: `bool` - True if password matches

**3. `to_dict(include_wallet=False)`**
- Serializes user data for API responses
- Args: `include_wallet` (bool) - Whether to include wallet data
- Returns: `dict` - User data including full_name

**Usage Example:**
```python
from models import User

# Create user
user = User(
    email='john@example.com',
    username='johndoe',
    phone_number='+254712345678',
    first_name='John',
    last_name='Doe'
)
user.set_password('secure_password')

# Verify password
if user.check_password('secure_password'):
    print("Login successful!")

# Get user data
user_data = user.to_dict(include_wallet=True)
```

---

#### `models/wallet.py` - Wallet Model

Manages user balances and funds with analytics capabilities.

**Purpose:**
One-to-one wallet for each user to store balance and track transactions.

**Database Table:** `wallets`

**Fields:**
- `id` (Integer, Primary Key) - Unique wallet ID
- `user_id` (Integer, Foreign Key, Unique) - Links to User
- `balance` (Numeric(10,2), default=0.00) - Current balance (uses Decimal for precision)
- `currency` (String(3), default='USD') - Currency code
- `created_at` (DateTime) - Wallet creation date
- `updated_at` (DateTime) - Last update timestamp

**Relationships:**
- `user` - Back reference to User model

**Methods:**

**1. `to_dict()`**
- Returns wallet data for API responses
- Converts Decimal balance to float
- Returns: `dict` - Wallet information

**2. `get_analytics()`**
- Calculates comprehensive wallet statistics
- Queries all completed transactions
- Returns: `dict` containing:
  - `current_balance` - Current wallet balance
  - `currency` - Currency code
  - `totals` - Dictionary with:
    - `sent` - Total amount sent in transfers
    - `received` - Total amount received
    - `deposited` - Total deposits made
    - `withdrawn` - Total withdrawals
  - `transaction_counts` - Dictionary with:
    - `transfers_sent` - Number of transfers sent
    - `transfers_received` - Number of transfers received
    - `deposits` - Number of deposits
    - `withdrawals` - Number of withdrawals
    - `total` - Total transaction count

**Usage Example:**
```python
from models import Wallet
from decimal import Decimal

# Create wallet
wallet = Wallet(user_id=1, balance=Decimal('100.50'))

# Get analytics
analytics = wallet.get_analytics()
print(f"Total sent: ${analytics['totals']['sent']}")
print(f"Transaction count: {analytics['transaction_counts']['total']}")
```

---

#### `models/transaction.py` - Transaction Model

Records all money movements including transfers, deposits, and withdrawals.

**Purpose:**
Complete audit trail of all financial transactions in the system.

**Database Table:** `transactions`

**Fields:**

**Participants:**
- `id` (Integer, Primary Key) - Unique transaction ID
- `sender_id` (Integer, Foreign Key, nullable) - User sending money
- `receiver_id` (Integer, Foreign Key, nullable) - User receiving money

**Transaction Details:**
- `amount` (Numeric(10,2)) - Transaction amount
- `transaction_type` (String(20), default='transfer') - Type: 'transfer', 'deposit', 'withdrawal'
- `status` (String(20), default='pending') - Status: 'pending', 'completed', 'failed'
- `transaction_fee` (Numeric(10,2), default=0.00) - Fee charged
- `reference` (String(100), Unique) - UUID-based transaction reference
- `description` (Text, nullable) - Optional transaction note

**Timestamps:**
- `created_at` (DateTime, Indexed) - Transaction creation time
- `completed_at` (DateTime, nullable) - Completion timestamp

**Constraints:**
- Amount must be positive (`amount > 0`)
- Type must be 'transfer', 'deposit', or 'withdrawal'
- Status must be 'pending', 'completed', or 'failed'

**Relationships:**
- `sender` - Reference to sender User
- `receiver` - Reference to receiver User

**Methods:**

**1. `calculate_fee(amount)` [Static Method]**
- Calculates transaction fee
- Formula: 1% of amount, minimum $0.50
- Args: `amount` (Decimal or float) - Transaction amount
- Returns: `Decimal` - Calculated fee

**2. `to_dict(include_users=True)`**
- Serializes transaction data for API responses
- Includes sender/receiver details if available
- Args: `include_users` (bool) - Whether to include user details
- Returns: `dict` - Transaction data with:
  - Basic transaction info
  - `sender_username`, `sender_phone`, `sender_name` (if sender exists)
  - `receiver_username`, `receiver_phone`, `receiver_name` (if receiver exists)

**Transaction Types:**
- **transfer** - User-to-user money transfer
- **deposit** - Money added to wallet
- **withdrawal** - Money withdrawn from wallet

**Transaction Status:**
- **pending** - Transaction initiated but not completed
- **completed** - Transaction successfully processed
- **failed** - Transaction failed (money not transferred)

**Usage Example:**
```python
from models import Transaction
from decimal import Decimal

# Calculate fee
fee = Transaction.calculate_fee(100)  # Returns Decimal('1.00')
fee_min = Transaction.calculate_fee(10)  # Returns Decimal('0.50')

# Create transaction
transaction = Transaction(
    sender_id=1,
    receiver_id=2,
    amount=Decimal('50.00'),
    transaction_type='transfer',
    transaction_fee=Transaction.calculate_fee(50),
    description='Payment for services'
)

# Get transaction data
trans_data = transaction.to_dict()
print(trans_data['sender_phone'])  # Phone number of sender
```

---

#### `models/beneficiary.py` - Beneficiary Model

Saves frequent recipients for quick and easy transfers.

**Purpose:**
Allows users to save contacts they frequently send money to.

**Database Table:** `beneficiaries`

**Fields:**
- `id` (Integer, Primary Key) - Unique beneficiary ID
- `user_id` (Integer, Foreign Key) - User who saved the beneficiary
- `beneficiary_id` (Integer, Foreign Key) - The saved user
- `nickname` (String(50), nullable) - Optional friendly name
- `created_at` (DateTime) - When beneficiary was saved

**Relationships:**
- `user` - Back reference to the user who saved this beneficiary
- `beneficiary_user` - Full User object of the beneficiary

**Constraints:**
- Unique constraint on (user_id, beneficiary_id) - Prevents duplicates
- Check constraint: user_id ≠ beneficiary_id - Prevents self-referencing

**Methods:**

**1. `to_dict()`**
- Returns beneficiary info with full user details
- Returns: `dict` containing:
  - Beneficiary record info (id, user_id, beneficiary_id, nickname)
  - `beneficiary` object with:
    - `username` - Beneficiary's username
    - `email` - Beneficiary's email
    - `phone_number` - Beneficiary's phone
    - `full_name` - Beneficiary's full name
    - `first_name` - First name
    - `last_name` - Last name

**Usage Example:**
```python
from models import Beneficiary

# Save beneficiary
ben = Beneficiary(
    user_id=1,
    beneficiary_id=2,
    nickname='Mom'
)

# Get beneficiary data
ben_data = ben.to_dict()
print(f"Nickname: {ben_data['nickname']}")
print(f"Phone: {ben_data['beneficiary']['phone_number']}")
```

---

### Testing & Validation

#### `tests/test_models.py` - Model Tests

Comprehensive test suite for all database models.

**Test Coverage:**

**1. User Model Tests**
- User creation
- Password hashing
- Password verification
- User representation

**2. Wallet Model Tests**
- Wallet creation
- Balance handling (Decimal precision)
- Analytics calculation

**3. Transaction Model Tests**
- Fee calculation (1%, min $0.50)
- Transaction creation
- User details in serialization

**4. Beneficiary Model Tests**
- Beneficiary creation
- Nickname handling
- Beneficiary details serialization

**5. Relationship Tests**
- User-Wallet one-to-one
- User-Transactions one-to-many
- User-Beneficiaries one-to-many

**6. Cascade Delete Tests**
- Verifies wallet is deleted when user is deleted
- Ensures data integrity

**Usage:**
```bash
python tests/test_models.py
```

**Expected Output:**
```
Testing Models...

1. Testing User Model...
   ✓ User creation and password hashing works
   ✓ User representation: <User testuser - +254700000000>

2. Testing Wallet Model...
   ✓ Wallet created: <Wallet user_id=1 balance=100.50 USD>
   ✓ Wallet analytics working

3. Testing Transaction Model...
   ✓ Fee calculation working
   ✓ Transaction created: <Transaction ... transfer 25.00 completed>
   ✓ Transaction serialization working

4. Testing Beneficiary Model...
   ✓ Beneficiary created: <Beneficiary user_id=1 beneficiary_id=2 (Friend)>
   ✓ Beneficiary serialization working

5. Testing Relationships...
   ✓ All relationships working correctly

6. Testing Cascade Delete...
   ✓ Cascade delete working

✅ All tests passed!
```

---

#### `validate.py` - Syntax Validation

Quick validation script to check Python file syntax.

**Purpose:**
Ensures all Python files have valid syntax before running.

**Files Checked:**
- app.py
- config.py
- database.py
- extensions.py
- manage.py
- All model files (user.py, wallet.py, transaction.py, beneficiary.py)

**Usage:**
```bash
python validate.py
```

**Output:**
```
Validating Python files...

✓ app.py
✓ config.py
✓ database.py
✓ extensions.py
✓ manage.py
✓ models/__init__.py
✓ models/user.py
✓ models/wallet.py
✓ models/transaction.py
✓ models/beneficiary.py

✅ All files have valid Python syntax!
```

---

### Setup & Configuration

#### `setup.sh` - Automated Setup Script

Bash script that automates the entire backend setup process.

**What It Does:**

1. **Checks PostgreSQL Installation**
   - Verifies psql command is available
   - Exits with helpful message if not found

2. **Starts PostgreSQL Service**
   - Checks if PostgreSQL is running
   - Starts it if not running

3. **Creates Databases**
   - Creates `palsuser` with password 'palspassword'
   - Creates `pals_db` database (main)
   - Creates `pals_db_test` database (testing)
   - Grants all privileges to palsuser

4. **Sets Up Python Environment**
   - Creates virtual environment if not exists
   - Activates virtual environment
   - Installs all dependencies from requirements.txt

5. **Initializes Database**
   - Runs `python manage.py init`
   - Creates all database tables

**Usage:**
```bash
chmod +x setup.sh
./setup.sh
```

**Output:**
```
🚀 Setting up Pulse-pay Backend...

✅ PostgreSQL is running

📊 Setting up database...
✅ Databases created

📦 Installing Python packages...
✅ Packages installed

🗄️  Initializing database tables...
✅ Database tables created successfully!

✅ Setup complete!

To start the application:
  1. source venv/bin/activate
  2. python app.py

Optional: Seed sample data with 'python manage.py seed'
```

---

#### `requirements.txt` - Python Dependencies

Lists all required Python packages with specific versions.

**Dependencies:**

| Package | Version | Purpose |
|---------|---------|---------|
| Flask | 3.0.0 | Web framework |
| Flask-SQLAlchemy | 3.1.1 | ORM for database operations |
| Flask-CORS | 4.0.0 | Cross-Origin Resource Sharing |
| psycopg2-binary | 2.9.9 | PostgreSQL database adapter |
| python-dotenv | 1.0.0 | Environment variable management |
| Werkzeug | 3.0.1 | WSGI utilities and security |

**Installation:**
```bash
pip install -r requirements.txt
```

---

#### `.env.example` - Environment Variables Template

Template file for environment configuration.

**Variables:**

```env
DATABASE_URL=postgresql://palsuser:palspassword@localhost:5432/pals_db
SECRET_KEY=your-secret-key-change-in-production
FLASK_APP=app.py
FLASK_ENV=development
```

**Setup:**
```bash
cp .env.example .env
# Edit .env with your actual values
```

**Security Note:** Never commit `.env` file to git (it's in .gitignore)

---

#### `.gitignore` - Git Ignore Rules

Specifies files and directories that Git should ignore.

**Ignored Items:**
- `venv/` - Virtual environment
- `__pycache__/` - Python bytecode cache
- `*.pyc`, `*.pyo`, `*.pyd` - Compiled Python files
- `*.egg`, `*.egg-info/` - Python package files
- `dist/`, `build/` - Build directories
- `.env` - Environment variables (contains secrets)
- `.vscode/`, `.idea/` - IDE settings
- `*.db`, `*.sqlite`, `*.sqlite3` - Database files
- `.DS_Store` - macOS system files

---

#### `__init__.py` - Package Documentation

Module-level documentation for the backend package.

**Contains:**
- Complete project overview
- Database model summaries
- Key features list
- Quick start guide
- CLI commands reference
- API endpoints documentation
- Database configuration details
- Environment variables list
- Version and author information

---

### Additional Documentation

#### `CODE_REVIEW.md` - Code Quality Review

Comprehensive code quality review document.

**Contents:**
- File structure overview
- Code quality checklist
- Best practices verification
- Database design summary
- Security features
- Features implemented
- Testing coverage
- Setup instructions
- Dependencies list

---

## 🔑 Key Features

### 1. **Phone Number as Client ID**
Every user is uniquely identified by their phone number, making transfers intuitive and secure.

### 2. **Secure Password Handling**
- Passwords are never stored in plain text
- Uses bcrypt hashing via Werkzeug
- Includes password verification methods

### 3. **Precise Money Handling**
- All monetary values use `Decimal` type
- Precision: 10 digits, 2 decimal places
- Prevents floating-point arithmetic errors

### 4. **Transaction Fee System**
- Automatic fee calculation: 1% of amount
- Minimum fee: $0.50
- Transparent fee display

### 5. **Comprehensive Analytics**
- Wallet analytics with totals by type
- Transaction counts and history
- Easy to extend for reports

### 6. **Data Integrity**
- Foreign key constraints
- Unique constraints prevent duplicates
- Cascade deletes maintain consistency
- Check constraints ensure validity

### 7. **Developer-Friendly**
- CLI tools for database management
- Automated setup script
- Comprehensive tests
- Well-documented code

---

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
cd backend
chmod +x setup.sh
./setup.sh
```

### Option 2: Manual Setup

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup PostgreSQL
sudo -u postgres psql << EOF
CREATE USER palsuser WITH PASSWORD 'palspassword';
CREATE DATABASE pals_db OWNER palsuser;
CREATE DATABASE pals_db_test OWNER palsuser;
GRANT ALL PRIVILEGES ON DATABASE pals_db TO palsuser;
GRANT ALL PRIVILEGES ON DATABASE pals_db_test TO palsuser;
EOF

# 4. Initialize database
python manage.py init

# 5. (Optional) Add sample data
python manage.py seed

# 6. Run application
python app.py
```

---

## 🗄️ Database Schema

### Entity Relationship Diagram

```
┌─────────────┐         ┌──────────────┐
│    User     │────1:1──│    Wallet    │
│             │         │              │
│ id (PK)     │         │ id (PK)      │
│ email       │         │ user_id (FK) │
│ username    │         │ balance      │
│ phone_number│         │ currency     │
│ password    │         └──────────────┘
│ ...         │
└─────┬───────┘
      │
      ├──1:N──────┐
      │           ▼
      │     ┌─────────────────┐
      │     │   Transaction   │
      │     │                 │
      │     │ id (PK)         │
      │     │ sender_id (FK)  │
      │     │ receiver_id (FK)│
      │     │ amount          │
      │     │ type            │
      │     │ status          │
      │     │ fee             │
      │     └─────────────────┘
      │
      └──1:N──────┐
                  ▼
            ┌──────────────┐
            │ Beneficiary  │
            │              │
            │ id (PK)      │
            │ user_id (FK) │
            │ beneficiary_ │
            │   id (FK)    │
            │ nickname     │
            └──────────────┘
```

---

## 📡 API Endpoints

### Current Endpoints

#### `GET /`
Returns API status and information.

**Response:**
```json
{
  "message": "Pulse-pay API",
  "status": "running",
  "database": "PostgreSQL"
}
```

#### `GET /health`
Tests database connection and returns health status.

**Response (Healthy):**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

**Response (Unhealthy):**
```json
{
  "status": "unhealthy",
  "error": "Error message here"
}
```

### Future Endpoints (To Be Implemented)

- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/users/me` - Get current user
- `GET /api/wallet` - Get user wallet
- `POST /api/transactions` - Create transaction
- `GET /api/transactions` - List transactions
- `GET /api/beneficiaries` - List beneficiaries
- `POST /api/beneficiaries` - Add beneficiary
- `DELETE /api/beneficiaries/:id` - Remove beneficiary

---

## 🛠️ Database Management Commands

### Initialize Database
```bash
python manage.py init
```
Creates all database tables. Safe to run multiple times.

### Reset Database
```bash
python manage.py reset
```
Drops and recreates all tables. ⚠️ Deletes all data.

### Seed Sample Data
```bash
python manage.py seed
```
Creates two sample users:
- **johndoe** (+254712345678) - $1,000 balance
- **janedoe** (+254723456789) - $500 balance

### Drop All Tables
```bash
python manage.py drop
```
⚠️ Warning: Permanently deletes all data.

---

## 🧪 Testing

### Run All Tests
```bash
python tests/test_models.py
```

### Validate Syntax
```bash
python validate.py
```

### Manual Testing with Python Shell
```bash
python
>>> from app import create_app
>>> from models import User, Wallet
>>> app = create_app()
>>> with app.app_context():
...     users = User.query.all()
...     print(users)
```

---

## 🔒 Security Considerations

### Passwords
- Never stored in plain text
- Hashed using Werkzeug's password hashing (bcrypt-based)
- Includes salt for additional security

### Database
- Parameterized queries via SQLAlchemy (prevents SQL injection)
- Foreign key constraints enforce referential integrity
- Indexes on sensitive fields for performance

### API
- CORS configured (customize in production)
- Secret key for session management
- Environment variables for sensitive data

### Production Checklist
- [ ] Change SECRET_KEY in .env
- [ ] Use strong database password
- [ ] Enable HTTPS
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Add authentication middleware
- [ ] Enable logging
- [ ] Use production WSGI server (gunicorn)

---

## 🐛 Troubleshooting

### Database Connection Issues

**Problem:** `psycopg2.OperationalError: connection refused`

**Solution:**
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Start PostgreSQL
sudo systemctl start postgresql

# Verify database exists
sudo -u postgres psql -l | grep pals_db
```

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'flask'`

**Solution:**
```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Permission Errors

**Problem:** `permission denied for database pals_db`

**Solution:**
```bash
sudo -u postgres psql << EOF
GRANT ALL PRIVILEGES ON DATABASE pals_db TO palsuser;
EOF
```

### Virtual Environment Issues

**Problem:** `command not found: python`

**Solution:**
```bash
# Use python3 explicitly
python3 -m venv venv
source venv/bin/activate
```

---

## 📚 Development Guidelines

### Code Style
- Follow PEP 8 guidelines
- Use meaningful variable names
- Add docstrings to all functions/classes
- Keep functions focused and small

### Commit Messages
```
type(scope): subject

body (optional)

footer (optional)
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example:
```
feat(models): add transaction fee calculation

Added static method to calculate 1% fee with $0.50 minimum
```

### Adding New Models

1. Create model file in `models/` directory
2. Import `db` from `extensions`
3. Define model class inheriting from `db.Model`
4. Add relationships if needed
5. Implement `to_dict()` method
6. Export in `models/__init__.py`
7. Run `python manage.py reset` to create tables

### Adding New Routes

1. Create a blueprints directory
2. Define blueprint in `blueprints/your_feature.py`
3. Register blueprint in `app.py`:
```python
from blueprints.your_feature import your_bp
app.register_blueprint(your_bp, url_prefix='/api/your-feature')
```

---

## 🌐 Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| DATABASE_URL | PostgreSQL connection string | `postgresql://palsuser:...` | Yes |
| SECRET_KEY | Flask secret key | `dev-secret-key-...` | Yes |
| FLASK_APP | Flask application file | `app.py` | No |
| FLASK_ENV | Environment mode | `development` | No |

---

## 📦 Production Deployment

### Using Gunicorn (Recommended)

```bash
# Install gunicorn
pip install gunicorn

# Run with 4 workers
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using systemd Service

Create `/etc/systemd/system/pulsepay.service`:

```ini
[Unit]
Description=Pulse-pay Flask Application
After=network.target postgresql.service

[Service]
User=www-data
WorkingDirectory=/path/to/backend
Environment="PATH=/path/to/backend/venv/bin"
ExecStart=/path/to/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable pulsepay
sudo systemctl start pulsepay
```

### Using Nginx as Reverse Proxy

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📄 License

MIT License - Feel free to use this project for learning or commercial purposes.

---

## 👥 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📞 Support

For issues, questions, or contributions:
- Create an issue on GitHub
- Check existing documentation
- Review the CODE_REVIEW.md file

---

## 🎯 Roadmap

- [ ] User authentication endpoints
- [ ] JWT token-based auth
- [ ] Transaction history API
- [ ] Beneficiary management endpoints
- [ ] Email notifications
- [ ] SMS notifications
- [ ] Transaction receipts
- [ ] Admin dashboard
- [ ] Rate limiting
- [ ] API documentation (Swagger)
- [ ] Docker containerization
- [ ] CI/CD pipeline

---

**Last Updated:** January 28, 2026  
**Version:** 1.0.0  
**Author:** Pulse-pay Development Team

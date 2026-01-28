#!/bin/bash
# Setup script for Pulse-pay backend

echo "🚀 Setting up Pulse-pay Backend..."
echo ""

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed. Please install it first:"
    echo "   sudo apt-get install postgresql postgresql-contrib"
    exit 1
fi

# Check if PostgreSQL is running
if ! sudo systemctl is-active --quiet postgresql; then
    echo "📦 Starting PostgreSQL..."
    sudo systemctl start postgresql
fi

echo "✅ PostgreSQL is running"
echo ""

# Create database and user
echo "📊 Setting up database..."
sudo -u postgres psql << EOF
-- Create user if not exists
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'palsuser') THEN
        CREATE USER palsuser WITH PASSWORD 'palspassword';
    END IF;
END
\$\$;

-- Create main database if not exists
SELECT 'CREATE DATABASE pals_db OWNER palsuser'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'pals_db')\gexec

-- Create test database if not exists
SELECT 'CREATE DATABASE pals_db_test OWNER palsuser'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'pals_db_test')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE pals_db TO palsuser;
GRANT ALL PRIVILEGES ON DATABASE pals_db_test TO palsuser;
EOF

echo "✅ Databases created"
echo ""

# Activate virtual environment and install packages
echo "📦 Installing Python packages..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

echo "✅ Packages installed"
echo ""

# Initialize database
echo "🗄️  Initializing database tables..."
python manage.py init

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo "  1. source venv/bin/activate"
echo "  2. python app.py"
echo ""
echo "Optional: Seed sample data with 'python manage.py seed'"

# Pulse-pay Backend

Flask API with PostgreSQL database for the Pulse-pay payment application.

## Setup

1. **Create virtual environment:**

```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Configure environment:**

```bash
cp .env.example .env
# Edit .env if needed
```

4. **Ensure PostgreSQL is running:**

```bash
sudo systemctl status postgresql
# If not running:
sudo systemctl start postgresql
```

5. **Initialize database:**

```bash
python manage.py init    # Create tables
python manage.py seed    # Add sample data (optional)
```

6. **Run the application:**

```bash
python app.py
```

The API will be available at `http://localhost:5000`

## Database Management

- `python manage.py init` - Create database tables
- `python manage.py drop` - Drop all tables
- `python manage.py reset` - Reset database (drop and recreate)
- `python manage.py seed` - Seed with sample data

## API Endpoints

- `GET /` - API status
- `GET /health` - Health check (tests DB connection)

## Database Connection

**URL:** `postgresql://palsuser:palspassword@localhost:5432/pals_db`

Make sure PostgreSQL is installed and the database/user exists.

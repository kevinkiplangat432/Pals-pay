FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies including PostgreSQL development files
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make scripts executable
RUN chmod +x build.sh seed_admin.py

# Expose port
EXPOSE 10000

# Run migrations and seed on startup, then start server
CMD flask db upgrade && python seed_admin.py && gunicorn run:app --bind 0.0.0.0:10000

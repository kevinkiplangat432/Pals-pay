#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Running database migrations..."
flask db upgrade

echo "Seeding admin user..."
python seed_admin.py

echo "Build completed successfully!"

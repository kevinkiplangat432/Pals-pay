"""
Flask extensions
Centralized initialization of Flask extensions
"""

from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()

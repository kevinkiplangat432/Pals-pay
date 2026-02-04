# app/__init__.py
from flask import Flask
from flask_cors import CORS
from .extensions import db, bcrypt, cors, migrate, jwt
from .models import *  # Import all models
from config import config
import os

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app, origins=app.config['CORS_ORIGINS'])
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # Register blueprints
    from .auth.routes import auth_bp
    from .Routes.admin_routes import admin_bp
    from .Routes.user_routes import user_bp
    from .Routes.wallet_routes import wallet_bp
    from .Routes.beneficiaries_routes import beneficiaries_bp
    from .Routes.otp_routes import otp_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(wallet_bp)
    app.register_blueprint(beneficiaries_bp)
    app.register_blueprint(otp_bp)
    
    # Create uploads directory
    uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'message': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'message': 'Internal server error'}, 500
    
    return app
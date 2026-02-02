from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
import uuid
from config import config
from .extensions import db, bcrypt, cors, migrate, jwt

def create_app(config_name='default'):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app, origins=app.config['CORS_ORIGINS'])
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # Create upload folder
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Configure logging
    if not app.debug:
        file_handler = RotatingFileHandler(
            'money_transfer.log',
            maxBytes=10240,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Money Transfer App startup')
    
    # Request ID middleware
    @app.before_request
    def assign_request_id():
        request.id = str(uuid.uuid4())
    
    # Register blueprints
    from app.auth.routes import auth_bp
    from app.Routes.admin_routes import admin_bp
    from app.Routes.beneficiaries_routes import beneficiaries_bp
    from app.Routes.user_routes import user_bp
    from app.Routes.wallet_routes import wallet_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(beneficiaries_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(wallet_bp)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Server Error: {error}')
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized access'}), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Forbidden'}), 403
    
    return app
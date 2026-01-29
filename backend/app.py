"""
Flask Application Factory
Creates and configures the Flask application with PostgreSQL database
"""

from flask import Flask
from flask_cors import CORS
from config import config
from extensions import db


def create_app(config_name='development'):
    """
    Application factory pattern
    
    Args:
        config_name (str): Configuration to use ('development', 'production', 'testing')
        
    Returns:
        Flask: Configured Flask application
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Register blueprints (add your routes here)
    # from routes import api_bp
    # app.register_blueprint(api_bp)
    
    # Create database tables
    with app.app_context():
        # Import models to ensure they're registered with SQLAlchemy
        from models import User, Wallet, Transaction, Beneficiary
        
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")
    
    @app.route('/')
    def index():
        return {
            'message': 'Pulse-pay API',
            'status': 'running',
            'database': 'PostgreSQL'
        }
    
    @app.route('/health')
    def health():
        """Health check endpoint"""
        try:
            # Test database connection
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            return {'status': 'healthy', 'database': 'connected'}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}, 500
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)

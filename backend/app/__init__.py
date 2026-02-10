from flask import Flask
from flask_cors import CORS
from .extensions import db, bcrypt,cors, migrate, jwt
from .models import *
from config import config
import os




def create_app(config_name='default'):
    app = Flask(__name__)
    
    app.config.from_object(config[config_name])
    
    db.init_app(app)
    bcrypt.init_app(app)
    
    cors.init_app(
    app,
    resources={
        r"/api/*": {
            "origins": "http://localhost:5173"
        }
    },
    supports_credentials=True
    )

    # cors.init_app(
    #     app, 
    #     origins=app.config.get('CORS_ORIGINS', '*'),
    #               methods=app.config.get('CORS_METHODS', ['GET', 'POST', 'PUT', 'DELETE']),
    #               allow_headers=app.config.get('CORS_HEADERS', ['Content-Type', 'Authorization']))
    

    migrate.init_app(app, db)
    jwt.init_app(app)
    
    from .auth.routes import auth_bp
    from .Routes.admin_routes import admin_bp
    from .Routes.user_routes import user_bp
    from .Routes.wallet_routes import wallet_bp
    from .Routes.beneficiaries_routes import beneficiaries_bp
    from .Routes.otp_routes import otp_bp
    from .Routes.payment_routes import payment_bp
    from .Routes.transfer_routes import transfer_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(wallet_bp)
    app.register_blueprint(beneficiaries_bp)
    app.register_blueprint(otp_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(transfer_bp)
    
    uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    
    # with app.app_context():
    #     db.create_all()
    
    @app.errorhandler(404)
    def not_found(error):
        return {'message': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'message': 'Internal server error'}, 500
    
    return app


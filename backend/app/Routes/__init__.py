from .admin_routes import admin_bp
from .beneficiaries_routes import beneficiaries_bp
from .otp_routes import otp_bp
from .user_routes import user_bp
from .wallet_routes import wallet_bp

__all__ = [
    'admin_bp',
    'beneficiaries_bp',
    'otp_bp',
    'user_bp',
    'wallet_bp'
]
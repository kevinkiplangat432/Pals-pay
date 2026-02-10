import os
from datetime import timedelta
from decimal import Decimal

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://palsuser:palspassword@localhost/pals_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    SUPPORTED_REGIONS = {
        'east_africa': {
            'name': 'East Africa',
            'countries': ['KE', 'TZ', 'UG', 'RW', 'BI'],
            'currencies': ['KES', 'TZS', 'UGX', 'RWF', 'BIF'],
            'default_currency': 'KES',
            'active': True
        },
        'west_africa': {
            'name': 'West Africa',
            'countries': ['NG', 'GH', 'CI', 'SN', 'ML'],
            'currencies': ['NGN', 'GHS', 'XOF', 'XOF', 'XOF'],
            'default_currency': 'NGN',
            'active': True
        },
        'southern_africa': {
            'name': 'Southern Africa',
            'countries': ['ZA', 'ZM', 'ZW', 'MW', 'BW'],
            'currencies': ['ZAR', 'ZMW', 'USD', 'MWK', 'BWP'],
            'default_currency': 'ZAR',
            'active': True
        },
        'europe': {
            'name': 'Europe',
            'countries': ['GB', 'DE', 'FR', 'IT', 'ES'],
            'currencies': ['GBP', 'EUR', 'EUR', 'EUR', 'EUR'],
            'default_currency': 'EUR',
            'active': True
        },
        'north_america': {
            'name': 'North America',
            'countries': ['US', 'CA'],
            'currencies': ['USD', 'CAD'],
            'default_currency': 'USD',
            'active': True
        }
    }
    
    PAYMENT_PROVIDERS = {
        'MPESA': {
            'active': True,
            'name': 'M-Pesa',
            'region': 'east_africa',
            'countries': ['KE'],
            'currencies': ['KES'],
            'type': 'mobile_money',
            'config': {
                'consumer_key': os.environ.get('DARAJA_CONSUMER_KEY', ''),
                'consumer_secret': os.environ.get('DARAJA_CONSUMER_SECRET', ''),
                'business_shortcode': os.environ.get('DARAJA_BUSINESS_SHORTCODE', '174379'),
                'passkey': os.environ.get('DARAJA_PASSKEY', ''),
                'callback_url': os.environ.get('MPESA_CALLBACK_URL', 'http://localhost:5000/api/v1/payments/mpesa-callback'),
                'environment': 'sandbox' if os.environ.get('FLASK_ENV') == 'development' else 'production'
            }
        },
        'AIRTEL_MONEY': {
            'active': True,
            'name': 'Airtel Money',
            'region': 'east_africa',
            'countries': ['KE', 'TZ', 'UG', 'RW'],
            'currencies': ['KES', 'TZS', 'UGX', 'RWF'],
            'type': 'mobile_money',
            'config': {}
        },
        'FLUTTERWAVE': {
            'active': True,
            'name': 'Flutterwave',
            'region': 'africa',
            'countries': ['NG', 'GH', 'KE', 'ZA', 'UG'],
            'currencies': ['NGN', 'GHS', 'KES', 'ZAR', 'UGX'],
            'type': 'payment_gateway',
            'config': {
                'public_key': os.environ.get('FLUTTERWAVE_PUBLIC_KEY', ''),
                'secret_key': os.environ.get('FLUTTERWAVE_SECRET_KEY', ''),
                'encryption_key': os.environ.get('FLUTTERWAVE_ENCRYPTION_KEY', '')
            }
        }
    }
    
    TRANSACTION_LIMITS = {
        'east_africa': {
            'min_transfer': Decimal('10.00'),
            'max_transfer': Decimal('250000.00'),
            'daily_limit': Decimal('500000.00'),
            'monthly_limit': Decimal('10000000.00')
        },
        'west_africa': {
            'min_transfer': Decimal('100.00'),
            'max_transfer': Decimal('2000000.00'),
            'daily_limit': Decimal('5000000.00'),
            'monthly_limit': Decimal('50000000.00')
        },
        'europe': {
            'min_transfer': Decimal('1.00'),
            'max_transfer': Decimal('10000.00'),
            'daily_limit': Decimal('50000.00'),
            'monthly_limit': Decimal('500000.00')
        }
    }
    
    FEE_STRUCTURE = {
        'local_transfer': {
            'percentage': Decimal('1.0'),
            'fixed': Decimal('10.00'),
            'max_fee': Decimal('5000.00'),
            'min_fee': Decimal('10.00')
        },
        'cross_region': {
            'percentage': Decimal('3.0'),
            'fixed': Decimal('100.00'),
            'max_fee': Decimal('10000.00'),
            'min_fee': Decimal('200.00')
        },
        'international': {
            'percentage': Decimal('5.0'),
            'fixed': Decimal('500.00'),
            'max_fee': Decimal('10000.00'),
            'min_fee': Decimal('1000.00')
        }
    }
    
    INTERNATIONAL_FEE_STRUCTURE = {
        'KE_NG': {
            'percentage': Decimal('4.5'),
            'fixed': Decimal('450.00'),
            'min_fee': Decimal('900.00')
        },
        'KE_GB': {
            'percentage': Decimal('5.0'),
            'fixed': Decimal('500.00'),
            'min_fee': Decimal('1000.00')
        },
        'KE_US': {
            'percentage': Decimal('5.0'),
            'fixed': Decimal('500.00'),
            'min_fee': Decimal('1000.00')
        },
        'default': {
            'percentage': Decimal('5.0'),
            'fixed': Decimal('500.00'),
            'min_fee': Decimal('1000.00')
        }
    }
    
    SETTLEMENT_TIMES = {
        'KE_NG': '1-2 business days',
        'KE_GB': '1-3 business days',
        'KE_US': '1-3 business days',
        'KE_ZA': 'Instant',
        'KE_TZ': 'Instant',
        'KE_UG': 'Instant',
        'KE_RW': 'Instant'
    }
    
    SETTLEMENT_REGIONS = {
        'east_africa_east_africa': 'Instant',
        'east_africa_west_africa': '1-2 business days',
        'east_africa_europe': '1-3 business days',
        'east_africa_north_america': '1-3 business days'
    }
    
    EXCHANGE_RATE_API = os.environ.get('EXCHANGE_RATE_API', 'https://v6.exchangerate-api.com/v6/YOUR_API_KEY/latest/')
    EXCHANGE_RATE_PROVIDER = os.environ.get('EXCHANGE_RATE_PROVIDER', 'exchangerate_api')
    
    EXCHANGERATE_API_KEY = os.environ.get('EXCHANGERATE_API_KEY', '')
    OPENEXCHANGERATES_API_KEY = os.environ.get('OPENEXCHANGERATES_API_KEY', '')
    CURRENCYLAYER_API_KEY = os.environ.get('CURRENCYLAYER_API_KEY', '')
    
    FALLBACK_EXCHANGE_RATES = {
        'KES_USD': Decimal('0.0065'),
        'USD_KES': Decimal('153.85'),
        'KES_EUR': Decimal('0.0060'),
        'EUR_KES': Decimal('166.67'),
        'KES_GBP': Decimal('0.0052'),
        'GBP_KES': Decimal('192.31'),
        'KES_NGN': Decimal('5.20'),
        'NGN_KES': Decimal('0.192'),
        'KES_GHS': Decimal('0.080'),
        'GHS_KES': Decimal('12.50'),
        'KES_ZAR': Decimal('0.123'),
        'ZAR_KES': Decimal('8.13'),
        'USD_EUR': Decimal('0.92'),
        'EUR_USD': Decimal('1.087'),
        'USD_GBP': Decimal('0.79'),
        'GBP_USD': Decimal('1.266'),
        'KES_TZS': Decimal('41.67'),
        'TZS_KES': Decimal('0.024'),
        'KES_UGX': Decimal('37.04'),
        'UGX_KES': Decimal('0.027'),
        'KES_RWF': Decimal('12.50'),
        'RWF_KES': Decimal('0.080'),
        'USD_NGN': Decimal('800.00'),
        'NGN_USD': Decimal('0.00125'),
        'USD_GHS': Decimal('12.50'),
        'GHS_USD': Decimal('0.080'),
        'USD_ZAR': Decimal('18.50'),
        'ZAR_USD': Decimal('0.054'),
        'USD_CAD': Decimal('1.35'),
        'CAD_USD': Decimal('0.741'),
        'USD_AUD': Decimal('1.50'),
        'AUD_USD': Decimal('0.667'),
        'USD_JPY': Decimal('145.00'),
        'JPY_USD': Decimal('0.0069'),
        'USD_CNY': Decimal('7.20'),
        'CNY_USD': Decimal('0.139'),
        'USD_INR': Decimal('83.00'),
        'INR_USD': Decimal('0.012'),
    }
    
    FX_FEE_PERCENTAGE = Decimal('1.0')
    FX_MIN_FEE = Decimal('10.00')
    FX_MAX_FEE = Decimal('500.00')
    
    HISTORICAL_RATE_API = os.environ.get('HISTORICAL_RATE_API', '')
    
    EXCHANGE_RATE_UPDATE_INTERVAL = 900
    
    QUOTE_EXPIRY = timedelta(minutes=15)
    INTERNATIONAL_QUOTE_EXPIRY = timedelta(minutes=30)
    
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')
    
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    EMAIL_CONFIG = {
        'enabled': os.environ.get('EMAIL_ENABLED', 'false').lower() == 'true',
        'api_key': os.environ.get('EMAIL_API_KEY', ''),
        'sender': os.environ.get('EMAIL_SENDER', 'noreply@palspay.com'),
        'endpoint': os.environ.get('EMAIL_ENDPOINT', 'https://api.mailgun.net/v3/your-domain/messages')
    }
    
    SMS_CONFIG = {
        'enabled': os.environ.get('SMS_ENABLED', 'false').lower() == 'true',
        'api_key': os.environ.get('SMS_API_KEY', ''),
        'sender_id': os.environ.get('SMS_SENDER_ID', 'PalsPay'),
        'endpoint': os.environ.get('SMS_ENDPOINT', 'https://api.africastalking.com/version1/messaging')
    }
    
    WHATSAPP_CONFIG = {
        'enabled': os.environ.get('WHATSAPP_ENABLED', 'false').lower() == 'true',
        'token': os.environ.get('WHATSAPP_TOKEN', ''),
        'phone_id': os.environ.get('WHATSAPP_PHONE_ID', '')
    }
    
    OTP_CONFIG = {
        'expiry_minutes': 10,
        'max_attempts': 3,
        'lockout_minutes': 15,
        'login_otp_required': os.environ.get('LOGIN_OTP_REQUIRED', 'false').lower() == 'true',
        'trusted_ip_expiry_days': 30
    }
    
    COMPLIANCE_CONFIG = {
        'sanctioned_countries': ['IR', 'KP', 'SY', 'CU', 'SD'],
        'high_risk_countries': ['AF', 'IQ', 'LY', 'SO', 'YE'],
        'enhanced_kyc_threshold': Decimal('100000.00'),
        'reporting_threshold': Decimal('1000000.00'),
        'suspicious_amount': Decimal('500000.00')
    }

class DevelopmentConfig(Config):
    DEBUG = True
    
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
class ProductionConfig(Config):
    DEBUG = False
    
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
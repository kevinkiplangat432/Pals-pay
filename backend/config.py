# config.py - Updated with international settings
import os
from datetime import timedelta
from decimal import Decimal

class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://palsuser:palspassword@localhost/pals_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # Supported Regions & Currencies
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
            'active': False
        },
        'southern_africa': {
            'name': 'Southern Africa',
            'countries': ['ZA', 'ZM', 'ZW', 'MW', 'BW'],
            'currencies': ['ZAR', 'ZMW', 'USD', 'MWK', 'BWP'],
            'default_currency': 'ZAR',
            'active': False
        },
        'europe': {
            'name': 'Europe',
            'countries': ['GB', 'DE', 'FR', 'IT', 'ES'],
            'currencies': ['GBP', 'EUR', 'EUR', 'EUR', 'EUR'],
            'default_currency': 'EUR',
            'active': False
        },
        'north_america': {
            'name': 'North America',
            'countries': ['US', 'CA'],
            'currencies': ['USD', 'CAD'],
            'default_currency': 'USD',
            'active': False
        }
    }
    
    # Payment Provider Configuration with Feature Flags
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
                'callback_url': os.environ.get('MPESA_CALLBACK_URL', 'http://localhost:5000/api/payments/mpesa-callback'),
                'environment': 'sandbox' if os.environ.get('FLASK_ENV') == 'development' else 'production'
            }
        },
        'AIRTEL_MONEY': {
            'active': False,
            'name': 'Airtel Money',
            'region': 'east_africa',
            'countries': ['KE', 'TZ', 'UG', 'RW'],
            'currencies': ['KES', 'TZS', 'UGX', 'RWF'],
            'type': 'mobile_money',
            'config': {}
        },
        'FLUTTERWAVE': {
            'active': False,
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
        },
        'WISE': {
            'active': False,
            'name': 'Wise',
            'region': 'global',
            'countries': ['*'],  # All countries
            'currencies': ['USD', 'EUR', 'GBP', 'KES', 'NGN', 'ZAR', 'GHS', 'INR'],
            'type': 'international_transfer',
            'config': {
                'api_key': os.environ.get('WISE_API_KEY', ''),
                'profile_id': os.environ.get('WISE_PROFILE_ID', ''),
                'environment': 'sandbox'
            }
        },
        'PAYPAL': {
            'active': False,
            'name': 'PayPal',
            'region': 'global',
            'countries': ['*'],
            'currencies': ['USD', 'EUR', 'GBP'],
            'type': 'digital_wallet',
            'config': {
                'client_id': os.environ.get('PAYPAL_CLIENT_ID', ''),
                'client_secret': os.environ.get('PAYPAL_CLIENT_SECRET', ''),
                'environment': 'sandbox'
            }
        }
    }
    
    # Transaction Limits by Region (in default currency)
    TRANSACTION_LIMITS = {
        'east_africa': {
            'min_transfer': Decimal('10.00'),
            'max_transfer': Decimal('100000.00'),
            'daily_limit': Decimal('500000.00'),
            'monthly_limit': Decimal('5000000.00')
        },
        'west_africa': {
            'min_transfer': Decimal('100.00'),  # ~$0.20
            'max_transfer': Decimal('2000000.00'),  # ~$4000
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
    
    # Fee Structure by Region and Type
    FEE_STRUCTURE = {
        'local_transfer': {
            'east_africa': {'percentage': Decimal('0.01'), 'fixed': Decimal('10.00'), 'max_fee': Decimal('5000.00')},
            'west_africa': {'percentage': Decimal('0.015'), 'fixed': Decimal('50.00'), 'max_fee': Decimal('5000.00')},
            'europe': {'percentage': Decimal('0.005'), 'fixed': Decimal('0.50'), 'max_fee': Decimal('50.00')}
        },
        'cross_region': {
            'percentage': Decimal('0.03'),  # 3%
            'fixed': Decimal('100.00'),
            'min_fee': Decimal('200.00')
        },
        'international': {
            'percentage': Decimal('0.05'),  # 5%
            'fixed': Decimal('500.00'),
            'min_fee': Decimal('1000.00')
        }
    }
    
    # Exchange Rate Configuration
    EXCHANGE_RATE_API = os.environ.get('EXCHANGE_RATE_API', 'https://api.exchangerate-api.com/v4/latest/KES')
    EXCHANGE_RATE_UPDATE_INTERVAL = 3600  # 1 hour in seconds
    
    # CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
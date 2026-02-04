# services/currency_service.py
import requests
from datetime import datetime, timedelta
from decimal import Decimal
from flask import current_app
from ..extensions import db
from ..models import ExchangeRate

class CurrencyService:
    """Service for handling currency conversions and exchange rates"""
    
    @staticmethod
    def get_exchange_rate(from_currency, to_currency):
        """Get exchange rate between two currencies"""
        if from_currency == to_currency:
            return Decimal('1.000000')
        
        # Check if rate exists in database and is recent
        rate = ExchangeRate.query.filter_by(
            base_currency=from_currency,
            target_currency=to_currency
        ).first()
        
        # If rate is older than 1 hour, update it
        if not rate or datetime.utcnow() - rate.last_updated > timedelta(hours=1):
            rate = CurrencyService.update_exchange_rate(from_currency, to_currency)
        
        return rate.rate if rate else Decimal('1.000000')
    
    @staticmethod
    def update_exchange_rate(base_currency, target_currency):
        """Update exchange rate from external API"""
        api_url = current_app.config.get('EXCHANGE_RATE_API', '')
        
        if not api_url:
            # Fallback to fixed rates for development
            fixed_rates = {
                ('KES', 'USD'): Decimal('0.0065'),
                ('KES', 'EUR'): Decimal('0.0060'),
                ('KES', 'GBP'): Decimal('0.0052'),
                ('USD', 'KES'): Decimal('153.85'),
                ('EUR', 'KES'): Decimal('166.67'),
                ('GBP', 'KES'): Decimal('192.31'),
            }
            
            rate_value = fixed_rates.get((base_currency, target_currency), Decimal('1.000000'))
        else:
            # Call external API
            try:
                response = requests.get(f"{api_url}?base={base_currency}")
                if response.status_code == 200:
                    data = response.json()
                    rate_value = Decimal(str(data['rates'].get(target_currency, 1)))
                else:
                    rate_value = Decimal('1.000000')
            except:
                rate_value = Decimal('1.000000')
        
        # Update or create rate in database
        rate = ExchangeRate.query.filter_by(
            base_currency=base_currency,
            target_currency=target_currency
        ).first()
        
        if not rate:
            rate = ExchangeRate(
                base_currency=base_currency,
                target_currency=target_currency,
                rate=rate_value,
                last_updated=datetime.utcnow()
            )
            db.session.add(rate)
        else:
            rate.rate = rate_value
            rate.last_updated = datetime.utcnow()
        
        db.session.commit()
        return rate
    
    @staticmethod
    def convert_amount(amount, from_currency, to_currency):
        """Convert amount from one currency to another"""
        rate = CurrencyService.get_exchange_rate(from_currency, to_currency)
        return amount * rate
    
    @staticmethod
    def format_currency(amount, currency_code):
        """Format currency amount with proper symbols"""
        currency_symbols = {
            'KES': 'KSh',
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'NGN': '₦',
            'GHS': 'GH₵',
            'ZAR': 'R',
            'UGX': 'USh',
            'TZS': 'TSh',
            'RWF': 'RF',
        }
        
        symbol = currency_symbols.get(currency_code, currency_code)
        return f"{symbol} {amount:,.2f}"
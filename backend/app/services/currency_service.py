import requests
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from flask import current_app
from ..extensions import db
from ..models import ExchangeRate, AuditLog

class CurrencyService:
    
    @staticmethod
    def get_exchange_rate(from_currency, to_currency):
        if from_currency == to_currency:
            return Decimal('1.000000')
        
        rate = ExchangeRate.query.filter_by(
            base_currency=from_currency,
            target_currency=to_currency
        ).first()
        
        if not rate or datetime.now(timezone.utc) - rate.last_updated > timedelta(minutes=15):
            rate = CurrencyService.update_exchange_rate(from_currency, to_currency)
        
        return rate.rate if rate else Decimal('1.000000')
    
    @staticmethod
    def update_exchange_rate(base_currency, target_currency):
        api_url = current_app.config.get('EXCHANGE_RATE_API')
        api_provider = current_app.config.get('EXCHANGE_RATE_PROVIDER', 'internal')
        
        try:
            if api_provider == 'exchangerate_api':
                rate_value = CurrencyService._fetch_from_exchangerate_api(base_currency, target_currency)
            elif api_provider == 'openexchangerates':
                rate_value = CurrencyService._fetch_from_openexchangerates(base_currency, target_currency)
            elif api_provider == 'currencylayer':
                rate_value = CurrencyService._fetch_from_currencylayer(base_currency, target_currency)
            else:
                rate_value = CurrencyService._get_fallback_rate(base_currency, target_currency)
            
            rate_value = Decimal(str(rate_value)).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
            
            rate = ExchangeRate.query.filter_by(
                base_currency=base_currency,
                target_currency=target_currency
            ).first()
            
            if not rate:
                rate = ExchangeRate(
                    base_currency=base_currency,
                    target_currency=target_currency,
                    rate=rate_value,
                    fx_provider=api_provider,
                    last_updated=datetime.now(timezone.utc)
                )
                db.session.add(rate)
            else:
                rate.rate = rate_value
                rate.fx_provider = api_provider
                rate.last_updated = datetime.now(timezone.utc)
            
            db.session.commit()
            
            AuditLog.log_system_action(
                action='exchange_rate.updated',
                resource_type='exchange_rate',
                resource_id=rate.id,
                metadata={
                    'base_currency': base_currency,
                    'target_currency': target_currency,
                    'rate': float(rate_value),
                    'provider': api_provider
                },
                status='success'
            )
            
            return rate
            
        except Exception as e:
            current_app.logger.error(f"Failed to update exchange rate {base_currency}/{target_currency}: {str(e)}")
            
            return CurrencyService._get_fallback_exchange_rate(base_currency, target_currency)
    
    @staticmethod
    def _fetch_from_exchangerate_api(base_currency, target_currency):
        api_key = current_app.config.get('EXCHANGERATE_API_KEY')
        url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base_currency}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data['result'] == 'success':
            return data['conversion_rates'].get(target_currency, 1)
        else:
            raise Exception(f"API error: {data.get('error-type', 'Unknown error')}")
    
    @staticmethod
    def _fetch_from_openexchangerates(base_currency, target_currency):
        api_key = current_app.config.get('OPENEXCHANGERATES_API_KEY')
        url = f"https://openexchangerates.org/api/latest.json?app_id={api_key}&base={base_currency}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return data['rates'].get(target_currency, 1)
    
    @staticmethod
    def _fetch_from_currencylayer(base_currency, target_currency):
        api_key = current_app.config.get('CURRENCYLAYER_API_KEY')
        url = f"http://apilayer.net/api/live?access_key={api_key}&currencies={target_currency}&source={base_currency}&format=1"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data['success']:
            rate_key = f"{base_currency}{target_currency}"
            return data['quotes'].get(rate_key, 1) / 100  # CurrencyLayer returns rates * 100
        else:
            raise Exception(f"API error: {data.get('error', {}).get('info', 'Unknown error')}")
    
    @staticmethod
    def _get_fallback_rate(base_currency, target_currency):
        fallback_rates = current_app.config.get('FALLBACK_EXCHANGE_RATES', {})
        
        pair_key = f"{base_currency}_{target_currency}"
        if pair_key in fallback_rates:
            return Decimal(str(fallback_rates[pair_key]))
        
        inverse_key = f"{target_currency}_{base_currency}"
        if inverse_key in fallback_rates:
            return Decimal('1') / Decimal(str(fallback_rates[inverse_key]))
        
        return CurrencyService._calculate_via_usd(base_currency, target_currency)
    
    @staticmethod
    def _calculate_via_usd(base_currency, target_currency):
        usd_rates = {
            'KES': Decimal('150.00'),
            'USD': Decimal('1.00'),
            'EUR': Decimal('0.92'),
            'GBP': Decimal('0.79'),
            'NGN': Decimal('800.00'),
            'GHS': Decimal('12.50'),
            'ZAR': Decimal('18.50'),
            'UGX': Decimal('3700.00'),
            'TZS': Decimal('2500.00'),
            'RWF': Decimal('1200.00'),
            'CAD': Decimal('1.35'),
            'AUD': Decimal('1.50'),
            'JPY': Decimal('145.00'),
            'CNY': Decimal('7.20'),
            'INR': Decimal('83.00')
        }
        
        base_to_usd = usd_rates.get(base_currency, Decimal('1.00'))
        target_to_usd = usd_rates.get(target_currency, Decimal('1.00'))
        
        if base_to_usd == Decimal('0') or target_to_usd == Decimal('0'):
            return Decimal('1.000000')
        
        return target_to_usd / base_to_usd
    
    @staticmethod
    def _get_fallback_exchange_rate(base_currency, target_currency):
        rate = ExchangeRate.query.filter_by(
            base_currency=base_currency,
            target_currency=target_currency
        ).first()
        
        if rate:
            return rate
        
        fallback_rate = CurrencyService._get_fallback_rate(base_currency, target_currency)
        
        rate = ExchangeRate(
            base_currency=base_currency,
            target_currency=target_currency,
            rate=fallback_rate,
            fx_provider='fallback',
            last_updated=datetime.now(timezone.utc)
        )
        
        db.session.add(rate)
        db.session.commit()
        
        return rate
    
    @staticmethod
    def convert_amount(amount, from_currency, to_currency, round_to=2):
        if from_currency == to_currency:
            return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        rate = CurrencyService.get_exchange_rate(from_currency, to_currency)
        converted = amount * rate
        
        if round_to == 0:
            return converted.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        elif round_to == 2:
            return converted.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        elif round_to == 4:
            return converted.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
        else:
            return converted.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def get_currency_symbol(currency_code):
        symbols = {
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
            'CAD': 'C$',
            'AUD': 'A$',
            'JPY': '¥',
            'CNY': '¥',
            'INR': '₹'
        }
        return symbols.get(currency_code, currency_code)
    
    @staticmethod
    def get_currency_name(currency_code):
        names = {
            'KES': 'Kenyan Shilling',
            'USD': 'US Dollar',
            'EUR': 'Euro',
            'GBP': 'British Pound',
            'NGN': 'Nigerian Naira',
            'GHS': 'Ghanaian Cedi',
            'ZAR': 'South African Rand',
            'UGX': 'Ugandan Shilling',
            'TZS': 'Tanzanian Shilling',
            'RWF': 'Rwandan Franc',
            'CAD': 'Canadian Dollar',
            'AUD': 'Australian Dollar',
            'JPY': 'Japanese Yen',
            'CNY': 'Chinese Yuan',
            'INR': 'Indian Rupee'
        }
        return names.get(currency_code, currency_code)
    
    @staticmethod
    def format_currency(amount, currency_code, include_symbol=True):
        symbol = CurrencyService.get_currency_symbol(currency_code) if include_symbol else ''
        
        if currency_code in ['JPY', 'KRW', 'VND']:
            formatted = f"{amount:,.0f}"
        else:
            formatted = f"{amount:,.2f}"
        
        return f"{symbol} {formatted}".strip()
    
    @staticmethod
    def get_all_rates(base_currency='USD'):
        rates = ExchangeRate.query.filter_by(base_currency=base_currency).all()
        
        if not rates or datetime.now(timezone.utc) - rates[0].last_updated > timedelta(hours=1):
            CurrencyService.update_all_rates(base_currency)
            rates = ExchangeRate.query.filter_by(base_currency=base_currency).all()
        
        result = {}
        for rate in rates:
            result[rate.target_currency] = {
                'rate': float(rate.rate),
                'last_updated': rate.last_updated.isoformat() if rate.last_updated else None,
                'provider': rate.fx_provider
            }
        
        return result
    
    @staticmethod
    def update_all_rates(base_currency='USD'):
        supported_currencies = ['KES', 'USD', 'EUR', 'GBP', 'NGN', 'GHS', 'ZAR', 'UGX', 'TZS', 'RWF']
        
        for target_currency in supported_currencies:
            if target_currency != base_currency:
                try:
                    CurrencyService.update_exchange_rate(base_currency, target_currency)
                except Exception as e:
                    current_app.logger.error(f"Failed to update rate for {base_currency}/{target_currency}: {str(e)}")
    
    @staticmethod
    def calculate_fx_fee(amount, from_currency, to_currency):
        if from_currency == to_currency:
            return Decimal('0.00')
        
        fx_fee_percentage = current_app.config.get('FX_FEE_PERCENTAGE', Decimal('1.0'))
        fx_min_fee = current_app.config.get('FX_MIN_FEE', Decimal('10.00'))
        fx_max_fee = current_app.config.get('FX_MAX_FEE', Decimal('500.00'))
        
        fee = amount * (fx_fee_percentage / Decimal('100'))
        fee = max(fee, fx_min_fee)
        fee = min(fee, fx_max_fee)
        
        return fee.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def get_historical_rate(base_currency, target_currency, date):
        historical_api = current_app.config.get('HISTORICAL_RATE_API')
        
        if not historical_api:
            return CurrencyService.get_exchange_rate(base_currency, target_currency)
        
        try:
            date_str = date.strftime('%Y-%m-%d')
            
            if current_app.config.get('EXCHANGE_RATE_PROVIDER') == 'exchangerate_api':
                api_key = current_app.config.get('EXCHANGERATE_API_KEY')
                url = f"https://v6.exchangerate-api.com/v6/{api_key}/history/{base_currency}/{date_str}"
                
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                if data['result'] == 'success':
                    return Decimal(str(data['conversion_rates'].get(target_currency, 1)))
            
            return CurrencyService.get_exchange_rate(base_currency, target_currency)
            
        except Exception as e:
            current_app.logger.error(f"Failed to get historical rate: {str(e)}")
            return CurrencyService.get_exchange_rate(base_currency, target_currency)
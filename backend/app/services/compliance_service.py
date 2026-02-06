# services/compliance_service.py
from decimal import Decimal
from flask import current_app
from .region_service import RegionService

class ComplianceService:
    """Service for handling regulatory compliance checks"""
    
    @staticmethod
    def check_cross_border_transfer(sender_country, receiver_country, amount):
        """Check if cross-border transfer is allowed"""
        
        # Check if both countries are supported
        if not RegionService.is_country_supported(sender_country):
            return {'allowed': False, 'reason': f'Sender country {sender_country} not supported'}
        
        if not RegionService.is_country_supported(receiver_country):
            return {'allowed': False, 'reason': f'Receiver country {receiver_country} not supported'}
        
        # Check if cross-border transfers are enabled between these countries
        cross_border_rules = current_app.config.get('CROSS_BORDER_RULES', {})
        
        rule_key = f"{sender_country}_{receiver_country}"
        if rule_key in cross_border_rules:
            rule = cross_border_rules[rule_key]
            if not rule.get('enabled', False):
                return {'allowed': False, 'reason': rule.get('message', 'Cross-border transfers not available')}
            
            # Check amount limits
            max_amount = Decimal(str(rule.get('max_amount', 0)))
            if amount > max_amount:
                return {'allowed': False, 'reason': f'Amount exceeds maximum for this route: {max_amount}'}
        
        # Check sanctions
        sanctioned_countries = current_app.config.get('SANCTIONED_COUNTRIES', [])
        if receiver_country in sanctioned_countries:
            return {'allowed': False, 'reason': 'Transfers to this country are restricted'}
        
        return {'allowed': True, 'reason': 'OK'}
    
    @staticmethod
    def check_transaction_limit(user, amount, transaction_type='transfer'):
        """Check transaction limits based on user's KYC level"""
        
        limits_by_kyc_level = {
            0: {'daily': Decimal('5000.00'), 'monthly': Decimal('20000.00')},  # Basic
            1: {'daily': Decimal('50000.00'), 'monthly': Decimal('500000.00')},  # Verified
            2: {'daily': Decimal('500000.00'), 'monthly': Decimal('5000000.00')},  # Enhanced
        }
        
        user_limits = limits_by_kyc_level.get(user.kyc_level, limits_by_kyc_level[0])
        
        # TODO: Check actual daily/monthly usage from database
        # For now, just check against limits
        if amount > user_limits['daily']:
            return {'allowed': False, 'reason': 'Exceeds daily limit for your KYC level'}
        
        return {'allowed': True, 'reason': 'OK'}
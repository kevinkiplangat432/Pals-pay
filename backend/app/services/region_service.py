# services/region_service.py
from flask import current_app
from ..extensions import db

class RegionService:
    """Service for handling region-based operations"""
    
    @staticmethod
    def get_region_by_country(country_code):
        """Get region for a country code"""
        config = current_app.config['SUPPORTED_REGIONS']
        
        for region_key, region_data in config.items():
            if country_code in region_data.get('countries', []):
                return region_key
        
        # Default to first active region or east_africa
        for region_key, region_data in config.items():
            if region_data.get('active', False):
                return region_key
        
        return 'east_africa'
    
    @staticmethod
    def get_region_config(region_key):
        """Get configuration for a region"""
        return current_app.config['SUPPORTED_REGIONS'].get(region_key, {})
    
    @staticmethod
    def get_active_regions():
        """Get all active regions"""
        config = current_app.config['SUPPORTED_REGIONS']
        return {k: v for k, v in config.items() if v.get('active', False)}
    
    @staticmethod
    def is_country_supported(country_code):
        """Check if country is supported"""
        config = current_app.config['SUPPORTED_REGIONS']
        
        for region_data in config.values():
            if country_code in region_data.get('countries', []):
                return True
        return False
    
    @staticmethod
    def get_supported_countries():
        """Get all supported countries"""
        config = current_app.config['SUPPORTED_REGIONS']
        countries = []
        
        for region_data in config.values():
            countries.extend(region_data.get('countries', []))
        
        return list(set(countries))
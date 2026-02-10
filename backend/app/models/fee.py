from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.dialects.postgresql import JSONB
from ..extensions import db


class Fee(db.Model):
    __tablename__ = 'fees'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Fee configuration
    fee_type = db.Column(db.String(50), nullable=False, index=True)  # 'transfer_fee', 'withdrawal_fee', 'fx_fee'
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Applicability
    applies_to = db.Column(db.JSON, default=[], nullable=False)  # ['transfer', 'cross_border', 'withdrawal']
    min_amount = db.Column(db.Numeric(12, 2), nullable=True)
    max_amount = db.Column(db.Numeric(12, 2), nullable=True)
    
    # Rate structure
    calculation_type = db.Column(db.String(20), nullable=False, default='percentage')  # 'percentage', 'flat', 'tiered'
    rate = db.Column(db.Numeric(10, 6), nullable=True)  # Percentage or flat amount
    currency = db.Column(db.String(3), default='KES', nullable=False)
    
    # Tiered rates (for tiered calculation)
    tiers = db.Column(JSONB, nullable=True)  # [{'min': 0, 'max': 1000, 'rate': 0.01}, ...]
    
    # Caps
    min_fee = db.Column(db.Numeric(12, 2), nullable=True)
    max_fee = db.Column(db.Numeric(12, 2), nullable=True)
    
    # Country-specific
    source_countries = db.Column(JSONB, default=[], nullable=False)
    destination_countries = db.Column(JSONB, default=[], nullable=False)
    
    # Timing
    effective_from = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    effective_to = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    
    # Metadata
    meta_data = db.Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=db.func.now(), nullable=True)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_fees_type_active', 'fee_type', 'is_active'),
        db.Index('idx_fees_effective', 'effective_from', 'effective_to'),
        db.Index('idx_fees_countries', 'source_countries', 'destination_countries', postgresql_using='gin'),
    )
    
    def calculate(self, amount, source_country=None, destination_country=None):
        """Calculate fee for given amount and context"""
        amount = Decimal(str(amount))
        
        # Check if fee applies to this transaction
        if not self._applies_to_context(source_country, destination_country):
            return Decimal('0.00')
        
        # Check amount range
        if self.min_amount and amount < self.min_amount:
            return Decimal('0.00')
        if self.max_amount and amount > self.max_amount:
            return Decimal('0.00')
        
        # Calculate based on type
        if self.calculation_type == 'percentage':
            fee = amount * (self.rate / Decimal('100'))
        elif self.calculation_type == 'flat':
            fee = self.rate
        elif self.calculation_type == 'tiered' and self.tiers:
            fee = self._calculate_tiered_fee(amount)
        else:
            fee = Decimal('0.00')
        
        # Apply caps
        if self.min_fee and fee < self.min_fee:
            fee = self.min_fee
        if self.max_fee and fee > self.max_fee:
            fee = self.max_fee
        
        return fee.quantize(Decimal('0.01'))
    
    def _applies_to_context(self, source_country, destination_country):
        """Check if fee applies to given context"""
        # Check countries
        if source_country and self.source_countries:
            if source_country not in self.source_countries:
                return False
        
        if destination_country and self.destination_countries:
            if destination_country not in self.destination_countries:
                return False
        
        # Check effective dates
        now = datetime.now(timezone.utc)
        if now < self.effective_from:
            return False
        if self.effective_to and now > self.effective_to:
            return False
        
        return True
    
    def _calculate_tiered_fee(self, amount):
        """Calculate tiered fee"""
        fee = Decimal('0.00')
        remaining = amount
        
        for tier in sorted(self.tiers, key=lambda x: x['min']):
            tier_min = Decimal(str(tier['min']))
            tier_max = Decimal(str(tier['max'])) if tier['max'] is not None else Decimal('Infinity')
            tier_rate = Decimal(str(tier['rate'])) / Decimal('100')
            
            if remaining <= 0:
                break
            
            if amount > tier_min:
                tier_amount = min(remaining, tier_max - tier_min)
                fee += tier_amount * tier_rate
                remaining -= tier_amount
        
        return fee
    
    def to_dict(self):
        return {
            'id': self.id,
            'fee_type': self.fee_type,
            'name': self.name,
            'description': self.description,
            'applies_to': self.applies_to,
            'min_amount': float(self.min_amount) if self.min_amount else None,
            'max_amount': float(self.max_amount) if self.max_amount else None,
            'calculation_type': self.calculation_type,
            'rate': float(self.rate) if self.rate else None,
            'currency': self.currency,
            'tiers': self.tiers,
            'min_fee': float(self.min_fee) if self.min_fee else None,
            'max_fee': float(self.max_fee) if self.max_fee else None,
            'source_countries': self.source_countries,
            'destination_countries': self.destination_countries,
            'effective_from': self.effective_from.isoformat() if self.effective_from else None,
            'effective_to': self.effective_to.isoformat() if self.effective_to else None,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Fee {self.name} ({self.fee_type})>'
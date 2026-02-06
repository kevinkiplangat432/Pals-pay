from datetime import datetime, timezone
from ..extensions import db

class ExchangeRate(db.Model):
    __tablename__ = 'exchange_rates'
    
    id = db.Column(db.Integer, primary_key=True)
    base_currency = db.Column(db.String(3), nullable=False, index=True)  # KES, USD, etc.
    target_currency = db.Column(db.String(3), nullable=False, index=True)
    rate = db.Column(db.Numeric(10, 6), nullable=False)  # 1 base = X target
    last_updated = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    
    # Indexes
    __table_args__ = (
        db.UniqueConstraint('base_currency', 'target_currency', name='unique_currency_pair'),
        db.Index('idx_exchange_rate_currency', 'base_currency', 'target_currency'),
        db.Index('idx_exchange_rate_updated', 'last_updated'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'base_currency': self.base_currency,
            'target_currency': self.target_currency,
            'rate': float(self.rate),
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
    
    def __repr__(self):
        return f'<ExchangeRate {self.base_currency}/{self.target_currency}={self.rate}>'
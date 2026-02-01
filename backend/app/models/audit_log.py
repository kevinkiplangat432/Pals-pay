"""
Audit Log Model - Tracks all system actions for security and analytics
"""
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import JSONB
from extensions import db


class AuditLog(db.Model):
    """
    Audit log model for tracking all system actions
    Critical for security, fraud detection, and AI analytics
    """
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Actor information
    actor_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id', ondelete='SET NULL'), 
        nullable=True,
        index=True
    )
    actor_type = db.Column(db.String(20), nullable=True)  # 'user', 'admin', 'system', 'api'
    actor_ip = db.Column(db.String(45), nullable=True)  # Supports IPv6
    user_agent = db.Column(db.Text, nullable=True)
    
    # Action details
    action = db.Column(db.String(100), nullable=False, index=True)
    resource_type = db.Column(db.String(50), nullable=False, index=True)  # 'user', 'transaction', 'wallet', etc.
    resource_id = db.Column(db.Integer, nullable=True, index=True)
    
    # Changes
    old_values = db.Column(JSONB, nullable=True)
    new_values = db.Column(JSONB, nullable=True)
    
    # Request context
    request_id = db.Column(db.String(100), nullable=True, index=True)
    endpoint = db.Column(db.String(200), nullable=True)
    http_method = db.Column(db.String(10), nullable=True)
    
    
    # Status
    status = db.Column(db.String(20), nullable=False, default='success')  # 'success', 'failed'
    error_message = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    
    # Indexes for fast analytics
    __table_args__ = (
        db.Index('idx_audit_logs_created_at', 'created_at'),
        db.Index('idx_audit_logs_actor_action', 'actor_id', 'action'),
        db.Index('idx_audit_logs_resource', 'resource_type', 'resource_id'),
        db.Index('idx_audit_logs_request_id', 'request_id'),
        db.Index('idx_audit_logs_action_status', 'action', 'status'),
    )
    
    @classmethod
    def log(cls, **kwargs):
        """
        Create an audit log entry
        
        Args:
            **kwargs: Audit log attributes
            
        Returns:
            AuditLog: Created audit log entry
        """
        log = cls(**kwargs)
        db.session.add(log)
        return log
    
    @classmethod
    def log_user_action(cls, actor_id, action, resource_type, resource_id=None, **kwargs):
        """
        Log a user action
        
        Args:
            actor_id (int): User ID performing the action
            action (str): Action being performed
            resource_type (str): Type of resource being acted upon
            resource_id (int): ID of the resource
            **kwargs: Additional attributes
            
        Returns:
            AuditLog: Created audit log entry
        """
        return cls.log(
            actor_id=actor_id,
            actor_type='user',
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            **kwargs
        )
    
    @classmethod
    def log_admin_action(cls, actor_id, action, resource_type, resource_id=None, **kwargs):
        """
        Log an admin action
        
        Args:
            actor_id (int): Admin user ID
            action (str): Action being performed
            resource_type (str): Type of resource being acted upon
            resource_id (int): ID of the resource
            **kwargs: Additional attributes
            
        Returns:
            AuditLog: Created audit log entry
        """
        return cls.log(
            actor_id=actor_id,
            actor_type='admin',
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            **kwargs
        )
    
    @classmethod
    def log_system_action(cls, action, resource_type, resource_id=None, **kwargs):
        """
        Log a system-generated action
        
        Args:
            action (str): System action
            resource_type (str): Type of resource being acted upon
            resource_id (int): ID of the resource
            **kwargs: Additional attributes
            
        Returns:
            AuditLog: Created audit log entry
        """
        return cls.log(
            actor_type='system',
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            **kwargs
        )
    
    def to_dict(self):
        """Serialize audit log for API responses"""
        return {
            'id': self.id,
            'actor_id': self.actor_id,
            'actor_type': self.actor_type,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'status': self.status,
            'actor_ip': self.actor_ip,
            'request_id': self.request_id,
            'endpoint': self.endpoint,
            'http_method': self.http_method,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<AuditLog {self.action} by {self.actor_type}:{self.actor_id} on {self.resource_type}:{self.resource_id}>'
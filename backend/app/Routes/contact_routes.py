from flask import Blueprint, request, jsonify, current_app
from app.services.notification_service import NotificationService
from config import Config
import logging

contact_bp = Blueprint('contact', __name__, url_prefix='/api/v1')
logger = logging.getLogger(__name__)

@contact_bp.route('/contact', methods=['POST'])
def submit_contact():
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        message = data.get('message')
        
        if not all([name, email, message]):
            return jsonify({'error': 'All fields are required'}), 400
        
        admin_email = current_app.config.get('EMAIL_CONFIG', {}).get('sender')
        
        email_body = f"""
New Contact Form Submission

Name: {name}
Email: {email}

Message:
{message}
"""
        
        with current_app.app_context():
            NotificationService._send_email(
                to_email=admin_email,
                subject=f"Contact Form: Message from {name}",
                body=email_body
            )
        
        logger.info(f"Contact form submitted by {email}")
        return jsonify({'message': 'Message sent successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error processing contact form: {str(e)}")
        return jsonify({'error': 'Failed to send message'}), 500

import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
from ..models import User

class NotificationService:
    
    @staticmethod
    def send_verification_otp(user_id, otp, channel='sms', preferences=None):
        user = User.query.get(user_id)
        if not user:
            return False
        
        message = f"Your PalsPay verification code is: {otp}"
        subject = "Verify Your PalsPay Account"
        
        if channel == 'email':
            return NotificationService._send_email(
                to_email=user.email,
                subject=subject,
                body=f"Hello {user.first_name},\n\n{message}\n\nThis code expires in 10 minutes."
            )
        elif channel == 'sms':
            return NotificationService._send_sms(
                phone_number=user.phone_number,
                message=message
            )
        elif channel == 'whatsapp':
            return NotificationService._send_whatsapp(
                phone_number=user.phone_number,
                message=message
            )
        
        return False
    
    @staticmethod
    def send_login_otp(user_id, otp, ip_address):
        user = User.query.get(user_id)
        if not user:
            return False
        
        message = f"Your PalsPay login code is: {otp}. Login attempt from {ip_address}"
        
        NotificationService._send_sms(user.phone_number, message)
        NotificationService._send_email(
            to_email=user.email,
            subject="Login Alert",
            body=f"Hello {user.first_name},\n\n{message}\n\nIf this wasn't you, please contact support immediately."
        )
        
        return True
    
    @staticmethod
    def send_transfer_notification(sender_user_id, receiver_user_id, amount, currency, transaction_id, is_cross_border=False):
        sender = User.query.get(sender_user_id)
        receiver = User.query.get(receiver_user_id)
        
        if not sender or not receiver:
            return False
        
        sender_message = f"You sent {currency} {amount:,.2f} to {receiver.first_name}"
        receiver_message = f"You received {currency} {amount:,.2f} from {sender.first_name}"
        
        if is_cross_border:
            sender_message += f" (International Transfer)"
            receiver_message += f" (International Transfer)"
        
        NotificationService._send_sms(sender.phone_number, sender_message)
        NotificationService._send_sms(receiver.phone_number, receiver_message)
        
        NotificationService._send_email(
            to_email=sender.email,
            subject="Transfer Sent",
            body=f"Hello {sender.first_name},\n\n{sender_message}\n\nTransaction ID: {transaction_id}"
        )
        
        NotificationService._send_email(
            to_email=receiver.email,
            subject="Transfer Received",
            body=f"Hello {receiver.first_name},\n\n{receiver_message}\n\nTransaction ID: {transaction_id}"
        )
        
        return True
    
    @staticmethod
    def send_welcome_notification(user_id, channel='email'):
        user = User.query.get(user_id)
        if not user:
            return False
        
        message = f"Welcome to PalsPay, {user.first_name}! Your account has been successfully verified."
        
        if channel == 'email':
            return NotificationService._send_email(
                to_email=user.email,
                subject="Welcome to PalsPay!",
                body=f"Hello {user.first_name},\n\n{message}\n\nStart sending money instantly!"
            )
        
        return False
    
    @staticmethod
    def send_password_reset_otp(user_id, otp, channel='email'):
        user = User.query.get(user_id)
        if not user:
            return False
        
        message = f"Your password reset code is: {otp}"
        
        if channel == 'email':
            return NotificationService._send_email(
                to_email=user.email,
                subject="Password Reset Request",
                body=f"Hello {user.first_name},\n\n{message}\n\nThis code expires in 10 minutes."
            )
        elif channel == 'sms':
            return NotificationService._send_sms(user.phone_number, message)
        
        return False
    
    @staticmethod
    def send_password_changed_notification(user_id, channel='email'):
        user = User.query.get(user_id)
        if not user:
            return False
        
        message = "Your PalsPay password has been successfully changed."
        
        if channel == 'email':
            return NotificationService._send_email(
                to_email=user.email,
                subject="Password Changed",
                body=f"Hello {user.first_name},\n\n{message}\n\nIf you didn't make this change, please contact support immediately."
            )
        
        return False
    
    @staticmethod
    def _send_email(to_email, subject, body):
        email_config = current_app.config.get('EMAIL_CONFIG', {})
        
        if not email_config.get('enabled', False):
            current_app.logger.info(f"Email would be sent to {to_email}: {subject}")
            current_app.logger.info(f"Body: {body}")
            return True
        
        try:
            sender = email_config.get('sender')
            password = email_config.get('password')
            
            msg = MIMEMultipart()
            msg['From'] = sender
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(email_config.get('smtp_host'), email_config.get('smtp_port'))
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
            server.quit()
            
            current_app.logger.info(f"Email sent successfully to {to_email}")
            return True
        except Exception as e:
            current_app.logger.error(f"Failed to send email: {str(e)}")
            return False
    
    @staticmethod
    def _send_sms(phone_number, message):
        sms_config = current_app.config.get('SMS_CONFIG', {})
        
        if not sms_config.get('enabled', False):
            current_app.logger.info(f"SMS would be sent to {phone_number}: {message}")
            return True
        
        try:
            api_key = sms_config.get('api_key')
            sender_id = sms_config.get('sender_id')
            
            response = requests.post(
                sms_config.get('endpoint'),
                headers={'Authorization': f'Bearer {api_key}'},
                json={
                    'sender': sender_id,
                    'message': message,
                    'recipients': [{'phone': phone_number}]
                }
            )
            
            return response.status_code == 200
        except Exception as e:
            current_app.logger.error(f"Failed to send SMS: {str(e)}")
            return False
    
    @staticmethod
    def _send_whatsapp(phone_number, message):
        whatsapp_config = current_app.config.get('WHATSAPP_CONFIG', {})
        
        if not whatsapp_config.get('enabled', False):
            current_app.logger.info(f"WhatsApp would be sent to {phone_number}: {message}")
            return True
        
        try:
            token = whatsapp_config.get('token')
            phone_id = whatsapp_config.get('phone_id')
            
            response = requests.post(
                f"https://graph.facebook.com/v17.0/{phone_id}/messages",
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                },
                json={
                    'messaging_product': 'whatsapp',
                    'to': phone_number.replace('+', ''),
                    'type': 'text',
                    'text': {'body': message}
                }
            )
            
            return response.status_code == 200
        except Exception as e:
            current_app.logger.error(f"Failed to send WhatsApp: {str(e)}")
            return False
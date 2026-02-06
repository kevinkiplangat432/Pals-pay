import requests
import base64
from datetime import datetime
import uuid
from decimal import Decimal
import json
from ..extensions import db
from app.models import Transaction, Wallet, PaymentMethod, AuditLog
from app.models.enums import TransactionStatus, TransactionType, PaymentProvider

class PaymentService:
    """
    Service for handling MPesa payments via Safaricom Daraja API
    """
    
    def __init__(self, app=None):
        self.app = app
        self.access_token = None
        self.token_expiry = None
    
    def init_app(self, app):
        self.app = app
    
    def get_access_token(self):
        """
        Get access token from Daraja API
        """
        if self.access_token and self.token_expiry and datetime.utcnow() < self.token_expiry:
            return self.access_token
        
        consumer_key = self.app.config['DARAJA_CONSUMER_KEY']
        consumer_secret = self.app.config['DARAJA_CONSUMER_SECRET']
        base_url = self.app.config['DARAJA_BASE_URL']
        
        # Encode credentials
        credentials = f"{consumer_key}:{consumer_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        # Request token
        headers = {
            'Authorization': f'Basic {encoded_credentials}'
        }
        
        try:
            response = requests.get(
                f'{base_url}/oauth/v1/generate?grant_type=client_credentials',
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                # Token expires in 1 hour
                self.token_expiry = datetime.utcnow().replace(second=0, microsecond=0)
                return self.access_token
            else:
                raise Exception(f"Failed to get access token: {response.text}")
                
        except Exception as e:
            self.app.logger.error(f"Error getting Daraja token: {str(e)}")
            return None
    
    def stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """
        Initiate STK push for payment
        """
        access_token = self.get_access_token()
        if not access_token:
            return {'success': False, 'message': 'Failed to authenticate with payment gateway'}
        
        base_url = self.app.config['DARAJA_BASE_URL']
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Business shortcode from environment (use 174379 for sandbox)
        business_shortcode = self.app.config.get('DARAJA_BUSINESS_SHORTCODE', '174379')
        passkey = self.app.config.get('DARAJA_PASSKEY', '')
        
        # Generate password
        password = base64.b64encode(
            f"{business_shortcode}{passkey}{timestamp}".encode()
        ).decode()
        
        # Request payload
        payload = {
            "BusinessShortCode": business_shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone_number,
            "PartyB": business_shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": f"{self.app.config.get('BASE_URL', 'http://localhost:5000')}/api/payments/mpesa-callback",
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc
        }
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                f'{base_url}/mpesa/stkpush/v1/processrequest',
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ResponseCode') == '0':
                    return {
                        'success': True,
                        'checkout_request_id': data.get('CheckoutRequestID'),
                        'customer_message': data.get('CustomerMessage'),
                        'data': data
                    }
                else:
                    return {
                        'success': False,
                        'message': data.get('ResponseDescription', 'Payment request failed')
                    }
            else:
                return {
                    'success': False,
                    'message': f'Payment gateway error: {response.status_code}'
                }
                
        except Exception as e:
            self.app.logger.error(f"Error initiating STK push: {str(e)}")
            return {'success': False, 'message': f'Payment request failed: {str(e)}'}
    
    def process_deposit(self, user_id, amount, phone_number):
        """
        Process deposit via MPesa
        """
        user_wallet = Wallet.query.filter_by(user_id=user_id).first()
        if not user_wallet:
            return {'success': False, 'message': 'Wallet not found'}
        
        # Initiate STK push
        result = self.stk_push(
            phone_number=phone_number,
            amount=amount,
            account_reference=str(user_id),
            transaction_desc=f"Wallet deposit for user {user_id}"
        )
        
        if result['success']:
            # Create pending transaction
            transaction = Transaction(
                sender_wallet_id=None,
                receiver_wallet_id=user_wallet.id,
                external_sender=phone_number,
                amount=Decimal(str(amount)),
                fee=Decimal('0.00'),
                net_amount=Decimal(str(amount)),
                transaction_type=TransactionType.deposit,
                status=TransactionStatus.pending,
                provider=PaymentProvider.mpesa,
                external_reference=result.get('checkout_request_id'),
                description=f"MPesa deposit from {phone_number}",
                metadata={'stk_push_response': result.get('data', {})}
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            # Log the action
            AuditLog.log_user_action(
                actor_id=user_id,
                action='deposit.initiate',
                resource_type='transaction',
                resource_id=transaction.id,
                new_values={'amount': float(amount), 'phone': phone_number},
                status='pending'
            )
            
            return {
                'success': True,
                'message': result.get('customer_message', 'Payment initiated'),
                'transaction_id': transaction.id,
                'checkout_request_id': result.get('checkout_request_id')
            }
        else:
            return result
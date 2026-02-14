import requests
import base64
from datetime import datetime
from flask import current_app
import json


class MpesaService:
    """M-Pesa Daraja API Integration Service"""
    
    @staticmethod
    def get_access_token():
        """Generate OAuth access token"""
        consumer_key = current_app.config.get('MPESA_CONSUMER_KEY')
        consumer_secret = current_app.config.get('MPESA_CONSUMER_SECRET')
        api_url = current_app.config.get('MPESA_API_URL')
        
        auth_string = f"{consumer_key}:{consumer_secret}"
        encoded = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {encoded}'
        }
        
        response = requests.get(f"{api_url}/oauth/v1/generate?grant_type=client_credentials", headers=headers)
        return response.json().get('access_token')
    
    @staticmethod
    def stk_push(phone_number, amount, account_reference, transaction_desc):
        """Initiate STK Push (Lipa Na M-Pesa Online)"""
        access_token = MpesaService.get_access_token()
        api_url = current_app.config.get('MPESA_API_URL')
        business_short_code = current_app.config.get('MPESA_SHORTCODE')
        passkey = current_app.config.get('MPESA_PASSKEY')
        callback_url = current_app.config.get('MPESA_CALLBACK_URL')
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(f"{business_short_code}{passkey}{timestamp}".encode()).decode()
        
        # Format phone number (remove + and ensure 254 format)
        if phone_number.startswith('+'):
            phone_number = phone_number[1:]
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "BusinessShortCode": business_short_code,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone_number,
            "PartyB": business_short_code,
            "PhoneNumber": phone_number,
            "CallBackURL": callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc
        }
        
        response = requests.post(
            f"{api_url}/mpesa/stkpush/v1/processrequest",
            json=payload,
            headers=headers
        )
        
        return response.json()
    
    @staticmethod
    def query_stk_status(checkout_request_id):
        """Query STK Push transaction status"""
        access_token = MpesaService.get_access_token()
        api_url = current_app.config.get('MPESA_API_URL')
        business_short_code = current_app.config.get('MPESA_SHORTCODE')
        passkey = current_app.config.get('MPESA_PASSKEY')
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(f"{business_short_code}{passkey}{timestamp}".encode()).decode()
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "BusinessShortCode": business_short_code,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id
        }
        
        response = requests.post(
            f"{api_url}/mpesa/stkpushquery/v1/query",
            json=payload,
            headers=headers
        )
        
        return response.json()
    
    @staticmethod
    def b2c_payment(phone_number, amount, occasion="Payment"):
        """Business to Customer payment"""
        access_token = MpesaService.get_access_token()
        api_url = current_app.config.get('MPESA_API_URL')
        initiator_name = current_app.config.get('MPESA_INITIATOR_NAME')
        security_credential = current_app.config.get('MPESA_SECURITY_CREDENTIAL')
        shortcode = current_app.config.get('MPESA_SHORTCODE')
        result_url = current_app.config.get('MPESA_B2C_RESULT_URL')
        timeout_url = current_app.config.get('MPESA_B2C_TIMEOUT_URL')
        
        # Format phone number
        if phone_number.startswith('+'):
            phone_number = phone_number[1:]
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "InitiatorName": initiator_name,
            "SecurityCredential": security_credential,
            "CommandID": "BusinessPayment",
            "Amount": int(amount),
            "PartyA": shortcode,
            "PartyB": phone_number,
            "Remarks": occasion,
            "QueueTimeOutURL": timeout_url,
            "ResultURL": result_url,
            "Occasion": occasion
        }
        
        response = requests.post(
            f"{api_url}/mpesa/b2c/v1/paymentrequest",
            json=payload,
            headers=headers
        )
        
        return response.json()

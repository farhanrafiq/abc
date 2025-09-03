import os
import hmac
import hashlib
import razorpay
from flask import current_app
import logging

def get_razorpay_client():
    """Get Razorpay client instance"""
    key_id = current_app.config.get('RAZORPAY_KEY_ID', 'test_key')
    key_secret = current_app.config.get('RAZORPAY_KEY_SECRET', 'test_secret')
    
    return razorpay.Client(auth=(key_id, key_secret))

def create_razorpay_order(amount_paisa, order_id, currency='INR'):
    """Create Razorpay order"""
    try:
        client = get_razorpay_client()
        
        # Convert paisa to paise for Razorpay (they expect smallest currency unit)
        order_data = {
            'amount': amount_paisa,  # Amount in paisa
            'currency': currency,
            'receipt': f'order_{order_id}',
            'payment_capture': 1  # Auto capture payment
        }
        
        razorpay_order = client.order.create(data=order_data)
        logging.info(f"Razorpay order created: {razorpay_order['id']}")
        
        return razorpay_order
    
    except Exception as e:
        logging.error(f"Razorpay order creation failed: {e}")
        raise

def verify_razorpay_payment(payment_id, order_id, signature):
    """Verify Razorpay payment signature"""
    try:
        client = get_razorpay_client()
        
        # Verify signature
        params_dict = {
            'razorpay_payment_id': payment_id,
            'razorpay_order_id': order_id,
            'razorpay_signature': signature
        }
        
        client.utility.verify_payment_signature(params_dict)
        logging.info(f"Payment verified successfully: {payment_id}")
        return True
    
    except Exception as e:
        logging.error(f"Payment verification failed: {e}")
        return False

def capture_razorpay_payment(payment_id, amount_paisa):
    """Capture Razorpay payment (if auto-capture is disabled)"""
    try:
        client = get_razorpay_client()
        
        client.payment.capture(payment_id, amount_paisa)
        logging.info(f"Payment captured: {payment_id}")
        return True
    
    except Exception as e:
        logging.error(f"Payment capture failed: {e}")
        return False

def refund_razorpay_payment(payment_id, amount_paisa=None, reason=None):
    """Refund Razorpay payment"""
    try:
        client = get_razorpay_client()
        
        refund_data = {}
        if amount_paisa:
            refund_data['amount'] = amount_paisa
        if reason:
            refund_data['notes'] = {'reason': reason}
        
        refund = client.payment.refund(payment_id, refund_data)
        logging.info(f"Refund processed: {refund['id']}")
        return refund
    
    except Exception as e:
        logging.error(f"Refund failed: {e}")
        return None

def get_payment_details(payment_id):
    """Get payment details from Razorpay"""
    try:
        client = get_razorpay_client()
        payment = client.payment.fetch(payment_id)
        return payment
    
    except Exception as e:
        logging.error(f"Failed to fetch payment details: {e}")
        return None

def create_upi_intent_url(amount_paisa, merchant_vpa, merchant_name, transaction_ref, note=None):
    """Create UPI intent URL for direct UPI payments"""
    amount_rupees = amount_paisa / 100
    
    upi_url = f"upi://pay?pa={merchant_vpa}&pn={merchant_name}&tr={transaction_ref}&am={amount_rupees}&cu=INR"
    
    if note:
        upi_url += f"&tn={note}"
    
    return upi_url

def validate_webhook_signature(payload, signature, secret):
    """Validate Razorpay webhook signature"""
    try:
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    except Exception as e:
        logging.error(f"Webhook signature validation failed: {e}")
        return False

def process_webhook_payload(payload):
    """Process Razorpay webhook payload"""
    try:
        event = payload.get('event')
        payment_entity = payload.get('payload', {}).get('payment', {}).get('entity', {})
        
        if event == 'payment.captured':
            # Handle successful payment
            payment_id = payment_entity.get('id')
            order_id = payment_entity.get('order_id')
            amount = payment_entity.get('amount')
            
            logging.info(f"Payment captured webhook: {payment_id} for order {order_id}")
            return {
                'type': 'payment_captured',
                'payment_id': payment_id,
                'order_id': order_id,
                'amount': amount
            }
        
        elif event == 'payment.failed':
            # Handle failed payment
            payment_id = payment_entity.get('id')
            order_id = payment_entity.get('order_id')
            error_description = payment_entity.get('error_description')
            
            logging.warning(f"Payment failed webhook: {payment_id} - {error_description}")
            return {
                'type': 'payment_failed',
                'payment_id': payment_id,
                'order_id': order_id,
                'error': error_description
            }
        
        return None
    
    except Exception as e:
        logging.error(f"Webhook processing failed: {e}")
        return None

# COD (Cash on Delivery) utilities
def validate_cod_availability(pincode, amount_paisa):
    """Validate if COD is available for given pincode and amount"""
    # Simplified validation - in production, integrate with courier API
    
    # COD limits
    max_cod_amount = 5000000  # 50,000 INR in paisa
    
    if amount_paisa > max_cod_amount:
        return False, "COD not available for orders above ₹50,000"
    
    # Kashmir pincodes (simplified check)
    kashmir_pincodes = ['19', '18']  # Starting digits for J&K pincodes
    
    if any(pincode.startswith(prefix) for prefix in kashmir_pincodes):
        return True, "COD available"
    
    # Other Indian pincodes
    if len(pincode) == 6 and pincode.isdigit():
        return True, "COD available"
    
    return False, "COD not available for this location"

def calculate_cod_charges(amount_paisa):
    """Calculate COD charges"""
    # Simplified COD charges - typically 2% with min/max limits
    cod_rate = 0.02  # 2%
    min_charge = 2000  # 20 INR
    max_charge = 10000  # 100 INR
    
    charge = int(amount_paisa * cod_rate)
    return max(min_charge, min(charge, max_charge))

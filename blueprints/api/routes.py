from flask import Blueprint, request, jsonify
from app import db
from models import Product, NewsletterSubscriber

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/newsletter/subscribe', methods=['POST'])
def subscribe_newsletter():
    """Subscribe to newsletter via AJAX"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'success': False, 'message': 'Email is required'}), 400
        
        # Validate email format
        import re
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email):
            return jsonify({'success': False, 'message': 'Invalid email format'}), 400
        
        # Check if already subscribed
        existing = NewsletterSubscriber.query.filter_by(email=email).first()
        if existing:
            if existing.is_active:
                return jsonify({'success': False, 'message': 'Already subscribed!'}), 409
            else:
                # Reactivate subscription
                existing.is_active = True
                db.session.commit()
                return jsonify({'success': True, 'message': 'Subscription reactivated!'})
        
        # Create new subscription
        subscriber = NewsletterSubscriber()
        subscriber.email = email
        subscriber.is_active = True
        db.session.add(subscriber)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Thank you for subscribing!'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Subscription failed. Please try again.'}), 500

@api_bp.route('/api/products/isbn/<isbn>')
def get_product_by_isbn(isbn):
    """Get product by ISBN for quick order"""
    try:
        # Clean ISBN
        clean_isbn = isbn.replace('-', '').replace(' ', '')
        
        # Find product by ISBN
        product = Product.query.filter_by(isbn=clean_isbn).first()
        
        if not product:
            return jsonify({'success': False, 'message': 'Book not found with this ISBN'})
        
        # Check if product is active and in stock
        if product.status.value != 'Active':
            return jsonify({'success': False, 'message': 'This book is currently unavailable'})
        
        if not product.inventory or product.inventory.stock_on_hand <= 0:
            return jsonify({'success': False, 'message': 'This book is out of stock'})
        
        # Return product data
        product_data = {
            'id': product.id,
            'title': product.title,
            'author': product.authors[0].name if product.authors else None,
            'isbn': product.isbn,
            'cover_image': product.cover_image,
            'price': product.price.sale_inr / 100 if product.price else 0,
            'slug': product.slug
        }
        
        return jsonify({'success': True, 'product': product_data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error searching for book'}), 500

@api_bp.route('/webhook/razorpay', methods=['POST'])
def razorpay_webhook():
    """Handle Razorpay webhooks with proper signature verification and order processing"""
    import logging
    from flask import current_app
    from models import Order, PaymentStatus, OrderStatus
    
    try:
        # Get webhook data
        payload = request.get_data()
        signature = request.headers.get('X-Razorpay-Signature')
        
        # CRITICAL: Always verify webhook signature for security
        import hmac
        import hashlib
        webhook_secret = current_app.config.get('RAZORPAY_WEBHOOK_SECRET')
        
        if not webhook_secret:
            logging.error('RAZORPAY_WEBHOOK_SECRET not configured - rejecting webhook')
            return jsonify({'error': 'Webhook secret not configured'}), 400
            
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            logging.warning('Razorpay webhook signature verification failed')
            return jsonify({'error': 'Invalid signature'}), 400
        
        # Parse webhook data
        webhook_data = request.get_json()
        event = webhook_data.get('event')
        payment_entity = webhook_data.get('payload', {}).get('payment', {}).get('entity', {})
        
        if event == 'payment.captured':
            # Handle successful payment
            razorpay_payment_id = payment_entity.get('id')
            razorpay_order_id = payment_entity.get('order_id')
            amount = payment_entity.get('amount', 0)
            
            # Find and update order
            order = Order.query.filter_by(razorpay_order_id=razorpay_order_id).first()
            if order and order.payment_status != PaymentStatus.PAID:
                # Update order status
                order.razorpay_payment_id = razorpay_payment_id
                order.payment_status = PaymentStatus.PAID
                order.status = OrderStatus.PAID
                
                # Update inventory atomically
                for item in order.items:
                    if item.product.inventory:
                        item.product.inventory.stock_on_hand -= item.quantity
                
                # Generate invoice PDF
                try:
                    from utils.pdf import generate_invoice_pdf
                    invoice_path = f"static/invoices/invoice_{order.id}.pdf"
                    generate_invoice_pdf(order, invoice_path)
                    order.invoice_path = invoice_path
                except Exception as e:
                    logging.error(f"Invoice generation failed for order {order.id}: {e}")
                
                db.session.commit()
                
                # Send confirmation email asynchronously
                try:
                    from utils.email import send_order_confirmation_email
                    send_order_confirmation_email(order)
                except Exception as e:
                    logging.error(f"Failed to send order confirmation email: {e}")
                
                logging.info(f'Payment captured for order {order.id}: {razorpay_payment_id}')
            
        elif event == 'payment.failed':
            # Handle failed payment
            razorpay_order_id = payment_entity.get('order_id')
            order = Order.query.filter_by(razorpay_order_id=razorpay_order_id).first()
            if order:
                order.payment_status = PaymentStatus.FAILED
                order.status = OrderStatus.CANCELLED
                db.session.commit()
                logging.info(f'Payment failed for order {order.id}')
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        logging.error(f'Razorpay webhook error: {e}')
        return jsonify({'error': 'Webhook processing failed'}), 500
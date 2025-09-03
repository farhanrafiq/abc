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
        subscriber = NewsletterSubscriber(email=email, is_active=True)
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
import os
import uuid
import re
from datetime import datetime
from flask import session, current_app
from flask_login import current_user
from models import Cart, Product, Coupon, CouponType
from app import db
from PIL import Image
import logging

def format_currency(amount_paisa, currency='INR'):
    """Format currency amount from paisa to readable format"""
    if amount_paisa is None:
        return f'{currency} 0.00'
    
    amount = amount_paisa / 100
    if currency == 'INR':
        return f'₹{amount:,.2f}'
    else:
        return f'{currency} {amount:,.2f}'

def generate_slug(text):
    """Generate URL-friendly slug from text"""
    # Convert to lowercase and replace spaces with dashes
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')

def save_uploaded_file(file, folder):
    """Save uploaded file and return filename"""
    if not file:
        return None
    
    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', folder)
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1].lower()
    filepath = os.path.join(upload_dir, filename)
    
    try:
        # Save original file
        file.save(filepath)
        
        # Optimize image if it's an image file
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            optimize_image(filepath)
        
        return f'uploads/{folder}/{filename}'
    except Exception as e:
        logging.error(f"Failed to save file: {e}")
        return None

def optimize_image(filepath, max_size=(800, 600), quality=85):
    """Optimize uploaded image"""
    try:
        with Image.open(filepath) as img:
            # Convert RGBA to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Resize if larger than max_size
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save with optimization
            img.save(filepath, optimize=True, quality=quality)
    except Exception as e:
        logging.error(f"Failed to optimize image: {e}")

def get_or_create_cart():
    """Get or create cart for current user/session"""
    if current_user.is_authenticated:
        cart = Cart.query.filter_by(user_id=current_user.id).first()
        if not cart:
            cart = Cart(user_id=current_user.id)
            db.session.add(cart)
            db.session.commit()
    else:
        # Guest user - use session
        if 'cart_session_id' not in session:
            session['cart_session_id'] = str(uuid.uuid4())
        
        cart = Cart.query.filter_by(session_id=session['cart_session_id']).first()
        if not cart:
            cart = Cart(session_id=session['cart_session_id'])
            db.session.add(cart)
            db.session.commit()
    
    return cart

def get_cart_count():
    """Get number of items in cart"""
    cart = get_or_create_cart()
    return cart.items.count() if cart else 0

def calculate_cart_total(cart):
    """Calculate cart total"""
    total = 0
    for item in cart.items:
        if item.product and item.product.price:
            price = item.product.price.sale_inr or item.product.price.mrp_inr
            total += price * item.quantity
    return total

def validate_coupon(code, subtotal_paisa):
    """Validate coupon code"""
    if not code:
        return None
    
    coupon = Coupon.query.filter_by(code=code.upper(), is_active=True).first()
    
    if not coupon:
        return None
    
    now = datetime.utcnow()
    
    # Check date validity
    if coupon.starts_at and now < coupon.starts_at:
        return None
    
    if coupon.ends_at and now > coupon.ends_at:
        return None
    
    # Check minimum subtotal
    if coupon.min_subtotal and subtotal_paisa < coupon.min_subtotal:
        return None
    
    # Check usage limits (simplified - in production, track actual usage)
    # This would require additional tracking tables
    
    return coupon

def paginate_query(query, page, per_page):
    """Paginate SQLAlchemy query"""
    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

def get_breadcrumbs(category=None, product=None):
    """Generate breadcrumbs for navigation"""
    breadcrumbs = [{'name': 'Home', 'url': '/'}]
    
    if category:
        # Add parent categories
        parents = []
        current = category
        while current.parent:
            parents.append(current.parent)
            current = current.parent
        
        # Add in reverse order (root first)
        for parent in reversed(parents):
            breadcrumbs.append({
                'name': parent.name,
                'url': f'/catalog/{parent.slug}'
            })
        
        breadcrumbs.append({
            'name': category.name,
            'url': f'/catalog/{category.slug}'
        })
    
    if product:
        breadcrumbs.append({
            'name': product.title,
            'url': f'/product/{product.slug}'
        })
    
    return breadcrumbs

def calculate_shipping(subtotal_paisa, user_state=None):
    """Calculate shipping cost based on location and order value"""
    # Free shipping threshold
    free_shipping_threshold = current_app.config.get('FREE_SHIPPING_THRESHOLD', 150000)  # 1500 INR
    
    if subtotal_paisa >= free_shipping_threshold:
        return 0
    
    # Kashmir vs rest of India
    if user_state and user_state.lower() in ['jammu and kashmir', 'j&k', 'kashmir']:
        return current_app.config.get('KASHMIR_SHIPPING_RATE', 5000)  # 50 INR
    else:
        return current_app.config.get('INDIA_SHIPPING_RATE', 10000)  # 100 INR

def get_featured_products(limit=8):
    """Get featured products for homepage"""
    from models import ProductStatus, Inventory
    
    return db.session.query(Product).join(Inventory)\
        .filter(Product.status == ProductStatus.ACTIVE)\
        .filter(Inventory.stock_on_hand > 0)\
        .order_by(db.desc(Product.created_at))\
        .limit(limit).all()

def get_related_products(product, limit=4):
    """Get related products based on categories"""
    if not product.categories:
        return []
    
    from models import ProductStatus, Inventory
    
    category_ids = [c.id for c in product.categories]
    
    return db.session.query(Product).join(Inventory)\
        .join(Product.categories)\
        .filter(Category.id.in_(category_ids))\
        .filter(Product.id != product.id)\
        .filter(Product.status == ProductStatus.ACTIVE)\
        .filter(Inventory.stock_on_hand > 0)\
        .limit(limit).all()

def merge_guest_cart_on_login(user):
    """Merge guest cart with user cart on login"""
    if 'cart_session_id' in session:
        guest_cart = Cart.query.filter_by(session_id=session['cart_session_id']).first()
        if guest_cart and guest_cart.items.count() > 0:
            user_cart = Cart.query.filter_by(user_id=user.id).first()
            if not user_cart:
                # Transfer guest cart to user
                guest_cart.user_id = user.id
                guest_cart.session_id = None
            else:
                # Merge items
                for item in guest_cart.items:
                    existing_item = user_cart.items.filter_by(product_id=item.product_id).first()
                    if existing_item:
                        existing_item.quantity += item.quantity
                    else:
                        item.cart_id = user_cart.id
                
                # Delete guest cart
                db.session.delete(guest_cart)
            
            db.session.commit()
            session.pop('cart_session_id', None)

def get_price_display(product):
    """Get formatted price display for product"""
    if not product.price:
        return 'Price not available'
    
    mrp = product.price.mrp_inr
    sale_price = product.price.sale_inr
    
    if sale_price and sale_price < mrp:
        # Show both prices with discount
        discount_pct = int((mrp - sale_price) / mrp * 100)
        return {
            'sale_price': format_currency(sale_price),
            'mrp': format_currency(mrp),
            'discount_pct': discount_pct,
            'has_discount': True
        }
    else:
        # Show only MRP
        return {
            'sale_price': format_currency(mrp),
            'mrp': None,
            'discount_pct': 0,
            'has_discount': False
        }

def is_in_stock(product):
    """Check if product is in stock"""
    return product.inventory and product.inventory.stock_on_hand > 0

def get_stock_status(product):
    """Get stock status for display"""
    if not product.inventory:
        return {'status': 'unknown', 'message': 'Stock information unavailable'}
    
    stock = product.inventory.stock_on_hand
    low_threshold = product.inventory.low_stock_threshold
    
    if stock <= 0:
        return {'status': 'out_of_stock', 'message': 'Out of stock'}
    elif stock <= low_threshold:
        return {'status': 'low_stock', 'message': f'Only {stock} left in stock'}
    else:
        return {'status': 'in_stock', 'message': 'In stock'}

def create_audit_log(action, entity_type, entity_id, details=None):
    """Create audit log entry (simplified version)"""
    # In a full implementation, you'd have an AuditLog model
    logging.info(f"AUDIT: {action} {entity_type} {entity_id} by user {current_user.id if current_user.is_authenticated else 'anonymous'} - {details}")

from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify, current_app
from flask_login import current_user, login_required
from models import Product, Cart, CartItem, Order, OrderItem, Address, Coupon, Inventory, Price, OrderStatus, PaymentStatus, PaymentMethod
from forms import CheckoutForm, AddressForm
from utils.helpers import get_or_create_cart, calculate_cart_total, format_currency, validate_coupon
from utils.payments import create_razorpay_order, verify_razorpay_payment
from utils.email import send_order_confirmation_email
from app import db
import logging
import uuid

cart_bp = Blueprint('cart', __name__)

@cart_bp.route('/')
def view_cart():
    """Display cart contents"""
    cart = get_or_create_cart()
    cart_items = cart.items.all() if cart else []
    
    # Calculate totals
    subtotal = 0
    for item in cart_items:
        if item.product and item.product.price:
            price = item.product.price.sale_inr or item.product.price.mrp_inr
            subtotal += price * item.quantity
    
    # Check stock availability
    for item in cart_items:
        if item.product and item.product.inventory:
            if item.quantity > item.product.inventory.stock_on_hand:
                flash(f'Only {item.product.inventory.stock_on_hand} units of "{item.product.title}" are available.', 'warning')
    
    return render_template('web/cart.html',
                         cart_items=cart_items,
                         subtotal=subtotal,
                         format_currency=format_currency)

@cart_bp.route('/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    """Add product to cart"""
    product = Product.query.get_or_404(product_id)
    quantity = request.form.get('quantity', 1, type=int)
    
    if quantity <= 0:
        flash('Invalid quantity.', 'error')
        return redirect(url_for('web.product_detail', slug=product.slug))
    
    # Check stock availability
    if product.inventory and quantity > product.inventory.stock_on_hand:
        flash(f'Only {product.inventory.stock_on_hand} units available.', 'error')
        return redirect(url_for('web.product_detail', slug=product.slug))
    
    cart = get_or_create_cart()
    
    # Check if item already in cart
    existing_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
    
    if existing_item:
        new_quantity = existing_item.quantity + quantity
        if product.inventory and new_quantity > product.inventory.stock_on_hand:
            flash(f'Cannot add more. Only {product.inventory.stock_on_hand} units available.', 'error')
        else:
            existing_item.quantity = new_quantity
            db.session.commit()
            flash(f'Updated quantity of "{product.title}" in cart.', 'success')
    else:
        cart_item = CartItem(
            cart_id=cart.id,
            product_id=product_id,
            quantity=quantity
        )
        db.session.add(cart_item)
        db.session.commit()
        flash(f'"{product.title}" added to cart.', 'success')
    
    return redirect(url_for('web.product_detail', slug=product.slug))

@cart_bp.route('/update/<int:item_id>', methods=['POST'])
def update_cart_item(item_id):
    """Update cart item quantity"""
    cart = get_or_create_cart()
    cart_item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first_or_404()
    
    quantity = request.form.get('quantity', 1, type=int)
    
    if quantity <= 0:
        db.session.delete(cart_item)
        flash('Item removed from cart.', 'info')
    else:
        # Check stock availability
        if cart_item.product.inventory and quantity > cart_item.product.inventory.stock_on_hand:
            flash(f'Only {cart_item.product.inventory.stock_on_hand} units available.', 'error')
        else:
            cart_item.quantity = quantity
            flash('Cart updated.', 'success')
    
    db.session.commit()
    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/remove/<int:item_id>')
def remove_cart_item(item_id):
    """Remove item from cart"""
    cart = get_or_create_cart()
    cart_item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first_or_404()
    
    product_title = cart_item.product.title
    db.session.delete(cart_item)
    db.session.commit()
    
    flash(f'"{product_title}" removed from cart.', 'info')
    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/clear')
def clear_cart():
    """Clear all items from cart"""
    cart = get_or_create_cart()
    if cart:
        CartItem.query.filter_by(cart_id=cart.id).delete()
        db.session.commit()
        flash('Cart cleared.', 'info')
    
    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """Checkout process"""
    cart = get_or_create_cart()
    cart_items = cart.items.all() if cart else []
    
    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart.view_cart'))
    
    form = CheckoutForm()
    
    # Populate address choices for logged-in users
    if current_user.is_authenticated:
        addresses = current_user.addresses.all()
        form.billing_address_id.choices = [('', 'Select Address')] + [(a.id, f'{a.name} - {a.line1}, {a.city}') for a in addresses]
        form.shipping_address_id.choices = form.billing_address_id.choices
    
    if form.validate_on_submit():
        # Calculate totals
        subtotal = 0
        for item in cart_items:
            if item.product and item.product.price:
                price = item.product.price.sale_inr or item.product.price.mrp_inr
                subtotal += price * item.quantity
        
        # Apply coupon if provided
        discount = 0
        coupon = None
        if form.coupon_code.data:
            coupon = validate_coupon(form.coupon_code.data, subtotal)
            if coupon:
                if coupon.type.value == 'PERCENT':
                    discount = int(subtotal * coupon.value / 100)
                else:  # AMOUNT
                    discount = int(coupon.value * 100)  # Convert to paisa
                discount = min(discount, subtotal)  # Don't exceed subtotal
        
        # Calculate shipping (simplified)
        shipping = current_app.config.get('KASHMIR_SHIPPING_RATE', 5000)  # 50 INR
        if subtotal >= current_app.config.get('FREE_SHIPPING_THRESHOLD', 150000):  # 1500 INR
            shipping = 0
        
        # Calculate tax (simplified - 0% for books)
        tax = 0
        
        grand_total = subtotal - discount + shipping + tax
        
        # Create order
        order = Order(
            user_id=current_user.id if current_user.is_authenticated else None,
            email=form.guest_email.data if form.guest_email.data else current_user.email,
            phone=form.guest_phone.data if form.guest_phone.data else current_user.phone,
            billing_address_id=form.billing_address_id.data if form.billing_address_id.data else None,
            shipping_address_id=form.shipping_address_id.data if form.shipping_address_id.data else None,
            subtotal_inr=subtotal,
            discount_inr=discount,
            shipping_inr=shipping,
            tax_inr=tax,
            grand_total_inr=grand_total,
            payment_method=PaymentMethod(form.payment_method.data.upper()),
            notes=form.notes.data
        )
        
        db.session.add(order)
        db.session.flush()  # To get order.id
        
        # Create order items
        for item in cart_items:
            price = item.product.price.sale_inr or item.product.price.mrp_inr
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                title_snapshot=item.product.title,
                sku_snapshot=item.product.inventory.sku if item.product.inventory else '',
                unit_price_inr=price,
                quantity=item.quantity,
                line_total_inr=price * item.quantity
            )
            db.session.add(order_item)
        
        # Handle payment
        if form.payment_method.data == 'razorpay':
            # Create Razorpay order
            try:
                razorpay_order = create_razorpay_order(grand_total, order.id)
                order.razorpay_order_id = razorpay_order['id']
                db.session.commit()
                
                # Redirect to payment page with Razorpay details
                return render_template('web/payment.html',
                                     order=order,
                                     razorpay_order=razorpay_order,
                                     razorpay_key=current_app.config['RAZORPAY_KEY_ID'])
            except Exception as e:
                logging.error(f"Razorpay order creation failed: {e}")
                flash('Payment initialization failed. Please try again.', 'error')
                db.session.rollback()
                return redirect(url_for('cart.checkout'))
        else:
            # Cash on Delivery
            order.status = OrderStatus.PENDING
            order.payment_status = PaymentStatus.UNPAID
            db.session.commit()
            
            # Clear cart
            CartItem.query.filter_by(cart_id=cart.id).delete()
            db.session.commit()
            
            # Send confirmation email
            try:
                send_order_confirmation_email(order)
            except Exception as e:
                logging.error(f"Failed to send order confirmation email: {e}")
            
            flash('Order placed successfully! You will receive a confirmation email shortly.', 'success')
            return redirect(url_for('cart.order_success', order_id=order.id))
    
    # Calculate cart summary for display
    subtotal = 0
    for item in cart_items:
        if item.product and item.product.price:
            price = item.product.price.sale_inr or item.product.price.mrp_inr
            subtotal += price * item.quantity
    
    shipping = current_app.config.get('KASHMIR_SHIPPING_RATE', 5000)
    if subtotal >= current_app.config.get('FREE_SHIPPING_THRESHOLD', 150000):
        shipping = 0
    
    return render_template('web/checkout.html',
                         form=form,
                         cart_items=cart_items,
                         subtotal=subtotal,
                         shipping=shipping,
                         format_currency=format_currency)

@cart_bp.route('/payment/verify', methods=['POST'])
def verify_payment():
    """Verify Razorpay payment"""
    try:
        payment_id = request.form.get('razorpay_payment_id')
        order_id = request.form.get('razorpay_order_id')
        signature = request.form.get('razorpay_signature')
        
        # Verify payment
        if verify_razorpay_payment(payment_id, order_id, signature):
            # Find order
            order = Order.query.filter_by(razorpay_order_id=order_id).first()
            if order:
                order.razorpay_payment_id = payment_id
                order.payment_status = PaymentStatus.PAID
                order.status = OrderStatus.PAID
                
                # Update inventory
                for item in order.items:
                    if item.product.inventory:
                        item.product.inventory.stock_on_hand -= item.quantity
                
                db.session.commit()
                
                # Clear cart
                if current_user.is_authenticated:
                    cart = Cart.query.filter_by(user_id=current_user.id).first()
                else:
                    cart = Cart.query.filter_by(session_id=session.get('cart_session_id')).first()
                
                if cart:
                    CartItem.query.filter_by(cart_id=cart.id).delete()
                    db.session.commit()
                
                # Send confirmation email
                try:
                    send_order_confirmation_email(order)
                except Exception as e:
                    logging.error(f"Failed to send order confirmation email: {e}")
                
                flash('Payment successful! Your order has been confirmed.', 'success')
                return redirect(url_for('cart.order_success', order_id=order.id))
        
        flash('Payment verification failed. Please contact support.', 'error')
        return redirect(url_for('cart.checkout'))
    
    except Exception as e:
        logging.error(f"Payment verification error: {e}")
        flash('Payment verification failed. Please contact support.', 'error')
        return redirect(url_for('cart.checkout'))

@cart_bp.route('/order/<int:order_id>/success')
def order_success(order_id):
    """Order success page"""
    order = Order.query.get_or_404(order_id)
    
    # Verify order belongs to current user or session
    if current_user.is_authenticated:
        if order.user_id != current_user.id:
            flash('Order not found.', 'error')
            return redirect(url_for('web.index'))
    
    return render_template('web/order_success.html',
                         order=order,
                         format_currency=format_currency)

@cart_bp.route('/order/<int:order_id>')
def order_detail(order_id):
    """Order detail page for customers"""
    order = Order.query.get_or_404(order_id)
    
    # Verify order belongs to current user
    if current_user.is_authenticated:
        if order.user_id != current_user.id:
            flash('Order not found.', 'error')
            return redirect(url_for('web.account'))
    else:
        # For guest orders, you might want additional verification
        pass
    
    return render_template('web/order.html',
                         order=order,
                         format_currency=format_currency)

# AJAX endpoints
@cart_bp.route('/api/add', methods=['POST'])
def ajax_add_to_cart():
    """Add to cart via AJAX"""
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    product = Product.query.get_or_404(product_id)
    
    # Check stock
    if product.inventory and quantity > product.inventory.stock_on_hand:
        return jsonify({
            'success': False,
            'message': f'Only {product.inventory.stock_on_hand} units available.'
        })
    
    cart = get_or_create_cart()
    existing_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
    
    if existing_item:
        new_quantity = existing_item.quantity + quantity
        if product.inventory and new_quantity > product.inventory.stock_on_hand:
            return jsonify({
                'success': False,
                'message': f'Cannot add more. Only {product.inventory.stock_on_hand} units available.'
            })
        existing_item.quantity = new_quantity
    else:
        cart_item = CartItem(
            cart_id=cart.id,
            product_id=product_id,
            quantity=quantity
        )
        db.session.add(cart_item)
    
    db.session.commit()
    
    # Get updated cart count
    cart_count = cart.items.count() if cart else 0
    
    return jsonify({
        'success': True,
        'message': f'"{product.title}" added to cart.',
        'cart_count': cart_count
    })

@cart_bp.route('/api/count')
def ajax_cart_count():
    """Get cart item count via AJAX"""
    cart = get_or_create_cart()
    count = cart.items.count() if cart else 0
    return jsonify({'count': count})

@cart_bp.route('/api/validate-coupon', methods=['POST'])
def ajax_validate_coupon():
    """Validate coupon code via AJAX"""
    data = request.get_json()
    code = data.get('code')
    subtotal = data.get('subtotal', 0)
    
    coupon = validate_coupon(code, subtotal)
    
    if coupon:
        if coupon.type.value == 'PERCENT':
            discount = subtotal * coupon.value / 100
        else:  # AMOUNT
            discount = coupon.value * 100  # Convert to paisa
        
        discount = min(discount, subtotal)
        
        return jsonify({
            'valid': True,
            'discount': discount,
            'message': f'Coupon applied! You saved {format_currency(discount)}'
        })
    else:
        return jsonify({
            'valid': False,
            'message': 'Invalid or expired coupon code.'
        })

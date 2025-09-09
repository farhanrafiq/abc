from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, send_file
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy import func, desc, and_, or_, text
from datetime import datetime, timedelta
from app import db
from models import (
    Product, Category, Author, Publisher, Price, Inventory, Order, OrderItem,
    User, Review, UserRole, OrderStatus, PaymentStatus, ProductStatus,
    ContactForm, NewsletterSubscriber, product_categories
)
import logging

# Professional Admin Blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator to require admin or staff privileges"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access the admin panel.', 'error')
            return redirect(url_for('auth.login'))
        
        if current_user.role not in [UserRole.ADMIN, UserRole.STAFF]:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('web.index'))
        
        return f(*args, **kwargs)
    return decorated_function

def format_currency(amount_paisa):
    """Format currency from paisa to rupees"""
    if amount_paisa is None:
        return "₹0.00"
    return f"₹{amount_paisa / 100:,.2f}"

@admin_bp.context_processor
def inject_admin_vars():
    """Inject template variables for admin"""
    return {
        'format_currency': format_currency,
        'datetime': datetime,
        'current_user': current_user
    }

# Dashboard Route
@admin_bp.route('/')
@admin_required
def dashboard():
    """Professional admin dashboard with comprehensive analytics"""
    try:
        # Basic counts
        total_products = Product.query.count()
        total_customers = User.query.filter(User.role == UserRole.CUSTOMER).count()
        total_orders = Order.query.count()
        total_revenue = db.session.query(func.sum(Order.grand_total_inr)).filter(
            Order.payment_status == PaymentStatus.PAID
        ).scalar() or 0
        
        # Today's stats
        today = datetime.utcnow().date()
        today_orders = Order.query.filter(
            func.date(Order.created_at) == today
        ).count()
        
        today_revenue = db.session.query(func.sum(Order.grand_total_inr)).filter(
            func.date(Order.created_at) == today,
            Order.payment_status == PaymentStatus.PAID
        ).scalar() or 0
        
        # Monthly stats
        month_start = today.replace(day=1)
        monthly_orders = Order.query.filter(
            Order.created_at >= month_start
        ).count()
        
        monthly_revenue = db.session.query(func.sum(Order.grand_total_inr)).filter(
            Order.created_at >= month_start,
            Order.payment_status == PaymentStatus.PAID
        ).scalar() or 0
        
        # Recent orders
        recent_orders = Order.query.order_by(desc(Order.created_at)).limit(10).all()
        
        # Low stock products
        low_stock_products = db.session.query(Product, Inventory).join(Inventory).filter(
            Inventory.stock_on_hand <= Inventory.low_stock_threshold
        ).limit(10).all()
        
        # Top categories (simplified query)
        top_categories = db.session.query(Category.name, func.count(Product.id).label('count')).join(
            product_categories, Category.id == product_categories.c.category_id
        ).join(Product, Product.id == product_categories.c.product_id).group_by(
            Category.id, Category.name
        ).order_by(desc('count')).limit(5).all()
        
        # Recent reviews
        recent_reviews = Review.query.filter(Review.is_approved == False).order_by(
            desc(Review.created_at)
        ).limit(5).all()
        
        # Newsletter stats
        newsletter_count = NewsletterSubscriber.query.filter(
            NewsletterSubscriber.is_active == True
        ).count()
        
        # Contact forms
        unread_contacts = ContactForm.query.filter(ContactForm.status == 'unread').count()
        
        return render_template('admin/dashboard.html',
            total_products=total_products,
            total_customers=total_customers,
            total_orders=total_orders,
            total_revenue=total_revenue,
            today_orders=today_orders,
            today_revenue=today_revenue,
            monthly_orders=monthly_orders,
            monthly_revenue=monthly_revenue,
            recent_orders=recent_orders,
            low_stock_products=low_stock_products,
            top_categories=top_categories,
            recent_reviews=recent_reviews,
            newsletter_count=newsletter_count,
            unread_contacts=unread_contacts
        )
        
    except Exception as e:
        logging.error(f"Dashboard error: {str(e)}")
        flash('Error loading dashboard. Some data may be unavailable.', 'warning')
        return render_template('admin/dashboard.html',
            total_products=0,
            total_customers=0,
            total_orders=0,
            total_revenue=0,
            today_orders=0,
            today_revenue=0,
            monthly_orders=0,
            monthly_revenue=0,
            recent_orders=[],
            low_stock_products=[],
            top_categories=[],
            recent_reviews=[],
            newsletter_count=0,
            unread_contacts=0
        )

# Products Management
@admin_bp.route('/products')
@admin_required
def products():
    """Products management with search and filtering"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_id = request.args.get('category', type=int)
    status = request.args.get('status', '')
    
    query = Product.query
    
    if search:
        query = query.filter(
            or_(
                Product.title.ilike(f'%{search}%'),
                Product.isbn.ilike(f'%{search}%')
            )
        )
    
    if category_id:
        query = query.join(product_categories).filter(
            product_categories.c.category_id == category_id
        )
    
    if status:
        if status == 'active':
            query = query.filter(Product.status == ProductStatus.ACTIVE)
        elif status == 'draft':
            query = query.filter(Product.status == ProductStatus.DRAFT)
        elif status == 'archived':
            query = query.filter(Product.status == ProductStatus.ARCHIVED)
    
    products = query.paginate(
        page=page, per_page=20, error_out=False
    )
    
    categories = Category.query.all()
    
    return render_template('admin/products_new.html',
        products=products,
        categories=categories,
        search=search,
        selected_category=category_id,
        selected_status=status
    )

# Orders Management
@admin_bp.route('/orders')
@admin_required
def orders():
    """Orders management with filtering and status updates"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    search = request.args.get('search', '')
    
    query = Order.query
    
    if search:
        query = query.filter(
            or_(
                Order.email.ilike(f'%{search}%'),
                Order.name.ilike(f'%{search}%'),
                Order.id.like(f'%{search}%')
            )
        )
    
    if status:
        query = query.filter(Order.status == OrderStatus(status))
    
    orders = query.order_by(desc(Order.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/orders_new.html',
        orders=orders,
        search=search,
        selected_status=status,
        order_statuses=OrderStatus
    )

# Order Detail
@admin_bp.route('/orders/<int:order_id>')
@admin_required
def order_detail(order_id):
    """Detailed order view with status management"""
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail_new.html', order=order)

# Update Order Status
@admin_bp.route('/orders/<int:order_id>/status', methods=['POST'])
@admin_required
def update_order_status(order_id):
    """Update order status"""
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    
    try:
        order.status = OrderStatus(new_status)
        db.session.commit()
        flash(f'Order #{order.id} status updated to {new_status.title()}', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating order status', 'error')
        logging.error(f"Order status update error: {str(e)}")
    
    return redirect(url_for('admin.order_detail', order_id=order_id))

# Contact Forms Management
@admin_bp.route('/contacts')
@admin_required
def contacts():
    """Contact form management"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    search = request.args.get('search', '')
    
    query = ContactForm.query
    
    if search:
        query = query.filter(
            or_(
                ContactForm.name.ilike(f'%{search}%'),
                ContactForm.email.ilike(f'%{search}%'),
                ContactForm.subject.ilike(f'%{search}%')
            )
        )
    
    if status:
        query = query.filter(ContactForm.status == status)
    
    contacts = query.order_by(desc(ContactForm.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/contacts_new.html',
        contacts=contacts,
        search=search,
        selected_status=status
    )

# Contact Detail
@admin_bp.route('/contacts/<int:contact_id>')
@admin_required
def contact_detail(contact_id):
    """Contact form detail view"""
    contact = ContactForm.query.get_or_404(contact_id)
    
    # Mark as read
    if contact.status == 'unread':
        contact.status = 'read'
        db.session.commit()
    
    return render_template('admin/contact_detail_new.html', contact=contact)

# Respond to Contact
@admin_bp.route('/contacts/<int:contact_id>/respond', methods=['POST'])
@admin_required
def respond_to_contact(contact_id):
    """Respond to contact form"""
    contact = ContactForm.query.get_or_404(contact_id)
    response = request.form.get('response')
    
    if response:
        contact.admin_response = response
        contact.responded_at = datetime.utcnow()
        contact.responded_by = current_user.id
        contact.status = 'resolved'
        db.session.commit()
        flash('Response saved successfully!', 'success')
    else:
        flash('Response cannot be empty!', 'error')
    
    return redirect(url_for('admin.contact_detail', contact_id=contact_id))

# Users Management
@admin_bp.route('/users')
@admin_required
def users():
    """User management"""
    page = request.args.get('page', 1, type=int)
    role = request.args.get('role', '')
    search = request.args.get('search', '')
    
    query = User.query
    
    if search:
        query = query.filter(
            or_(
                User.name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )
    
    if role:
        query = query.filter(User.role == UserRole(role))
    
    users = query.order_by(desc(User.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/users_new.html',
        users=users,
        search=search,
        selected_role=role,
        user_roles=UserRole
    )

# Newsletter Management
@admin_bp.route('/newsletter')
@admin_required
def newsletter():
    """Newsletter subscriber management"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = NewsletterSubscriber.query
    
    if search:
        query = query.filter(NewsletterSubscriber.email.ilike(f'%{search}%'))
    
    subscribers = query.order_by(desc(NewsletterSubscriber.created_at)).paginate(
        page=page, per_page=50, error_out=False
    )
    
    return render_template('admin/newsletter_new.html',
        subscribers=subscribers,
        search=search
    )

# Analytics API endpoints
@admin_bp.route('/api/analytics/sales')
@admin_required
def api_analytics_sales():
    """API endpoint for sales chart data"""
    try:
        # Last 30 days sales data
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=30)
        
        sales_data = db.session.query(
            func.date(Order.created_at).label('date'),
            func.sum(Order.grand_total_inr).label('total')
        ).filter(
            Order.created_at >= start_date,
            Order.payment_status == PaymentStatus.PAID
        ).group_by(func.date(Order.created_at)).all()
        
        result = [{'date': str(row.date), 'total': row.total or 0} for row in sales_data]
        return jsonify(result)
    except Exception as e:
        logging.error(f"Sales analytics API error: {str(e)}")
        return jsonify([])

@admin_bp.route('/api/analytics/orders')
@admin_required
def api_analytics_orders():
    """API endpoint for orders chart data"""
    try:
        # Orders by status
        orders_by_status = db.session.query(
            Order.status,
            func.count(Order.id).label('count')
        ).group_by(Order.status).all()
        
        result = [{'status': row.status.value, 'count': row.count} for row in orders_by_status]
        return jsonify(result)
    except Exception as e:
        logging.error(f"Orders analytics API error: {str(e)}")
        return jsonify([])

# Settings (placeholder)
@admin_bp.route('/settings')
@admin_required
def settings():
    """Admin settings page"""
    return render_template('admin/settings_new.html')

# Error handlers - simplified to avoid template issues
@admin_bp.errorhandler(404)
def admin_not_found(error):
    return "Admin page not found", 404

@admin_bp.errorhandler(500)
def admin_internal_error(error):
    db.session.rollback()
    return f"Admin internal error: {str(error)}", 500
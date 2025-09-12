from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, send_file
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy import func, desc, and_, or_, text
from datetime import datetime, timedelta
from app import db
from models import (
    Product, Category, Author, Publisher, Price, Inventory, Order, OrderItem,
    User, Review, UserRole, OrderStatus, PaymentStatus, ProductStatus,
    ContactForm, NewsletterSubscriber, product_categories, product_authors,
    Banner, ContentPage, Coupon
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
    # Get unread contacts count
    unread_contacts = 0
    try:
        unread_contacts = ContactForm.query.filter_by(status='unread').count()
    except:
        pass
    
    return {
        'format_currency': format_currency,
        'datetime': datetime,
        'current_user': current_user,
        'unread_contacts': unread_contacts
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
        flash(f'Order #{order.id} status updated to {new_status.value.title() if new_status else "Unknown"}', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating order status', 'error')
        logging.error(f"Order status update error: {str(e)}")
    
    return redirect(url_for('admin.order_detail', order_id=order_id))

# Bulk Order Operations
@admin_bp.route('/orders/bulk-update', methods=['POST'])
@admin_required
def bulk_update_orders():
    """Bulk update order status"""
    order_ids = request.form.getlist('order_ids')
    new_status = request.form.get('bulk_status')
    
    if not order_ids or not new_status:
        flash('Please select orders and a status to update.', 'error')
        return redirect(url_for('admin.orders'))
    
    try:
        orders = Order.query.filter(Order.id.in_(order_ids)).all()
        updated_count = 0
        
        for order in orders:
            order.status = OrderStatus(new_status)
            updated_count += 1
        
        db.session.commit()
        flash(f'Successfully updated {updated_count} orders to {new_status.title()}.', 'success')
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Bulk order update error: {str(e)}")
        flash('Error updating orders. Please try again.', 'error')
    
    return redirect(url_for('admin.orders'))

# Invoice Download
@admin_bp.route('/orders/<int:order_id>/invoice')
@admin_required  
def download_invoice(order_id):
    """Download order invoice PDF"""
    order = Order.query.get_or_404(order_id)
    
    try:
        from utils.pdf import generate_invoice_pdf
        import os
        
        # Ensure invoice directory exists
        invoice_dir = "static/invoices"
        if not os.path.exists(invoice_dir):
            os.makedirs(invoice_dir)
        
        invoice_path = f"{invoice_dir}/invoice_{order.id}.pdf"
        
        # Generate PDF if it doesn't exist
        if not os.path.exists(invoice_path):
            generate_invoice_pdf(order, invoice_path)
        
        from flask import send_file
        return send_file(invoice_path, as_attachment=True, 
                        download_name=f'Invoice-{order.id}.pdf')
    
    except Exception as e:
        logging.error(f"Invoice download error: {str(e)}")
        flash('Error generating invoice. Please try again.', 'error')
        return redirect(url_for('admin.order_detail', order_id=order_id))

# Order Analytics
@admin_bp.route('/orders/analytics')
@admin_required
def order_analytics():
    """Advanced order analytics dashboard"""
    from datetime import datetime, timedelta
    from sqlalchemy import extract
    
    try:
        # Date range (last 30 days by default)
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=30)
        
        # Daily order trends
        daily_orders = db.session.query(
            func.date(Order.created_at).label('date'),
            func.count(Order.id).label('count'),
            func.sum(Order.grand_total_inr).label('revenue')
        ).filter(
            Order.created_at >= start_date
        ).group_by(func.date(Order.created_at)).all()
        
        # Order status distribution
        status_distribution = db.session.query(
            Order.status,
            func.count(Order.id).label('count')
        ).group_by(Order.status).all()
        
        # Payment method distribution
        payment_distribution = db.session.query(
            Order.payment_method,
            func.count(Order.id).label('count'),
            func.sum(Order.grand_total_inr).label('revenue')
        ).group_by(Order.payment_method).all()
        
        # Top customers
        top_customers = db.session.query(
            Order.email,
            func.count(Order.id).label('order_count'),
            func.sum(Order.grand_total_inr).label('total_spent')
        ).group_by(Order.email).order_by(
            func.sum(Order.grand_total_inr).desc()
        ).limit(10).all()
        
        return render_template('admin/order_analytics.html',
            daily_orders=daily_orders,
            status_distribution=status_distribution,
            payment_distribution=payment_distribution,
            top_customers=top_customers,
            start_date=start_date,
            end_date=end_date
        )
        
    except Exception as e:
        logging.error(f"Order analytics error: {str(e)}")
        flash('Error loading analytics. Please try again.', 'error')
        return redirect(url_for('admin.dashboard'))

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

# Additional admin routes for complete functionality
# Imports already at the top of the file

# Helper function for file uploads
def save_uploaded_file(file, folder='products'):
    """Save uploaded file and return filename"""
    if file and file.filename:
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        upload_path = os.path.join('static', 'uploads', folder)
        os.makedirs(upload_path, exist_ok=True)
        
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)
        return filename
    return None

# PRODUCT MANAGEMENT ROUTES
@admin_bp.route('/products/add', methods=['GET', 'POST'])
@admin_required
def product_add():
    """Add new product"""
    form = ProductForm()
    
    # Populate select fields
    form.publisher_id.choices = [(0, 'Select Publisher')] + [(p.id, p.name) for p in Publisher.query.all()]
    
    if form.validate_on_submit():
        try:
            # Create product
            product = Product(
                title=form.title.data,
                slug=form.slug.data,
                isbn=form.isbn.data,
                language=form.language.data,
                format=form.format.data,
                description=form.description.data,
                publisher_id=form.publisher_id.data if form.publisher_id.data != 0 else None,
                published_at=form.published_at.data,
                pages=form.data.get('pages'),
                weight_grams=form.weight_grams.data,
                dimensions_l=form.dimensions_l.data,
                dimensions_w=form.dimensions_w.data,
                dimensions_h=form.dimensions_h.data,
                status=form.status.data
            )
            
            # Handle cover image upload
            if form.cover_image.data:
                filename = save_uploaded_file(form.cover_image.data, 'products')
                if filename:
                    product.cover_image = filename
            
            db.session.add(product)
            db.session.flush()
            
            # Create price
            price = Price(
                product_id=product.id,
                mrp_inr=int(form.mrp_inr.data * 100),  # Convert to paisa
                sale_inr=int(form.sale_inr.data * 100) if form.sale_inr.data else None,
                tax_rate_pct=form.tax_rate_pct.data
            )
            db.session.add(price)
            
            # Create inventory
            inventory = Inventory(
                product_id=product.id,
                sku=form.sku.data,
                stock_on_hand=form.stock_on_hand.data,
                low_stock_threshold=form.low_stock_threshold.data
            )
            db.session.add(inventory)
            
            db.session.commit()
            flash('Product added successfully!', 'success')
            return redirect(url_for('admin.products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding product: {str(e)}', 'error')
            logging.error(f"Product add error: {str(e)}")
    
    return render_template('admin/product_form.html', form=form, title='Add Product')

@admin_bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def product_edit(product_id):
    """Edit existing product"""
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    
    # Populate select fields
    form.publisher_id.choices = [(0, 'Select Publisher')] + [(p.id, p.name) for p in Publisher.query.all()]
    
    if request.method == 'GET':
        # Populate form with existing data
        if product.price:
            form.mrp_inr.data = product.price.mrp_inr / 100
            form.sale_inr.data = product.price.sale_inr / 100 if product.price.sale_inr else None
            form.tax_rate_pct.data = product.price.tax_rate_pct
        
        if product.inventory:
            form.sku.data = product.inventory.sku
            form.stock_on_hand.data = product.inventory.stock_on_hand
            form.low_stock_threshold.data = product.inventory.low_stock_threshold
    
    if form.validate_on_submit():
        try:
            # Update product
            product.title = form.title.data
            product.slug = form.slug.data
            product.isbn = form.isbn.data
            product.language = form.language.data
            product.format = form.format.data
            product.description = form.description.data
            product.publisher_id = form.publisher_id.data if form.publisher_id.data != 0 else None
            product.published_at = form.published_at.data
            product.pages = form.data.get('pages')
            product.weight_grams = form.weight_grams.data
            product.dimensions_l = form.dimensions_l.data
            product.dimensions_w = form.dimensions_w.data
            product.dimensions_h = form.dimensions_h.data
            product.status = form.status.data
            
            # Handle cover image upload
            if form.cover_image.data:
                filename = save_uploaded_file(form.cover_image.data, 'products')
                if filename:
                    product.cover_image = filename
            
            # Update or create price
            if product.price:
                product.price.mrp_inr = int(form.mrp_inr.data * 100)
                product.price.sale_inr = int(form.sale_inr.data * 100) if form.sale_inr.data else None
                product.price.tax_rate_pct = form.tax_rate_pct.data
            else:
                price = Price(
                    product_id=product.id,
                    mrp_inr=int(form.mrp_inr.data * 100),
                    sale_inr=int(form.sale_inr.data * 100) if form.sale_inr.data else None,
                    tax_rate_pct=form.tax_rate_pct.data
                )
                db.session.add(price)
            
            # Update or create inventory
            if product.inventory:
                product.inventory.sku = form.sku.data
                product.inventory.stock_on_hand = form.stock_on_hand.data
                product.inventory.low_stock_threshold = form.low_stock_threshold.data
            else:
                inventory = Inventory(
                    product_id=product.id,
                    sku=form.sku.data,
                    stock_on_hand=form.stock_on_hand.data,
                    low_stock_threshold=form.low_stock_threshold.data
                )
                db.session.add(inventory)
            
            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('admin.products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating product: {str(e)}', 'error')
            logging.error(f"Product update error: {str(e)}")
    
    return render_template('admin/product_form.html', form=form, product=product, title='Edit Product')

@admin_bp.route('/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def product_delete(product_id):
    """Delete product"""
    try:
        product = Product.query.get_or_404(product_id)
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting product: {str(e)}', 'error')
    
    return redirect(url_for('admin.products'))

# CATEGORY MANAGEMENT ROUTES
@admin_bp.route('/categories')
@admin_required
def categories():
    """List all categories"""
    categories = Category.query.order_by(Category.sort_order, Category.name).all()
    return render_template('admin/categories.html', categories=categories)

@admin_bp.route('/categories/add', methods=['GET', 'POST'])
@admin_required
def category_add():
    """Add new category"""
    form = CategoryForm()
    
    # Set parent choices
    form.parent_id.choices = [(0, 'No Parent')] + [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        try:
            category = Category(
                name=form.name.data,
                slug=form.slug.data,
                description=form.description.data,
                parent_id=form.parent_id.data if form.parent_id.data != 0 else None,
                sort_order=form.sort_order.data,
                is_active=form.is_active.data
            )
            
            # Handle image upload
            if form.image.data:
                filename = save_uploaded_file(form.image.data, 'categories')
                if filename:
                    category.image = filename
            
            db.session.add(category)
            db.session.commit()
            flash('Category added successfully!', 'success')
            return redirect(url_for('admin.categories'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding category: {str(e)}', 'error')
    
    return render_template('admin/category_form.html', form=form, title='Add Category')

@admin_bp.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@admin_required
def category_edit(category_id):
    """Edit category"""
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)
    
    # Set parent choices (exclude self and children)
    form.parent_id.choices = [(0, 'No Parent')]
    for c in Category.query.all():
        if c.id != category_id:  # Simple check, should be more complex for children
            form.parent_id.choices.append((c.id, c.name))
    
    if form.validate_on_submit():
        try:
            category.name = form.name.data
            category.slug = form.slug.data
            category.description = form.description.data
            category.parent_id = form.parent_id.data if form.parent_id.data != 0 else None
            category.sort_order = form.sort_order.data
            category.is_active = form.is_active.data
            
            # Handle image upload
            if form.image.data:
                filename = save_uploaded_file(form.image.data, 'categories')
                if filename:
                    category.image = filename
            
            db.session.commit()
            flash('Category updated successfully!', 'success')
            return redirect(url_for('admin.categories'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating category: {str(e)}', 'error')
    
    return render_template('admin/category_form.html', form=form, category=category, title='Edit Category')

@admin_bp.route('/categories/delete/<int:category_id>', methods=['POST'])
@admin_required
def category_delete(category_id):
    """Delete category"""
    try:
        category = Category.query.get_or_404(category_id)
        db.session.delete(category)
        db.session.commit()
        flash('Category deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting category: {str(e)}', 'error')
    
    return redirect(url_for('admin.categories'))

# AUTHOR MANAGEMENT ROUTES
@admin_bp.route('/authors')
@admin_required
def authors():
    """List all authors"""
    page = request.args.get('page', 1, type=int)
    authors = Author.query.order_by(Author.name).paginate(page=page, per_page=20)
    return render_template('admin/authors.html', authors=authors)

@admin_bp.route('/authors/add', methods=['GET', 'POST'])
@admin_required
def author_add():
    """Add new author"""
    form = AuthorForm()
    
    if form.validate_on_submit():
        try:
            author = Author(
                name=form.name.data,
                slug=form.slug.data,
                bio=form.bio.data,
                website=form.website.data
            )
            
            # Handle image upload
            if form.image.data:
                filename = save_uploaded_file(form.image.data, 'authors')
                if filename:
                    author.image = filename
            
            db.session.add(author)
            db.session.commit()
            flash('Author added successfully!', 'success')
            return redirect(url_for('admin.authors'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding author: {str(e)}', 'error')
    
    return render_template('admin/author_form.html', form=form, title='Add Author')

@admin_bp.route('/authors/edit/<int:author_id>', methods=['GET', 'POST'])
@admin_required
def author_edit(author_id):
    """Edit author"""
    author = Author.query.get_or_404(author_id)
    form = AuthorForm(obj=author)
    
    if form.validate_on_submit():
        try:
            author.name = form.name.data
            author.slug = form.slug.data
            author.bio = form.bio.data
            author.website = form.website.data
            
            # Handle image upload
            if form.image.data:
                filename = save_uploaded_file(form.image.data, 'authors')
                if filename:
                    author.image = filename
            
            db.session.commit()
            flash('Author updated successfully!', 'success')
            return redirect(url_for('admin.authors'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating author: {str(e)}', 'error')
    
    return render_template('admin/author_form.html', form=form, author=author, title='Edit Author')

@admin_bp.route('/authors/delete/<int:author_id>', methods=['POST'])
@admin_required
def author_delete(author_id):
    """Delete author"""
    try:
        author = Author.query.get_or_404(author_id)
        db.session.delete(author)
        db.session.commit()
        flash('Author deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting author: {str(e)}', 'error')
    
    return redirect(url_for('admin.authors'))

# PUBLISHER MANAGEMENT ROUTES
@admin_bp.route('/publishers')
@admin_required
def publishers():
    """List all publishers"""
    page = request.args.get('page', 1, type=int)
    publishers = Publisher.query.order_by(Publisher.name).paginate(page=page, per_page=20)
    return render_template('admin/publishers.html', publishers=publishers)

@admin_bp.route('/publishers/add', methods=['GET', 'POST'])
@admin_required
def publisher_add():
    """Add new publisher"""
    form = PublisherForm()
    
    if form.validate_on_submit():
        try:
            publisher = Publisher(
                name=form.name.data,
                slug=form.slug.data,
                description=form.description.data,
                website=form.website.data
            )
            
            # Handle image upload
            if form.logo.data:
                filename = save_uploaded_file(form.logo.data, 'publishers')
                if filename:
                    publisher.logo = filename
            
            db.session.add(publisher)
            db.session.commit()
            flash('Publisher added successfully!', 'success')
            return redirect(url_for('admin.publishers'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding publisher: {str(e)}', 'error')
    
    return render_template('admin/publisher_form.html', form=form, title='Add Publisher')

@admin_bp.route('/publishers/edit/<int:publisher_id>', methods=['GET', 'POST'])
@admin_required
def publisher_edit(publisher_id):
    """Edit publisher"""
    publisher = Publisher.query.get_or_404(publisher_id)
    form = PublisherForm(obj=publisher)
    
    if form.validate_on_submit():
        try:
            publisher.name = form.name.data
            publisher.slug = form.slug.data
            publisher.description = form.description.data
            publisher.website = form.website.data
            
            # Handle image upload
            if form.logo.data:
                filename = save_uploaded_file(form.logo.data, 'publishers')
                if filename:
                    publisher.logo = filename
            
            db.session.commit()
            flash('Publisher updated successfully!', 'success')
            return redirect(url_for('admin.publishers'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating publisher: {str(e)}', 'error')
    
    return render_template('admin/publisher_form.html', form=form, publisher=publisher, title='Edit Publisher')

@admin_bp.route('/publishers/delete/<int:publisher_id>', methods=['POST'])
@admin_required
def publisher_delete(publisher_id):
    """Delete publisher"""
    try:
        publisher = Publisher.query.get_or_404(publisher_id)
        db.session.delete(publisher)
        db.session.commit()
        flash('Publisher deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting publisher: {str(e)}', 'error')
    
    return redirect(url_for('admin.publishers'))

# REVIEW MANAGEMENT ROUTES
@admin_bp.route('/reviews')
@admin_required
def reviews():
    """List all reviews"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'pending')
    
    query = Review.query
    if status == 'pending':
        query = query.filter_by(is_approved=False)
    elif status == 'approved':
        query = query.filter_by(is_approved=True)
    
    reviews = query.order_by(Review.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/reviews.html', reviews=reviews, status=status)

@admin_bp.route('/reviews/approve/<int:review_id>', methods=['POST'])
@admin_required
def review_approve(review_id):
    """Approve review"""
    try:
        review = Review.query.get_or_404(review_id)
        review.is_approved = True
        db.session.commit()
        flash('Review approved successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error approving review: {str(e)}', 'error')
    
    return redirect(url_for('admin.reviews'))

@admin_bp.route('/reviews/delete/<int:review_id>', methods=['POST'])
@admin_required
def review_delete(review_id):
    """Delete review"""
    try:
        review = Review.query.get_or_404(review_id)
        db.session.delete(review)
        db.session.commit()
        flash('Review deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting review: {str(e)}', 'error')
    
    return redirect(url_for('admin.reviews'))

# COUPON MANAGEMENT ROUTES
@admin_bp.route('/coupons')
@admin_required
def coupons():
    """List all coupons"""
    coupons = Coupon.query.order_by(Coupon.created_at.desc()).all()
    return render_template('admin/coupons.html', coupons=coupons)

# BANNER MANAGEMENT ROUTES
@admin_bp.route('/banners')
@admin_required
def banners():
    """List all banners"""
    banners = Banner.query.order_by(Banner.sort_order).all()
    return render_template('admin/banners.html', banners=banners)

# CONTENT BLOCKS ROUTES
@admin_bp.route('/content_blocks')
@admin_required
def content_blocks():
    """List all content blocks"""
    content_pages = ContentPage.query.order_by(ContentPage.created_at.desc()).all()
    return render_template('admin/content_blocks.html', content_pages=content_pages)

# ANALYTICS ROUTES
@admin_bp.route('/analytics')
@admin_required
def analytics():
    """Analytics dashboard"""
    # Analytics data
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    # Date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    # Sales data
    from models import Order, PaymentStatus
    sales_data = db.session.query(
        func.date(Order.created_at).label('date'),
        func.sum(Order.grand_total_inr).label('total')
    ).filter(
        Order.created_at >= start_date,
        Order.payment_status == PaymentStatus.PAID
    ).group_by(func.date(Order.created_at)).all()
    
    # Top products
    from models import OrderItem
    top_products = db.session.query(
        Product.title,
        func.sum(OrderItem.quantity).label('total_sold')
    ).join(OrderItem).group_by(Product.id).order_by(
        func.sum(OrderItem.quantity).desc()
    ).limit(10).all()
    
    return render_template('admin/analytics.html', 
                         sales_data=sales_data, 
                         top_products=top_products)
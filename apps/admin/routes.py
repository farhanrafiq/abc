from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify, send_file
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy import func, desc, and_, or_
from models import (Product, Category, Author, Publisher, Price, Inventory, Order, OrderItem, 
                   User, Review, Coupon, Setting, UserRole, OrderStatus, PaymentStatus, ProductStatus)
from forms import (ProductForm, AuthorForm, PublisherForm, CategoryForm, CouponForm, UserForm)
from utils.helpers import format_currency, save_uploaded_file, generate_slug, paginate_query
from utils.pdf import generate_invoice_pdf
from app import db
from datetime import datetime, timedelta
import csv
import io
import logging

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin or staff role"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in [UserRole.ADMIN, UserRole.STAFF]:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('web.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard with KPIs and analytics"""
    today = datetime.utcnow().date()
    month_start = today.replace(day=1)
    
    # Today's stats
    today_orders = Order.query.filter(
        func.date(Order.created_at) == today
    ).count()
    
    today_sales = db.session.query(func.sum(Order.grand_total_inr)).filter(
        func.date(Order.created_at) == today,
        Order.payment_status == PaymentStatus.PAID
    ).scalar() or 0
    
    # Month-to-date stats
    mtd_orders = Order.query.filter(
        Order.created_at >= month_start
    ).count()
    
    mtd_sales = db.session.query(func.sum(Order.grand_total_inr)).filter(
        Order.created_at >= month_start,
        Order.payment_status == PaymentStatus.PAID
    ).scalar() or 0
    
    # Average order value
    aov = db.session.query(func.avg(Order.grand_total_inr)).filter(
        Order.payment_status == PaymentStatus.PAID
    ).scalar() or 0
    
    # Top categories by sales
    top_categories = db.session.query(
        Category.name,
        func.sum(OrderItem.line_total_inr).label('total_sales')
    ).join(Product.categories).join(OrderItem)\
    .join(Order).filter(Order.payment_status == PaymentStatus.PAID)\
    .group_by(Category.id, Category.name)\
    .order_by(desc('total_sales')).limit(5).all()
    
    # Recent orders
    recent_orders = Order.query.order_by(desc(Order.created_at)).limit(10).all()
    
    # Low stock products
    low_stock_products = db.session.query(Product).join(Inventory)\
        .filter(Inventory.stock_on_hand <= Inventory.low_stock_threshold)\
        .limit(10).all()
    
    # Pending reviews
    pending_reviews = Review.query.filter_by(is_approved=False).count()
    
    return render_template('admin/dashboard.html',
                         today_orders=today_orders,
                         today_sales=today_sales,
                         mtd_orders=mtd_orders,
                         mtd_sales=mtd_sales,
                         aov=aov,
                         top_categories=top_categories,
                         recent_orders=recent_orders,
                         low_stock_products=low_stock_products,
                         pending_reviews=pending_reviews,
                         format_currency=format_currency)

@admin_bp.route('/products')
@admin_required
def products():
    """Product management listing"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_id = request.args.get('category', type=int)
    status = request.args.get('status', '')
    
    query = Product.query
    
    # Search filter
    if search:
        query = query.filter(or_(
            Product.title.ilike(f'%{search}%'),
            Product.isbn.ilike(f'%{search}%')
        ))
    
    # Category filter
    if category_id:
        query = query.join(Product.categories).filter(Category.id == category_id)
    
    # Status filter
    if status:
        query = query.filter(Product.status == status)
    
    query = query.order_by(desc(Product.created_at))
    products = paginate_query(query, page, 20)
    
    # Get filter options
    categories = Category.query.all()
    
    return render_template('admin/products.html',
                         products=products,
                         categories=categories,
                         search=search,
                         selected_category=category_id,
                         selected_status=status)

@admin_bp.route('/products/new', methods=['GET', 'POST'])
@admin_required
def product_new():
    """Create new product"""
    form = ProductForm()
    
    # Populate choices
    form.publisher_id.choices = [('', 'Select Publisher')] + [(p.id, p.name) for p in Publisher.query.all()]
    
    if form.validate_on_submit():
        # Create product
        product = Product(
            title=form.title.data,
            slug=form.slug.data or generate_slug(form.title.data),
            isbn=form.isbn.data,
            language=Language(form.language.data) if form.language.data else Language.ENGLISH,
            format=Format(form.format.data) if form.format.data else Format.PAPERBACK,
            description=form.description.data,
            publisher_id=form.publisher_id.data if form.publisher_id.data else None,
            published_at=form.published_at.data,
            weight_grams=form.weight_grams.data,
            dimensions_l=form.dimensions_l.data,
            dimensions_w=form.dimensions_w.data,
            dimensions_h=form.dimensions_h.data,
            status=ProductStatus(form.status.data)
        )
        
        # Handle cover image upload
        if form.cover_image.data:
            filename = save_uploaded_file(form.cover_image.data, 'products')
            if filename:
                product.cover_image = filename
        
        db.session.add(product)
        db.session.flush()  # To get product.id
        
        # Create price
        price = Price(
            product_id=product.id,
            mrp_inr=int(form.mrp_inr.data * 100),  # Convert to paisa
            sale_inr=int(form.sale_inr.data * 100) if form.sale_inr.data else None,
            tax_rate_pct=form.tax_rate_pct.data or 0.0
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
        flash('Product created successfully!', 'success')
        return redirect(url_for('admin.products'))
    
    return render_template('admin/product_form.html', form=form, product=None)

@admin_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@admin_required
def product_edit(product_id):
    """Edit existing product"""
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    
    # Populate choices
    form.publisher_id.choices = [('', 'Select Publisher')] + [(p.id, p.name) for p in Publisher.query.all()]
    
    # Populate form with existing data
    if request.method == 'GET':
        if product.price:
            form.mrp_inr.data = product.price.mrp_inr / 100  # Convert from paisa
            form.sale_inr.data = product.price.sale_inr / 100 if product.price.sale_inr else None
            form.tax_rate_pct.data = product.price.tax_rate_pct
        
        if product.inventory:
            form.sku.data = product.inventory.sku
            form.stock_on_hand.data = product.inventory.stock_on_hand
            form.low_stock_threshold.data = product.inventory.low_stock_threshold
    
    if form.validate_on_submit():
        # Update product
        product.title = form.title.data
        product.slug = form.slug.data
        product.isbn = form.isbn.data
        product.language = Language(form.language.data) if form.language.data else Language.ENGLISH
        product.format = Format(form.format.data) if form.format.data else Format.PAPERBACK
        product.description = form.description.data
        product.publisher_id = form.publisher_id.data if form.publisher_id.data else None
        product.published_at = form.published_at.data
        product.weight_grams = form.weight_grams.data
        product.dimensions_l = form.dimensions_l.data
        product.dimensions_w = form.dimensions_w.data
        product.dimensions_h = form.dimensions_h.data
        product.status = ProductStatus(form.status.data)
        
        # Handle cover image upload
        if form.cover_image.data:
            filename = save_uploaded_file(form.cover_image.data, 'products')
            if filename:
                product.cover_image = filename
        
        # Update or create price
        if product.price:
            product.price.mrp_inr = int(form.mrp_inr.data * 100)
            product.price.sale_inr = int(form.sale_inr.data * 100) if form.sale_inr.data else None
            product.price.tax_rate_pct = form.tax_rate_pct.data or 0.0
        else:
            price = Price(
                product_id=product.id,
                mrp_inr=int(form.mrp_inr.data * 100),
                sale_inr=int(form.sale_inr.data * 100) if form.sale_inr.data else None,
                tax_rate_pct=form.tax_rate_pct.data or 0.0
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
    
    return render_template('admin/product_form.html', form=form, product=product)

@admin_bp.route('/orders')
@admin_required
def orders():
    """Order management listing"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    
    query = Order.query
    
    # Search filter
    if search:
        query = query.filter(or_(
            Order.id.like(f'%{search}%'),
            Order.email.ilike(f'%{search}%'),
            Order.phone.ilike(f'%{search}%')
        ))
    
    # Status filter
    if status:
        query = query.filter(Order.status == status)
    
    query = query.order_by(desc(Order.created_at))
    orders = paginate_query(query, page, 20)
    
    return render_template('admin/orders.html',
                         orders=orders,
                         search=search,
                         selected_status=status,
                         OrderStatus=OrderStatus,
                         format_currency=format_currency)

@admin_bp.route('/orders/<int:order_id>')
@admin_required
def order_detail(order_id):
    """Order detail page"""
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html',
                         order=order,
                         format_currency=format_currency)

@admin_bp.route('/orders/<int:order_id>/update_status', methods=['POST'])
@admin_required
def update_order_status(order_id):
    """Update order status"""
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    
    if new_status in [status.value for status in OrderStatus]:
        order.status = OrderStatus(new_status)
        db.session.commit()
        flash(f'Order status updated to {new_status}', 'success')
    else:
        flash('Invalid status', 'error')
    
    return redirect(url_for('admin.order_detail', order_id=order_id))

@admin_bp.route('/orders/<int:order_id>/invoice')
@admin_required
def order_invoice(order_id):
    """Generate and download order invoice"""
    order = Order.query.get_or_404(order_id)
    
    # Generate PDF
    pdf_buffer = generate_invoice_pdf(order)
    
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f'invoice_{order.id}.pdf',
        mimetype='application/pdf'
    )

@admin_bp.route('/authors')
@admin_required
def authors():
    """Author management"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Author.query
    if search:
        query = query.filter(Author.name.ilike(f'%{search}%'))
    
    query = query.order_by(Author.name)
    authors = paginate_query(query, page, 20)
    
    return render_template('admin/authors.html', authors=authors, search=search)

@admin_bp.route('/authors/new', methods=['GET', 'POST'])
@admin_required
def author_new():
    """Create new author"""
    form = AuthorForm()
    
    if form.validate_on_submit():
        author = Author(
            name=form.name.data,
            slug=form.slug.data or generate_slug(form.name.data),
            bio=form.bio.data
        )
        db.session.add(author)
        db.session.commit()
        flash('Author created successfully!', 'success')
        return redirect(url_for('admin.authors'))
    
    return render_template('admin/author_form.html', form=form, author=None)

@admin_bp.route('/publishers')
@admin_required
def publishers():
    """Publisher management"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Publisher.query
    if search:
        query = query.filter(Publisher.name.ilike(f'%{search}%'))
    
    query = query.order_by(Publisher.name)
    publishers = paginate_query(query, page, 20)
    
    return render_template('admin/publishers.html', publishers=publishers, search=search)

@admin_bp.route('/categories')
@admin_required
def categories():
    """Category management"""
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/categories.html', categories=categories)

@admin_bp.route('/reviews')
@admin_required
def reviews():
    """Review management"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'pending')
    
    query = Review.query.join(Product).join(User)
    
    if status == 'pending':
        query = query.filter(Review.is_approved == False)
    elif status == 'approved':
        query = query.filter(Review.is_approved == True)
    
    query = query.order_by(desc(Review.created_at))
    reviews = paginate_query(query, page, 20)
    
    return render_template('admin/reviews.html', reviews=reviews, status=status)

@admin_bp.route('/reviews/<int:review_id>/approve', methods=['POST'])
@admin_required
def approve_review(review_id):
    """Approve a review"""
    review = Review.query.get_or_404(review_id)
    review.is_approved = True
    db.session.commit()
    flash('Review approved successfully!', 'success')
    return redirect(url_for('admin.reviews'))

@admin_bp.route('/reviews/<int:review_id>/reject', methods=['POST'])
@admin_required
def reject_review(review_id):
    """Reject a review"""
    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()
    flash('Review rejected and deleted.', 'success')
    return redirect(url_for('admin.reviews'))

@admin_bp.route('/coupons')
@admin_required
def coupons():
    """Coupon management"""
    page = request.args.get('page', 1, type=int)
    coupons = paginate_query(Coupon.query.order_by(desc(Coupon.created_at)), page, 20)
    return render_template('admin/coupons.html', coupons=coupons)

@admin_bp.route('/settings')
@admin_required
def settings():
    """Store settings"""
    # Get all settings
    settings_dict = {}
    settings = Setting.query.all()
    for setting in settings:
        settings_dict[setting.key] = setting.value
    
    return render_template('admin/settings.html', settings=settings_dict)

@admin_bp.route('/settings/update', methods=['POST'])
@admin_required
def update_settings():
    """Update store settings"""
    for key, value in request.form.items():
        if key.startswith('setting_'):
            setting_key = key.replace('setting_', '')
            setting = Setting.query.filter_by(key=setting_key).first()
            if setting:
                setting.value = value
            else:
                setting = Setting(key=setting_key, value=value)
                db.session.add(setting)
    
    db.session.commit()
    flash('Settings updated successfully!', 'success')
    return redirect(url_for('admin.settings'))

@admin_bp.route('/export/products')
@admin_required
def export_products():
    """Export products to CSV"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Title', 'ISBN', 'Language', 'Format', 'Publisher', 'MRP', 'Sale Price', 'Stock', 'Status'])
    
    # Write products
    products = db.session.query(Product).join(Price).join(Inventory).all()
    for product in products:
        writer.writerow([
            product.id,
            product.title,
            product.isbn or '',
            product.language.value if product.language else '',
            product.format.value if product.format else '',
            product.publisher.name if product.publisher else '',
            product.price.mrp_inr / 100 if product.price else 0,
            product.price.sale_inr / 100 if product.price and product.price.sale_inr else '',
            product.inventory.stock_on_hand if product.inventory else 0,
            product.status.value
        ])
    
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        as_attachment=True,
        download_name='products.csv',
        mimetype='text/csv'
    )

# AJAX endpoints
@admin_bp.route('/api/products/<int:product_id>/toggle_status', methods=['POST'])
@admin_required
def toggle_product_status(product_id):
    """Toggle product status via AJAX"""
    product = Product.query.get_or_404(product_id)
    
    if product.status == ProductStatus.ACTIVE:
        product.status = ProductStatus.ARCHIVED
    else:
        product.status = ProductStatus.ACTIVE
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'new_status': product.status.value
    })

@admin_bp.route('/api/inventory/<int:product_id>/update', methods=['POST'])
@admin_required
def update_inventory(product_id):
    """Update product inventory via AJAX"""
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    
    if product.inventory:
        product.inventory.stock_on_hand = data.get('stock', 0)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'new_stock': product.inventory.stock_on_hand
        })
    
    return jsonify({'success': False, 'error': 'No inventory record found'})

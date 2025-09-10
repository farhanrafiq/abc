from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_, func, desc, asc
from models import Product, Category, Author, Publisher, Price, Inventory, Review, ContentPage, ProductStatus, Language, Format, Banner, FeaturedCategory, BannerType, HomeSection, SectionType, MediaAsset, NewsletterSubscriber, ContactForm, Order, OrderItem, product_categories, product_authors
from forms import SearchForm, ReviewForm
from utils.helpers import format_currency, get_cart_count, paginate_query
from app import db
import logging

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def index():
    """Dynamic homepage with configurable sections"""
    # Get active homepage sections
    sections = HomeSection.get_scheduled_active_sections()
    
    # Render each section with its data
    rendered_sections = []
    for section in sections:
        section_data = get_section_data(section)
        rendered_sections.append({
            'section': section,
            'data': section_data
        })
    
    return render_template('web/index_dynamic.html',
                         sections=rendered_sections)

def get_section_data(section):
    """Get data needed to render a section"""
    data = {}
    
    if section.type == SectionType.HERO_SLIDER:
        # Get hero banners for slider
        data['hero_banners'] = Banner.query\
            .filter(Banner.banner_type == BannerType.HERO, Banner.is_active == True)\
            .order_by(Banner.sort_order, Banner.created_at.desc())\
            .all()
    
    elif section.type in [SectionType.FEATURED_COLLECTION, SectionType.NEW_ARRIVALS, SectionType.BESTSELLERS]:
        data_source = section.get_config_value('data_source', 'query')
        limit = section.get_config_value('limit', 8)
        
        if data_source == 'manual':
            product_ids = section.get_config_value('manual_product_ids', [])
            products = Product.query.filter(Product.id.in_(product_ids)).limit(limit).all()
        else:
            query_config = section.get_config_value('query', {})
            category_slug = query_config.get('category_slug')
            sort_by = query_config.get('sort', 'newest')
            
            query = Product.query.join(Price).join(Inventory)\
                .filter(Product.status == ProductStatus.ACTIVE)\
                .filter(Inventory.stock_on_hand > 0)
            
            if category_slug:
                query = query.join(product_categories).join(Category).filter(Category.slug == category_slug)
            
            if sort_by == 'newest':
                query = query.order_by(desc(Product.created_at))
            elif sort_by == 'price_low':
                query = query.order_by(asc(Price.sale_inr))
            elif sort_by == 'price_high':
                query = query.order_by(desc(Price.sale_inr))
            elif section.type == SectionType.BESTSELLERS:
                query = query.outerjoin(Review)\
                    .group_by(Product.id, Price.id, Inventory.product_id)\
                    .order_by(desc(func.count(Review.id)))
            
            products = query.limit(limit).all()
        
        data['products'] = products
    
    elif section.type == SectionType.AUTHOR_SPOTLIGHT:
        author_id = section.get_config_value('author_id')
        if author_id:
            data['author'] = Author.query.get(author_id)
    
    elif section.type == SectionType.PUBLISHER_SPOTLIGHT:
        publisher_id = section.get_config_value('publisher_id')
        if publisher_id:
            data['publisher'] = Publisher.query.get(publisher_id)
    
    elif section.type == SectionType.STAFF_PICKS:
        items = section.get_config_value('items', [])
        staff_picks = []
        for item in items:
            product = Product.query.get(item.get('product_id'))
            if product:
                staff_picks.append({
                    'product': product,
                    'editor_note': item.get('editor_note', '')
                })
        data['staff_picks'] = staff_picks
    
    return data

@web_bp.route('/catalog')
@web_bp.route('/catalog/<category_slug>')
def catalog(category_slug=None):
    """Product catalog with filtering and search"""
    form = SearchForm(request.args)
    
    # Base query
    query = db.session.query(Product).join(Price).join(Inventory)\
        .filter(Product.status == ProductStatus.ACTIVE)
    
    # Category filter
    selected_category = None
    if category_slug:
        selected_category = Category.query.filter_by(slug=category_slug).first_or_404()
        query = query.join(product_categories).join(Category).filter(Category.id == selected_category.id)
    elif form.category.data:
        query = query.join(product_categories).join(Category).filter(Category.id == form.category.data)
    
    # Search filter
    if form.q.data:
        search_term = f"%{form.q.data}%"
        query = query.filter(or_(
            Product.title.ilike(search_term),
            Product.isbn.ilike(search_term),
            Product.description.ilike(search_term)
        ))
    
    # Author filter
    if form.author.data:
        query = query.join(product_authors).join(Author).filter(Author.id == form.author.data)
    
    # Publisher filter
    if form.publisher.data:
        query = query.filter(Product.publisher_id == form.publisher.data)
    
    # Language filter
    if form.language.data:
        query = query.filter(Product.language == form.language.data)
    
    # Format filter
    if form.format.data:
        query = query.filter(Product.format == form.format.data)
    
    # Price filter
    if form.min_price.data:
        min_price_paisa = int(form.min_price.data * 100)
        query = query.filter(
            func.coalesce(Price.sale_inr, Price.mrp_inr) >= min_price_paisa
        )
    
    if form.max_price.data:
        max_price_paisa = int(form.max_price.data * 100)
        query = query.filter(
            func.coalesce(Price.sale_inr, Price.mrp_inr) <= max_price_paisa
        )
    
    # Stock filter
    if form.in_stock.data:
        query = query.filter(Inventory.stock_on_hand > 0)
    
    # Sorting
    sort_by = form.sort.data or 'newest'
    if sort_by == 'newest':
        query = query.order_by(desc(Product.created_at))
    elif sort_by == 'price_asc':
        query = query.order_by(asc(func.coalesce(Price.sale_inr, Price.mrp_inr)))
    elif sort_by == 'price_desc':
        query = query.order_by(desc(func.coalesce(Price.sale_inr, Price.mrp_inr)))
    elif sort_by == 'title_asc':
        query = query.order_by(asc(Product.title))
    elif sort_by == 'title_desc':
        query = query.order_by(desc(Product.title))
    else:  # relevance - default to newest for now
        query = query.order_by(desc(Product.created_at))
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    products = paginate_query(query, page, current_app.config.get('PRODUCTS_PER_PAGE', 20))
    
    # Get filter options
    categories = Category.query.all()
    authors = Author.query.all()
    publishers = Publisher.query.all()
    
    # Populate form choices
    form.category.choices = [('', 'All Categories')] + [(c.id, c.name) for c in categories]
    form.author.choices = [('', 'All Authors')] + [(a.id, a.name) for a in authors]
    form.publisher.choices = [('', 'All Publishers')] + [(p.id, p.name) for p in publishers]
    
    return render_template('web/catalog.html',
                         products=products,
                         form=form,
                         selected_category=selected_category,
                         categories=categories,
                         all_categories=categories)

@web_bp.route('/product/<slug>')
def product_detail(slug):
    """Individual product page"""
    product = Product.query.filter_by(slug=slug, status=ProductStatus.ACTIVE).first_or_404()
    
    # Get related products (same category)
    related_products = []
    if product.categories:
        related_products = db.session.query(Product).join(Price).join(Inventory)\
            .join(product_categories).join(Category)\
            .filter(Category.id.in_([c.id for c in product.categories]))\
            .filter(Product.id != product.id)\
            .filter(Product.status == ProductStatus.ACTIVE)\
            .filter(Inventory.stock_on_hand > 0)\
            .limit(4).all()
    
    # Get product reviews
    reviews = Review.query.filter_by(product_id=product.id, is_approved=True)\
        .order_by(desc(Review.created_at)).limit(10).all()
    
    # Review form
    review_form = ReviewForm()
    
    return render_template('web/product.html',
                         product=product,
                         related_products=related_products,
                         reviews=reviews,
                         review_form=review_form)

@web_bp.route('/search')
def search():
    """Search results page"""
    form = SearchForm(request.args)
    
    if not form.q.data:
        flash('Please enter a search term.', 'warning')
        return redirect(url_for('web.catalog'))
    
    # Enhanced PostgreSQL full-text search
    search_query = form.q.data.strip()
    
    # Clean search query for full-text search
    import re
    clean_query = re.sub(r'[^\w\s]', ' ', search_query)
    search_vector = ' & '.join(clean_query.split())
    
    # Full-text search with ranking
    from sqlalchemy import text
    query = db.session.query(Product).join(Price).join(Inventory)\
        .outerjoin(product_authors).outerjoin(Author)\
        .filter(Product.status == ProductStatus.ACTIVE)
    
    if len(search_query) >= 3:
        # Use PostgreSQL full-text search for better performance
        fts_query = text("""
            to_tsvector('english', 
                COALESCE(product.title, '') || ' ' || 
                COALESCE(product.description, '') || ' ' ||
                COALESCE(product.isbn, '') || ' ' ||
                COALESCE(string_agg(author.name, ' '), '')
            ) @@ plainto_tsquery('english', :search_term)
        """)
        
        query = query.group_by(Product.id, Price.id, Inventory.id)\
            .having(fts_query).params(search_term=search_query)
    else:
        # Fallback to ILIKE for short queries
        search_term = f"%{search_query}%"
        query = query.filter(or_(
            Product.title.ilike(search_term),
            Product.isbn.ilike(search_term),
            Product.description.ilike(search_term),
            Author.name.ilike(search_term)
        ))
    
    # Apply additional filters
    if form.category.data:
        query = query.join(product_categories).join(Category).filter(Category.id == form.category.data)
    
    if form.language.data:
        query = query.filter(Product.language == form.language.data)
    
    if form.format.data:
        query = query.filter(Product.format == form.format.data)
    
    if form.in_stock.data:
        query = query.filter(Inventory.stock_on_hand > 0)
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    products = paginate_query(query.distinct(), page, current_app.config.get('PRODUCTS_PER_PAGE', 20))
    
    # Get filter options
    categories = Category.query.all()
    form.category.choices = [('', 'All Categories')] + [(c.id, c.name) for c in categories]
    
    return render_template('web/search.html',
                         products=products,
                         form=form,
                         search_term=form.q.data)

@web_bp.route('/product/<int:product_id>/review', methods=['POST'])
@login_required
def add_review(product_id):
    """Add a product review"""
    product = Product.query.get_or_404(product_id)
    form = ReviewForm()
    
    if form.validate_on_submit():
        # Check if user already reviewed this product
        existing_review = Review.query.filter_by(
            product_id=product_id,
            user_id=current_user.id
        ).first()
        
        if existing_review:
            flash('You have already reviewed this product.', 'warning')
        else:
            review = Review()
            review.product_id = product_id
            review.user_id = current_user.id
            review.rating = form.rating.data
            review.title = form.title.data
            review.body = form.body.data
            review.is_approved = False
            db.session.add(review)
            db.session.commit()
            flash('Your review has been submitted and is pending approval.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
    
    return redirect(url_for('web.product_detail', slug=product.slug))

@web_bp.route('/pages/<slug>')
def content_page(slug):
    """Display content pages like About, Terms, etc."""
    page = ContentPage.query.filter_by(slug=slug).first_or_404()
    return render_template('web/content_page.html', page=page)

@web_bp.route('/account')
@login_required
def account():
    """Enhanced user account dashboard with comprehensive statistics"""
    from models import OrderStatus, PaymentStatus
    
    # Get user's recent orders
    recent_orders = current_user.orders.order_by(desc('created_at')).limit(10).all()
    
    # Get user's addresses
    addresses = current_user.addresses.all()
    
    # Calculate account statistics
    total_orders = current_user.orders.count()
    completed_orders = current_user.orders.filter_by(status=OrderStatus.DELIVERED).count()
    total_spent = db.session.query(func.sum(Order.grand_total_inr)).filter(
        Order.user_id == current_user.id,
        Order.payment_status == PaymentStatus.PAID
    ).scalar() or 0
    
    # Get favorite products (most reviewed)
    from models import Review
    favorite_products_query = db.session.query(Product).join(Review).filter(
        Review.user_id == current_user.id
    ).group_by(Product.id).order_by(func.count(Review.id).desc()).limit(5)
    favorite_products = favorite_products_query.all()
    
    # Get pending reviews (purchased but not reviewed)
    purchased_product_ids = db.session.query(OrderItem.product_id).join(Order).filter(
        Order.user_id == current_user.id,
        Order.status == OrderStatus.DELIVERED
    ).distinct().subquery()
    
    reviewed_product_ids = db.session.query(Review.product_id).filter(
        Review.user_id == current_user.id
    ).distinct().subquery()
    
    pending_reviews_query = db.session.query(Product).filter(
        Product.id.in_(purchased_product_ids),
        ~Product.id.in_(reviewed_product_ids)
    ).limit(5)
    pending_reviews = pending_reviews_query.all()
    
    return render_template('web/account.html',
                         recent_orders=recent_orders,
                         addresses=addresses,
                         total_orders=total_orders,
                         completed_orders=completed_orders,
                         total_spent=total_spent,
                         favorite_products=favorite_products,
                         pending_reviews=pending_reviews)

@web_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact form submission"""
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        
        # Validate required fields
        if not all([name, email, subject, message]):
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('web.content_page', slug='contact'))
        
        # Create contact form record
        contact_form = ContactForm()
        contact_form.name = name
        contact_form.email = email
        contact_form.phone = phone if phone else None
        contact_form.subject = subject
        contact_form.message = message
        contact_form.status = 'unread'
        
        try:
            db.session.add(contact_form)
            db.session.commit()
            flash('Thank you for your message! We will get back to you soon.', 'success')
            
            # Optional: Send notification email to admin
            # send_admin_notification_email(contact_form)
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error saving contact form: {str(e)}')
            flash('There was an error sending your message. Please try again.', 'error')
    
    return redirect(url_for('web.content_page', slug='contact'))

@web_bp.route('/newsletter/subscribe', methods=['POST'])
def newsletter_subscribe():
    """Newsletter subscription"""
    email = request.form.get('email', '').strip().lower()
    
    if not email:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Email is required'})
        flash('Please enter your email address.', 'error')
        return redirect(request.referrer or url_for('web.index'))
    
    # Check if already subscribed
    existing = NewsletterSubscriber.query.filter_by(email=email).first()
    if existing:
        if existing.is_active:
            message = 'You are already subscribed to our newsletter.'
        else:
            # Reactivate subscription
            existing.is_active = True
            db.session.commit()
            message = 'Welcome back! Your newsletter subscription has been reactivated.'
    else:
        # Create new subscription
        subscriber = NewsletterSubscriber()
        subscriber.email = email
        subscriber.is_active = True
        try:
            db.session.add(subscriber)
            db.session.commit()
            message = 'Thank you for subscribing to our newsletter!'
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error subscribing to newsletter: {str(e)}')
            message = 'There was an error subscribing. Please try again.'
    
    if request.is_json:
        return jsonify({'success': True, 'message': message})
    
    flash(message, 'success' if 'thank you' in message.lower() else 'info')
    return redirect(request.referrer or url_for('web.index'))

@web_bp.context_processor
def inject_global_vars():
    """Inject global template variables"""
    return {
        'format_currency': format_currency,
        'get_cart_count': get_cart_count,
        'store_name': current_app.config.get('STORE_NAME', 'ABC Publishing Kashmir')
    }

@web_bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@web_bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

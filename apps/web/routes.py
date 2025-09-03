from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_, func, desc, asc
from models import Product, Category, Author, Publisher, Price, Inventory, Review, ContentPage, ProductStatus, Language, Format, Banner, FeaturedCategory, BannerType, HomeSection, SectionType, MediaAsset, NewsletterSubscriber
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
                query = query.join(Product.categories).filter(Category.slug == category_slug)
            
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
        query = query.join(Product.categories).filter(Category.id == selected_category.id)
    elif form.category.data:
        query = query.join(Product.categories).filter(Category.id == form.category.data)
    
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
        query = query.join(Product.authors).filter(Author.id == form.author.data)
    
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
            .join(Product.categories)\
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
    
    # Perform search
    search_term = f"%{form.q.data}%"
    query = db.session.query(Product).join(Price).join(Inventory)\
        .outerjoin(Product.authors)\
        .filter(Product.status == ProductStatus.ACTIVE)\
        .filter(or_(
            Product.title.ilike(search_term),
            Product.isbn.ilike(search_term),
            Product.description.ilike(search_term),
            Author.name.ilike(search_term)
        ))
    
    # Apply additional filters
    if form.category.data:
        query = query.join(Product.categories).filter(Category.id == form.category.data)
    
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
            review = Review(
                product_id=product_id,
                user_id=current_user.id,
                rating=form.rating.data,
                title=form.title.data,
                body=form.body.data,
                is_approved=False  # Requires admin approval
            )
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
    """User account dashboard"""
    # Get user's recent orders
    recent_orders = current_user.orders.order_by(desc('created_at')).limit(5).all()
    
    # Get user's addresses
    addresses = current_user.addresses.all()
    
    return render_template('web/account.html',
                         recent_orders=recent_orders,
                         addresses=addresses)

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

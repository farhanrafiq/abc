from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_, func, desc, asc
from models import Product, Category, Author, Publisher, Price, Inventory, Review, ContentPage, ProductStatus, Language, Format
from forms import SearchForm, ReviewForm
from utils.helpers import format_currency, get_cart_count, paginate_query
from app import db
import logging

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def index():
    """Homepage with featured products and categories"""
    # Get featured categories
    featured_categories = Category.query.filter_by(parent_id=None).limit(6).all()
    
    # Get featured products (latest active products)
    featured_products = db.session.query(Product).join(Price).join(Inventory)\
        .filter(Product.status == ProductStatus.ACTIVE)\
        .filter(Inventory.stock_on_hand > 0)\
        .order_by(desc(Product.created_at))\
        .limit(8).all()
    
    # Get bestsellers (products with most reviews for now)
    bestsellers = db.session.query(Product).join(Price).join(Inventory)\
        .outerjoin(Review)\
        .filter(Product.status == ProductStatus.ACTIVE)\
        .filter(Inventory.stock_on_hand > 0)\
        .group_by(Product.id, Price.id, Inventory.product_id)\
        .order_by(desc(func.count(Review.id)))\
        .limit(6).all()
    
    # Get new arrivals
    new_arrivals = db.session.query(Product).join(Price).join(Inventory)\
        .filter(Product.status == ProductStatus.ACTIVE)\
        .filter(Inventory.stock_on_hand > 0)\
        .order_by(desc(Product.created_at))\
        .limit(6).all()
    
    return render_template('web/index_3d.html',
                         featured_categories=featured_categories,
                         featured_products=featured_products,
                         bestsellers=bestsellers,
                         new_arrivals=new_arrivals)

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
    
    return render_template('web/catalog_3d.html',
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

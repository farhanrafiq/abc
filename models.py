from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
import enum

class UserRole(enum.Enum):
    CUSTOMER = "customer"
    STAFF = "staff"
    ADMIN = "admin"

class Language(enum.Enum):
    ENGLISH = "EN"
    URDU = "UR"
    HINDI = "HI"
    ARABIC = "AR"
    OTHER = "OTHER"

class Format(enum.Enum):
    PAPERBACK = "Paperback"
    HARDCOVER = "Hardcover"
    OTHER = "Other"

class ProductStatus(enum.Enum):
    DRAFT = "Draft"
    ACTIVE = "Active"
    ARCHIVED = "Archived"

class OrderStatus(enum.Enum):
    PENDING = "Pending"
    PAID = "Paid"
    PACKED = "Packed"
    SHIPPED = "Shipped"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"
    REFUNDED = "Refunded"

class PaymentStatus(enum.Enum):
    UNPAID = "Unpaid"
    PAID = "Paid"
    FAILED = "Failed"
    REFUNDED = "Refunded"

class PaymentMethod(enum.Enum):
    RAZORPAY = "Razorpay"
    COD = "COD"
    UPI = "UPI"

class CouponType(enum.Enum):
    PERCENT = "PERCENT"
    AMOUNT = "AMOUNT"

class BannerType(enum.Enum):
    HERO = "hero"
    PROMOTIONAL = "promotional"
    CATEGORY = "category"

# User model
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(256))
    role = db.Column(db.Enum(UserRole), default=UserRole.CUSTOMER)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    addresses = db.relationship('Address', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='user', lazy='dynamic')
    reviews = db.relationship('Review', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_active(self):
        return self.active
        
    def __repr__(self):
        return f'<User {self.email}>'

# Address model
class Address(db.Model):
    __tablename__ = 'addresses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    line1 = db.Column(db.String(200), nullable=False)
    line2 = db.Column(db.String(200))
    city = db.Column(db.String(100), nullable=False)
    district = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    country = db.Column(db.String(50), default='IN')
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Author model
class Author(db.Model):
    __tablename__ = 'authors'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    bio = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', secondary='product_authors', back_populates='authors')

# Publisher model
class Publisher(db.Model):
    __tablename__ = 'publishers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='publisher', lazy='dynamic')

# Category model
class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Self-referential relationship
    children = db.relationship('Category', backref=db.backref('parent', remote_side=[id]))
    
    # Relationships
    products = db.relationship('Product', secondary='product_categories', back_populates='categories')

# Product model
class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    title_urdu = db.Column(db.String(200))
    title_arabic = db.Column(db.String(200))
    slug = db.Column(db.String(220), unique=True, nullable=False)
    isbn = db.Column(db.String(20))
    language = db.Column(db.String(10), default='EN')
    format = db.Column(db.String(20), default='Hardcover')
    description = db.Column(db.Text)
    pages = db.Column(db.Integer)
    publisher_id = db.Column(db.Integer, db.ForeignKey('publishers.id'))
    cover_image = db.Column(db.String(255))
    images = db.Column(db.JSON)  # Store array of image URLs
    published_at = db.Column(db.Date)
    weight_grams = db.Column(db.Integer)
    dimensions_l = db.Column(db.Float)  # Length in cm
    dimensions_w = db.Column(db.Float)  # Width in cm
    dimensions_h = db.Column(db.Float)  # Height in cm
    status = db.Column(db.Enum(ProductStatus), default=ProductStatus.DRAFT)
    is_bestseller = db.Column(db.Boolean, default=False)
    is_new = db.Column(db.Boolean, default=False)
    average_rating = db.Column(db.Float, default=0.0)
    review_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    authors = db.relationship('Author', secondary='product_authors', back_populates='products')
    categories = db.relationship('Category', secondary='product_categories', back_populates='products')
    price = db.relationship('Price', backref='product', uselist=False)
    inventory = db.relationship('Inventory', backref='product', uselist=False)
    reviews = db.relationship('Review', backref='product', lazy='dynamic')
    
    def __repr__(self):
        return f'<Product {self.title}>'

# Association tables
product_authors = db.Table('product_authors',
    db.Column('product_id', db.Integer, db.ForeignKey('products.id'), primary_key=True),
    db.Column('author_id', db.Integer, db.ForeignKey('authors.id'), primary_key=True)
)

product_categories = db.Table('product_categories',
    db.Column('product_id', db.Integer, db.ForeignKey('products.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id'), primary_key=True)
)

# Price model
class Price(db.Model):
    __tablename__ = 'prices'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    mrp_inr = db.Column(db.Integer, nullable=False)  # Price in paisa
    sale_inr = db.Column(db.Integer)  # Sale price in paisa
    currency = db.Column(db.String(3), default='INR')
    tax_rate_pct = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Inventory model
class Inventory(db.Model):
    __tablename__ = 'inventory'
    
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    stock_on_hand = db.Column(db.Integer, default=0)
    low_stock_threshold = db.Column(db.Integer, default=5)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Coupon model
class Coupon(db.Model):
    __tablename__ = 'coupons'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    type = db.Column(db.Enum(CouponType), nullable=False)
    value = db.Column(db.Float, nullable=False)
    min_subtotal = db.Column(db.Integer)  # In paisa
    starts_at = db.Column(db.DateTime)
    ends_at = db.Column(db.DateTime)
    max_redemptions = db.Column(db.Integer)
    per_user_limit = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Cart model
class Cart(db.Model):
    __tablename__ = 'carts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    session_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('CartItem', backref='cart', lazy='dynamic', cascade='all, delete-orphan')

class CartItem(db.Model):
    __tablename__ = 'cart_items'
    
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    product = db.relationship('Product', backref='cart_items')

# Order model
class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    billing_address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'))
    shipping_address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'))
    subtotal_inr = db.Column(db.Integer, nullable=False)  # In paisa
    discount_inr = db.Column(db.Integer, default=0)
    shipping_inr = db.Column(db.Integer, default=0)
    tax_inr = db.Column(db.Integer, default=0)
    grand_total_inr = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum(OrderStatus), default=OrderStatus.PENDING)
    payment_status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.UNPAID)
    payment_method = db.Column(db.Enum(PaymentMethod))
    razorpay_order_id = db.Column(db.String(100))
    razorpay_payment_id = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    billing_address = db.relationship('Address', foreign_keys=[billing_address_id])
    shipping_address = db.relationship('Address', foreign_keys=[shipping_address_id])
    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    shipments = db.relationship('Shipment', backref='order', lazy='dynamic')

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    title_snapshot = db.Column(db.String(200), nullable=False)
    sku_snapshot = db.Column(db.String(50), nullable=False)
    unit_price_inr = db.Column(db.Integer, nullable=False)  # In paisa
    quantity = db.Column(db.Integer, nullable=False)
    line_total_inr = db.Column(db.Integer, nullable=False)
    
    # Relationships
    product = db.relationship('Product', backref='order_items')

# Shipment model
class Shipment(db.Model):
    __tablename__ = 'shipments'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    carrier = db.Column(db.String(100))
    tracking_no = db.Column(db.String(100))
    status = db.Column(db.String(50))
    shipped_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Review model
class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    title = db.Column(db.String(200))
    body = db.Column(db.Text)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Content page model
class ContentPage(db.Model):
    __tablename__ = 'content_pages'
    
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Settings model
class Setting(db.Model):
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Banner model for hero sliders and promotional content
class Banner(db.Model):
    __tablename__ = 'banners'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subtitle = db.Column(db.String(300))
    description = db.Column(db.Text)
    image_url = db.Column(db.String(300))
    link_url = db.Column(db.String(300))
    link_text = db.Column(db.String(100))
    banner_type = db.Column(db.Enum(BannerType), default=BannerType.HERO)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Featured Category model for homepage management
class FeaturedCategory(db.Model):
    __tablename__ = 'featured_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    category = db.relationship('Category', backref='featured_entries')

import os

class Config:
    SECRET_KEY = os.environ.get('SESSION_SECRET')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@abcpublishingkashmir.com')
    
    # Payment
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', 'test_key')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', 'test_secret')
    
    # Upload
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Store settings
    STORE_NAME = 'ABC Publishing Kashmir'
    STORE_EMAIL = 'info@abcpublishingkashmir.com'
    STORE_PHONE = '+91-194-XXXXXX'
    STORE_ADDRESS = 'Srinagar, Jammu & Kashmir, India'
    
    # Shipping
    KASHMIR_SHIPPING_RATE = 5000  # 50 INR in paisa
    INDIA_SHIPPING_RATE = 10000   # 100 INR in paisa
    FREE_SHIPPING_THRESHOLD = 150000  # 1500 INR in paisa
    
    # Pagination
    PRODUCTS_PER_PAGE = 20
    ORDERS_PER_PAGE = 20
    REVIEWS_PER_PAGE = 10

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SelectField, IntegerField, FloatField, DateField, HiddenField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange, EqualTo, ValidationError
from flask_wtf.file import FileField, FileAllowed
from models import UserRole, ProductStatus, Language, Format

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

class RegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    
    def validate_email(self, field):
        """Validate email is unique during registration"""
        from models import User
        user = User.query.filter_by(email=field.data).first()
        if user:
            raise ValidationError('Email address already registered.')

class AddressForm(FlaskForm):
    name = StringField('Address Name', validators=[DataRequired(), Length(max=100)])
    line1 = StringField('Address Line 1', validators=[DataRequired(), Length(max=200)])
    line2 = StringField('Address Line 2', validators=[Optional(), Length(max=200)])
    city = StringField('City', validators=[DataRequired(), Length(max=100)])
    district = StringField('District', validators=[DataRequired(), Length(max=100)])
    state = StringField('State', validators=[DataRequired(), Length(max=100)])
    pincode = StringField('PIN Code', validators=[DataRequired(), Length(min=6, max=10)])
    is_default = BooleanField('Set as Default Address')
    
    def validate_pincode(self, field):
        """Validate Indian PIN code format"""
        pincode = field.data
        if pincode and not pincode.isdigit():
            raise ValidationError('PIN code must contain only numbers.')

class ProductForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    slug = StringField('Slug', validators=[DataRequired(), Length(max=220)])
    isbn = StringField('ISBN', validators=[Optional(), Length(max=20)])
    language = SelectField('Language', choices=[(lang.value, lang.value) for lang in Language])
    format = SelectField('Format', choices=[(fmt.value, fmt.value) for fmt in Format])
    description = TextAreaField('Description')
    publisher_id = SelectField('Publisher', coerce=int)
    cover_image = FileField('Cover Image', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'gif'])])
    published_at = DateField('Published Date', validators=[Optional()])
    weight_grams = IntegerField('Weight (grams)', validators=[Optional(), NumberRange(min=0)])
    dimensions_l = FloatField('Length (cm)', validators=[Optional(), NumberRange(min=0)])
    dimensions_w = FloatField('Width (cm)', validators=[Optional(), NumberRange(min=0)])
    dimensions_h = FloatField('Height (cm)', validators=[Optional(), NumberRange(min=0)])
    status = SelectField('Status', choices=[(status.value, status.value) for status in ProductStatus])
    
    # Price fields
    mrp_inr = FloatField('MRP (INR)', validators=[DataRequired(), NumberRange(min=0)])
    sale_inr = FloatField('Sale Price (INR)', validators=[Optional(), NumberRange(min=0)])
    tax_rate_pct = FloatField('Tax Rate (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    
    # Inventory fields
    sku = StringField('SKU', validators=[DataRequired(), Length(max=50)])
    stock_on_hand = IntegerField('Stock Quantity', validators=[DataRequired(), NumberRange(min=0)])
    low_stock_threshold = IntegerField('Low Stock Threshold', validators=[DataRequired(), NumberRange(min=0)])
    
    def validate_isbn(self, field):
        """Validate ISBN format if provided"""
        isbn = field.data
        if isbn:
            # Remove hyphens and spaces
            isbn_clean = isbn.replace('-', '').replace(' ', '')
            # Check if it's ISBN-10 or ISBN-13
            if len(isbn_clean) == 10:
                if not (isbn_clean[:-1].isdigit() and (isbn_clean[-1].isdigit() or isbn_clean[-1].upper() == 'X')):
                    raise ValidationError('Invalid ISBN-10 format.')
            elif len(isbn_clean) == 13:
                if not isbn_clean.isdigit():
                    raise ValidationError('Invalid ISBN-13 format.')
            else:
                raise ValidationError('ISBN must be 10 or 13 characters long.')
    
    def validate_sale_inr(self, field):
        """Validate sale price is less than MRP"""
        if field.data and self.mrp_inr.data:
            if field.data >= self.mrp_inr.data:
                raise ValidationError('Sale price must be less than MRP.')

class AuthorForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    slug = StringField('Slug', validators=[DataRequired(), Length(max=120)])
    bio = TextAreaField('Biography')
    website = StringField('Website', validators=[Optional(), Length(max=200)])
    image = FileField('Author Image', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'gif'])])

class PublisherForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    slug = StringField('Slug', validators=[DataRequired(), Length(max=120)])
    description = TextAreaField('Description')
    website = StringField('Website', validators=[Optional(), Length(max=200)])
    logo = FileField('Publisher Logo', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'gif'])])

class CategoryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    slug = StringField('Slug', validators=[DataRequired(), Length(max=120)])
    description = TextAreaField('Description', validators=[Optional()])
    parent_id = SelectField('Parent Category', coerce=int, validators=[Optional()])
    sort_order = IntegerField('Sort Order', validators=[Optional(), NumberRange(min=0)])
    is_active = BooleanField('Active', default=True)
    image = FileField('Category Image', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'gif'])])

class CouponForm(FlaskForm):
    code = StringField('Coupon Code', validators=[DataRequired(), Length(min=3, max=50)])
    type = SelectField('Type', choices=[('PERCENT', 'Percentage'), ('AMOUNT', 'Fixed Amount')])
    value = FloatField('Value', validators=[DataRequired(), NumberRange(min=0.01)])
    min_subtotal = FloatField('Minimum Subtotal (INR)', validators=[Optional(), NumberRange(min=0)])
    max_redemptions = IntegerField('Max Redemptions', validators=[Optional(), NumberRange(min=1)])
    per_user_limit = IntegerField('Per User Limit', validators=[DataRequired(), NumberRange(min=1)])
    
    def validate_code(self, field):
        """Validate coupon code format and uniqueness"""
        code = field.data.upper() if field.data else ''
        # Check for valid characters (letters, numbers, underscores, hyphens)
        import re
        if not re.match(r'^[A-Z0-9_-]+$', code):
            raise ValidationError('Coupon code can only contain letters, numbers, underscores, and hyphens.')
    
    def validate_value(self, field):
        """Validate coupon value based on type"""
        if field.data and self.type.data == 'PERCENT':
            if field.data > 100:
                raise ValidationError('Percentage discount cannot exceed 100%.')

class SearchForm(FlaskForm):
    q = StringField('Search', validators=[Optional()])
    category = SelectField('Category', coerce=int, validators=[Optional()])
    author = SelectField('Author', coerce=int, validators=[Optional()])
    publisher = SelectField('Publisher', coerce=int, validators=[Optional()])
    language = SelectField('Language', choices=[('', 'All Languages')] + [(lang.value, lang.value) for lang in Language])
    format = SelectField('Format', choices=[('', 'All Formats')] + [(fmt.value, fmt.value) for fmt in Format])
    min_price = FloatField('Min Price', validators=[Optional(), NumberRange(min=0)])
    max_price = FloatField('Max Price', validators=[Optional(), NumberRange(min=0)])
    in_stock = BooleanField('In Stock Only')
    sort = SelectField('Sort By', choices=[
        ('relevance', 'Relevance'),
        ('newest', 'Newest First'),
        ('price_asc', 'Price: Low to High'),
        ('price_desc', 'Price: High to Low'),
        ('title_asc', 'Title: A to Z'),
        ('title_desc', 'Title: Z to A')
    ])
    
    def validate_max_price(self, field):
        """Validate max price is greater than min price"""
        if field.data and self.min_price.data:
            if field.data <= self.min_price.data:
                raise ValidationError('Maximum price must be greater than minimum price.')

class CheckoutForm(FlaskForm):
    # Guest checkout fields
    guest_email = StringField('Email', validators=[Optional(), Email()])
    guest_phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    
    # Address selection
    billing_address_id = SelectField('Billing Address', coerce=int, validators=[Optional()])
    shipping_address_id = SelectField('Shipping Address', coerce=int, validators=[Optional()])
    
    # Payment
    payment_method = SelectField('Payment Method', choices=[
        ('razorpay', 'Credit/Debit Card/UPI'),
        ('cod', 'Cash on Delivery')
    ])
    
    # Coupon
    coupon_code = StringField('Coupon Code', validators=[Optional(), Length(max=50)])
    
    # Notes
    notes = TextAreaField('Order Notes', validators=[Optional()])

class PasswordResetRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])

class PasswordResetForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=8, message="Password must be at least 8 characters long")])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message="Passwords must match")])
    token = HiddenField()
    
    def validate_password(self, field):
        """Custom validation for password strength"""
        password = field.data
        if password:
            # Check for at least one uppercase letter
            if not any(c.isupper() for c in password):
                raise ValidationError('Password must contain at least one uppercase letter.')
            # Check for at least one lowercase letter  
            if not any(c.islower() for c in password):
                raise ValidationError('Password must contain at least one lowercase letter.')
            # Check for at least one digit
            if not any(c.isdigit() for c in password):
                raise ValidationError('Password must contain at least one number.')

class UserForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    role = SelectField('Role', choices=[(role.value, role.value.title()) for role in UserRole])
    is_active = BooleanField('Active')
    
    def __init__(self, user=None, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.user = user
    
    def validate_email(self, field):
        """Validate email is unique"""
        from models import User
        user = User.query.filter_by(email=field.data).first()
        if user and (not self.user or user.id != self.user.id):
            raise ValidationError('Email address already in use.')

class ProfileForm(FlaskForm):
    """Enhanced profile form with proper validation"""
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    current_password = PasswordField('Current Password', validators=[Optional()])
    new_password = PasswordField('New Password', validators=[Optional(), Length(min=8)])
    confirm_password = PasswordField('Confirm New Password', validators=[Optional(), EqualTo('new_password')])
    
    def validate_new_password(self, field):
        """Validate new password strength if provided"""
        if field.data:
            password = field.data
            # Check for at least one uppercase letter
            if not any(c.isupper() for c in password):
                raise ValidationError('Password must contain at least one uppercase letter.')
            # Check for at least one lowercase letter  
            if not any(c.islower() for c in password):
                raise ValidationError('Password must contain at least one lowercase letter.')
            # Check for at least one digit
            if not any(c.isdigit() for c in password):
                raise ValidationError('Password must contain at least one number.')
    
    def validate_current_password(self, field):
        """Validate current password if changing password"""
        if field.data and not self.new_password.data:
            raise ValidationError('Please provide a new password.')
        if self.new_password.data and not field.data:
            raise ValidationError('Current password required to change password.')

class ContactForm(FlaskForm):
    """Contact form with enhanced validation"""
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    subject = StringField('Subject', validators=[DataRequired(), Length(min=5, max=200)])
    message = TextAreaField('Message', validators=[DataRequired(), Length(min=10, max=2000)])

class ReviewForm(FlaskForm):
    """Product review form"""
    rating = SelectField('Rating', choices=[(i, f'{i} Star{"s" if i != 1 else ""}') for i in range(1, 6)], coerce=int, validators=[DataRequired()])
    title = StringField('Review Title', validators=[DataRequired(), Length(min=5, max=200)])
    body = TextAreaField('Review', validators=[DataRequired(), Length(min=10, max=2000)])
    
    def validate_rating(self, field):
        """Validate rating is between 1-5"""
        if field.data not in range(1, 6):
            raise ValidationError('Rating must be between 1 and 5 stars.')
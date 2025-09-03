from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, IntegerField, FloatField, BooleanField, PasswordField, DateField, HiddenField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, EqualTo
from models import Language, Format, ProductStatus, UserRole

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

class RegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])

class AddressForm(FlaskForm):
    name = StringField('Address Name', validators=[DataRequired(), Length(max=100)])
    line1 = StringField('Address Line 1', validators=[DataRequired(), Length(max=200)])
    line2 = StringField('Address Line 2', validators=[Optional(), Length(max=200)])
    city = StringField('City', validators=[DataRequired(), Length(max=100)])
    district = StringField('District', validators=[DataRequired(), Length(max=100)])
    state = StringField('State', validators=[DataRequired(), Length(max=100)])
    pincode = StringField('PIN Code', validators=[DataRequired(), Length(min=6, max=10)])
    is_default = BooleanField('Set as Default Address')

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
    stock_on_hand = IntegerField('Stock on Hand', validators=[DataRequired(), NumberRange(min=0)])
    low_stock_threshold = IntegerField('Low Stock Threshold', validators=[DataRequired(), NumberRange(min=0)])

class AuthorForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    slug = StringField('Slug', validators=[DataRequired(), Length(max=120)])
    bio = TextAreaField('Biography')

class PublisherForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    slug = StringField('Slug', validators=[DataRequired(), Length(max=120)])
    description = TextAreaField('Description')

class CategoryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    slug = StringField('Slug', validators=[DataRequired(), Length(max=120)])
    parent_id = SelectField('Parent Category', coerce=int, validators=[Optional()])

class CouponForm(FlaskForm):
    code = StringField('Coupon Code', validators=[DataRequired(), Length(max=50)])
    type = SelectField('Type', choices=[('PERCENT', 'Percentage'), ('AMOUNT', 'Fixed Amount')])
    value = FloatField('Value', validators=[DataRequired(), NumberRange(min=0)])
    min_subtotal = FloatField('Minimum Subtotal (INR)', validators=[Optional(), NumberRange(min=0)])
    max_redemptions = IntegerField('Max Redemptions', validators=[Optional(), NumberRange(min=1)])
    per_user_limit = IntegerField('Per User Limit', validators=[DataRequired(), NumberRange(min=1)])

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

class ReviewForm(FlaskForm):
    rating = SelectField('Rating', choices=[(i, f'{i} Star{"s" if i != 1 else ""}') for i in range(1, 6)], coerce=int)
    title = StringField('Review Title', validators=[DataRequired(), Length(max=200)])
    body = TextAreaField('Review', validators=[DataRequired()])

class PasswordResetRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])

class PasswordResetForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    token = HiddenField()

class UserForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    role = SelectField('Role', choices=[(role.value, role.value.title()) for role in UserRole])
    is_active = BooleanField('Active')

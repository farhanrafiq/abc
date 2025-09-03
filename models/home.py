from enum import Enum
from datetime import datetime
from app import db
from sqlalchemy import JSON


class SectionType(Enum):
    HERO_SLIDER = "hero_slider"
    TRUST_BADGES = "trust_badges"
    CATEGORY_TILES = "category_tiles"
    FEATURED_COLLECTION = "featured_collection"
    NEW_ARRIVALS = "new_arrivals"
    BESTSELLERS = "bestsellers"
    STAFF_PICKS = "staff_picks"
    DEALS_OF_DAY = "deals_of_day"
    AUTHOR_SPOTLIGHT = "author_spotlight"
    PUBLISHER_SPOTLIGHT = "publisher_spotlight"
    LANGUAGE_SHELF = "language_shelf"
    KIDS_CORNER = "kids_corner"
    QUICK_ORDER_ISBN = "quick_order_isbn"
    TRENDING_SEARCHES = "trending_searches"
    BLOG_SNIPPETS = "blog_snippets"
    TESTIMONIALS = "testimonials"
    NEWSLETTER_BAR = "newsletter_bar"
    INFO_STRIP = "info_strip"


class MediaKind(Enum):
    IMAGE = "image"
    ICON = "icon"


class HomeSection(db.Model):
    __tablename__ = 'home_sections'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum(SectionType), nullable=False)
    title = db.Column(db.String(200))
    subtitle = db.Column(db.String(500))
    config = db.Column(JSON, default=dict)
    position = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, default=True)
    start_at = db.Column(db.DateTime, nullable=True)
    end_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<HomeSection {self.type.value}: {self.title}>'
    
    @property
    def is_scheduled_active(self):
        """Check if section is within its scheduled time window"""
        if not self.is_active:
            return False
        
        now = datetime.utcnow()
        
        if self.start_at and now < self.start_at:
            return False
        
        if self.end_at and now > self.end_at:
            return False
        
        return True
    
    def get_config_value(self, key, default=None):
        """Safely get a configuration value"""
        return self.config.get(key, default) if self.config else default
    
    def set_config_value(self, key, value):
        """Set a configuration value"""
        if self.config is None:
            self.config = {}
        self.config[key] = value
    
    @classmethod
    def get_active_sections(cls):
        """Get all active sections in order"""
        return cls.query.filter_by(is_active=True).order_by(cls.position).all()
    
    @classmethod
    def get_scheduled_active_sections(cls):
        """Get all sections that are active and within schedule"""
        sections = cls.get_active_sections()
        return [s for s in sections if s.is_scheduled_active]


class MediaAsset(db.Model):
    __tablename__ = 'media_assets'
    
    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.Enum(MediaKind), nullable=False)
    path = db.Column(db.String(500), nullable=False)
    alt_text = db.Column(db.String(255), default='')
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MediaAsset {self.kind.value}: {self.path}>'
    
    @property
    def url(self):
        """Get the URL for this asset"""
        if self.path.startswith('http'):
            return self.path
        return f'/static/{self.path}'
    
    @property
    def is_image(self):
        return self.kind == MediaKind.IMAGE
    
    @property
    def is_icon(self):
        return self.kind == MediaKind.ICON


class NewsletterSubscriber(db.Model):
    __tablename__ = 'newsletter_subscribers'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<NewsletterSubscriber {self.email}>'


# Section configuration schemas for validation
SECTION_SCHEMAS = {
    SectionType.HERO_SLIDER: {
        'show_arrows': bool,
        'show_dots': bool,
        'autoplay_enabled': bool,
        'autoplay_interval_ms': int,
        'transition': str,  # 'fade' or 'slide'
        'transition_ms': int
    },
    SectionType.TRUST_BADGES: {
        'items': list  # [{icon_path, icon_name, label, sublabel}]
    },
    SectionType.CATEGORY_TILES: {
        'tiles': list,  # [{title, slug, image_asset, accent_color, href}]
        'columns_mobile': int,
        'columns_desktop': int
    },
    SectionType.FEATURED_COLLECTION: {
        'data_source': str,  # 'manual' or 'query'
        'manual_product_ids': list,
        'query': dict,  # {category_slug, limit, sort}
        'layout': str  # 'carousel' or 'grid'
    },
    SectionType.NEW_ARRIVALS: {
        'limit': int,
        'layout': str,
        'show_price_badges': bool
    },
    SectionType.BESTSELLERS: {
        'limit': int,
        'layout': str,
        'show_price_badges': bool
    },
    SectionType.STAFF_PICKS: {
        'items': list  # [{product_id, editor_note}]
    },
    SectionType.DEALS_OF_DAY: {
        'items': list  # [{product_id, deal_price, ends_at}]
    },
    SectionType.AUTHOR_SPOTLIGHT: {
        'author_id': int,
        'portrait_asset': int,
        'blurb': str
    },
    SectionType.PUBLISHER_SPOTLIGHT: {
        'publisher_id': int,
        'logo_asset': int,
        'blurb': str
    },
    SectionType.LANGUAGE_SHELF: {
        'languages': list,
        'limit': int,
        'layout': str
    },
    SectionType.KIDS_CORNER: {
        'limit': int,
        'layout': str,
        'banner_asset': int
    },
    SectionType.QUICK_ORDER_ISBN: {
        'enable_scanner': bool,
        'note_text': str
    },
    SectionType.TRENDING_SEARCHES: {
        'terms': list,
        'view_all_link': str
    },
    SectionType.BLOG_SNIPPETS: {
        'posts': list  # [{title, excerpt, href, image_asset, read_time}]
    },
    SectionType.TESTIMONIALS: {
        'items': list  # [{name, text, rating, location}]
    },
    SectionType.NEWSLETTER_BAR: {
        'title': str,
        'subtitle': str,
        'placeholder_text': str,
        'submit_label': str
    },
    SectionType.INFO_STRIP: {
        'items': list  # [{text, icon}]
    }
}


def validate_section_config(section_type, config):
    """Validate section configuration against schema"""
    if section_type not in SECTION_SCHEMAS:
        return False, f"Unknown section type: {section_type}"
    
    schema = SECTION_SCHEMAS[section_type]
    errors = []
    
    for key, expected_type in schema.items():
        if key in config:
            value = config[key]
            if not isinstance(value, expected_type):
                errors.append(f"{key} must be of type {expected_type.__name__}")
    
    return len(errors) == 0, errors
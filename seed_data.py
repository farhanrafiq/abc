#!/usr/bin/env python3
"""
Sample data seeder for ABC Publishing Kashmir Homepage Builder
Creates demo homepage sections to showcase the system
"""

from app import app, db
from models import HomeSection, SectionType, Banner, BannerType, NewsletterSubscriber
from datetime import datetime, timedelta
import json

def create_sample_sections():
    """Create sample homepage sections"""
    
    # Clear existing sections
    HomeSection.query.delete()
    
    # 1. Hero Slider Section
    hero_section = HomeSection(
        type=SectionType.HERO_SLIDER,
        title="Welcome Banner",
        subtitle="Featured books and promotions",
        position=1,
        is_active=True,
        config={
            'show_arrows': True,
            'show_dots': True,
            'autoplay_enabled': True,
            'autoplay_interval_ms': 5000,
            'transition': 'fade',
            'transition_ms': 600
        }
    )
    
    # 2. Trust Badges Section
    trust_section = HomeSection(
        type=SectionType.TRUST_BADGES,
        title="Why Choose ABC Publishing Kashmir",
        subtitle="Your trusted partner for authentic Islamic literature",
        position=2,
        is_active=True,
        config={
            'items': [
                {
                    'icon_name': 'fa-shield-alt',
                    'label': 'Authentic Books',
                    'sublabel': 'Carefully curated Islamic literature'
                },
                {
                    'icon_name': 'fa-truck',
                    'label': 'Fast Delivery',
                    'sublabel': 'Free shipping across Kashmir & India'
                },
                {
                    'icon_name': 'fa-phone',
                    'label': '24/7 Support',
                    'sublabel': 'Always here to help you'
                },
                {
                    'icon_name': 'fa-undo',
                    'label': 'Easy Returns',
                    'sublabel': '30-day hassle-free returns'
                }
            ]
        }
    )
    
    # 3. Category Tiles Section
    category_section = HomeSection(
        type=SectionType.CATEGORY_TILES,
        title="Explore Our Categories",
        subtitle="Discover books across different areas of Islamic knowledge",
        position=3,
        is_active=True,
        config={
            'tiles': [
                {
                    'title': 'Tafaseer-ul-Quran',
                    'slug': 'tafaseer-ul-quran',
                    'image_url': 'https://images.unsplash.com/photo-1609599006353-e629aaabfeae?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=80',
                    'accent_color': '#E86A17'
                },
                {
                    'title': 'Hadith Collections',
                    'slug': 'hadith-collections',
                    'image_url': 'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=80',
                    'accent_color': '#5A4034'
                },
                {
                    'title': 'Seerat & Biography',
                    'slug': 'seerat-biography',
                    'image_url': 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=80',
                    'accent_color': '#8A6A5A'
                },
                {
                    'title': 'Fiqh & Islamic Law',
                    'slug': 'fiqh-islamic-law',
                    'image_url': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=80',
                    'accent_color': '#B25E0B'
                }
            ],
            'columns_mobile': 2,
            'columns_desktop': 4
        }
    )
    
    # 4. Featured Collection Section
    featured_section = HomeSection(
        type=SectionType.FEATURED_COLLECTION,
        title="Featured Books",
        subtitle="Hand-picked selections from our curated collection",
        position=4,
        is_active=True,
        config={
            'data_source': 'query',
            'query': {
                'category_slug': '',
                'sort': 'newest'
            },
            'limit': 8,
            'layout': 'grid',
            'show_price_badges': True
        }
    )
    
    # 5. New Arrivals Section
    new_arrivals_section = HomeSection(
        type=SectionType.NEW_ARRIVALS,
        title="New Arrivals",
        subtitle="Latest additions to our Islamic literature collection",
        position=5,
        is_active=True,
        config={
            'data_source': 'query',
            'query': {
                'sort': 'newest'
            },
            'limit': 6,
            'layout': 'carousel',
            'show_price_badges': True
        }
    )
    
    # 6. Quick Order ISBN Section
    isbn_section = HomeSection(
        type=SectionType.QUICK_ORDER_ISBN,
        title="Quick Order by ISBN",
        subtitle="Have an ISBN? Find your book instantly",
        position=6,
        is_active=True,
        config={
            'enable_scanner': True,
            'note_text': 'Enter the ISBN number (with or without dashes) to quickly find and order any book from our catalog.'
        }
    )
    
    # 7. Newsletter Subscription Section
    newsletter_section = HomeSection(
        type=SectionType.NEWSLETTER_BAR,
        title="Stay Connected",
        subtitle="Subscribe to our newsletter for book recommendations and exclusive offers",
        position=7,
        is_active=True,
        config={
            'title': 'Join Our Reading Community',
            'subtitle': 'Get weekly book recommendations, author insights, and exclusive deals delivered to your inbox',
            'placeholder_text': 'Enter your email address',
            'submit_label': 'Subscribe Now'
        }
    )
    
    # Add all sections to database
    sections = [
        hero_section,
        trust_section, 
        category_section,
        featured_section,
        new_arrivals_section,
        isbn_section,
        newsletter_section
    ]
    
    for section in sections:
        db.session.add(section)
    
    print(f"Created {len(sections)} homepage sections")

def create_sample_banners():
    """Create sample hero banners"""
    
    # Clear existing hero banners
    Banner.query.filter_by(banner_type=BannerType.HERO).delete()
    
    banners = [
        Banner(
            title="Discover Authentic Islamic Literature",
            subtitle="From classical texts to contemporary works",
            description="Explore our carefully curated collection of books that inspire, educate, and enlighten readers on their spiritual journey.",
            image_url="https://images.unsplash.com/photo-1481627834876-b7833e8f5570?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80",
            link_url="/catalog",
            link_text="Browse Collection",
            banner_type=BannerType.HERO,
            is_active=True,
            sort_order=1
        ),
        Banner(
            title="Special Ramadan Collection",
            subtitle="Spiritual books for the holy month",
            description="Enhance your Ramadan experience with our special collection of books on spirituality, prayer, and self-reflection.",
            image_url="https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80",
            link_url="/catalog?category=spirituality",
            link_text="View Collection",
            banner_type=BannerType.HERO,
            is_active=True,
            sort_order=2
        ),
        Banner(
            title="Free Shipping Across Kashmir",
            subtitle="Get your favorite books delivered",
            description="Enjoy free shipping on all orders above ₹999. Fast and reliable delivery to every corner of Kashmir and India.",
            image_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80",
            link_url="/shipping-info",
            link_text="Learn More",
            banner_type=BannerType.HERO,
            is_active=True,
            sort_order=3
        )
    ]
    
    for banner in banners:
        db.session.add(banner)
    
    print(f"Created {len(banners)} hero banners")

def create_sample_newsletter_subscribers():
    """Create some sample newsletter subscribers"""
    
    subscribers = [
        NewsletterSubscriber(email="reader1@example.com", is_active=True),
        NewsletterSubscriber(email="bookworm@example.com", is_active=True),
        NewsletterSubscriber(email="student@university.edu", is_active=True),
    ]
    
    for subscriber in subscribers:
        try:
            db.session.add(subscriber)
        except:
            pass  # Skip if already exists
    
    print(f"Created sample newsletter subscribers")

def main():
    """Main seeder function"""
    with app.app_context():
        print("🌱 Seeding ABC Publishing Kashmir Homepage Builder data...")
        
        try:
            create_sample_sections()
            create_sample_banners()
            create_sample_newsletter_subscribers()
            
            db.session.commit()
            print("✅ Sample data created successfully!")
            print("\n📝 Homepage Builder Features:")
            print("   • 7 Dynamic sections configured")
            print("   • 3 Hero banner slides")
            print("   • Trust badges with icons")
            print("   • Category tiles with images")
            print("   • Product collections (featured & new arrivals)")
            print("   • Quick ISBN order functionality")
            print("   • Newsletter subscription")
            print("\n🎨 Admin Panel:")
            print("   • Visit /admin/home to manage sections")
            print("   • Drag & drop to reorder sections")
            print("   • Toggle section visibility")
            print("   • Live preview functionality")
            print("\n🏠 Homepage:")
            print("   • Visit / to see the dynamic homepage")
            print("   • All sections render with sample data")
            print("   • Responsive design with iOS-style animations")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating sample data: {str(e)}")
            raise

if __name__ == "__main__":
    main()
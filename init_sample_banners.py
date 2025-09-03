#!/usr/bin/env python3
"""
Initialize sample banner data for the hero carousel
"""

from app import app, db
from models import Banner, FeaturedCategory, Category, BannerType
from datetime import datetime

def init_sample_banners():
    """Create sample banners for the hero carousel"""
    
    with app.app_context():
        print("Creating sample banners...")
        
        # Clear existing banners
        Banner.query.delete()
        
        # Sample banner data
        banners_data = [
            {
                'title': 'Discover Authentic Islamic Literature',
                'subtitle': 'From Classical Tafaseer to Contemporary Islamic Thought',
                'description': 'Explore our curated collection of books that inspire, educate, and enlighten the soul',
                'image_url': 'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80',
                'link_url': '/catalog',
                'link_text': 'Shop Now',
                'banner_type': BannerType.HERO,
                'sort_order': 1,
                'is_active': True
            },
            {
                'title': 'Quran & Tafseer Collection',
                'subtitle': 'The Most Comprehensive Quranic Commentary Library',
                'description': 'Including works by Ibn Kathir, Tabari, Qurtubi and other renowned scholars',
                'image_url': 'https://images.unsplash.com/photo-1542816417-0983c9c9ad53?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80',
                'link_url': '/catalog/tafaseer-ul-quran',
                'link_text': 'Explore Tafseer',
                'banner_type': BannerType.HERO,
                'sort_order': 2,
                'is_active': True
            },
            {
                'title': 'Hadith & Sunnah Library',
                'subtitle': 'Authentic Collections from Trusted Sources',
                'description': 'Sahih Bukhari, Sahih Muslim, Sunan Abu Dawud and complete hadith collections',
                'image_url': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80',
                'link_url': '/catalog/hadith-collections',
                'link_text': 'View Hadith Books',
                'banner_type': BannerType.HERO,
                'sort_order': 3,
                'is_active': True
            },
            {
                'title': 'Spiritual Development & Tasawwuf',
                'subtitle': 'Journey of the Soul Towards Allah',
                'description': 'Works by Al-Ghazali, Ibn Arabi, Rumi and contemporary spiritual masters',
                'image_url': 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80',
                'link_url': '/catalog/tasawwuf-spirituality',
                'link_text': 'Discover Spirituality',
                'banner_type': BannerType.HERO,
                'sort_order': 4,
                'is_active': True
            }
        ]
        
        # Create banners
        for banner_data in banners_data:
            banner = Banner(**banner_data)
            db.session.add(banner)
        
        # Set up featured categories if none exist
        existing_featured = FeaturedCategory.query.filter_by(is_active=True).count()
        
        if existing_featured == 0:
            print("Setting up featured categories...")
            
            # Get some categories to feature
            categories_to_feature = [
                'tafaseer-ul-quran',
                'hadith-collections', 
                'seerat-biography',
                'fiqh-islamic-law',
                'tasawwuf-spirituality',
                'islamic-history'
            ]
            
            for i, slug in enumerate(categories_to_feature):
                category = Category.query.filter_by(slug=slug).first()
                if category:
                    featured = FeaturedCategory(
                        category_id=category.id,
                        sort_order=i + 1,
                        is_active=True
                    )
                    db.session.add(featured)
        
        # Commit all changes
        db.session.commit()
        print(f"Successfully created {len(banners_data)} hero banners!")
        print("Featured categories configured!")
        print("\nAdmin panel links:")
        print("- Banners: /admin/banners")
        print("- Featured Categories: /admin/featured-categories")

if __name__ == "__main__":
    init_sample_banners()
#!/usr/bin/env python3
"""
Create categories to match the navigation menu structure
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Category

def create_categories():
    """Create all categories needed for the navigation menu"""
    
    with app.app_context():
        # Create main categories first
        main_categories = [
            # English Main Categories
            {'name': 'All Books', 'slug': 'all-books', 'description': 'Complete collection of Islamic books'},
            {'name': 'Mushafs', 'slug': 'mushafs', 'description': 'Holy Quran in various formats'},
            {'name': 'Academics', 'slug': 'academics', 'description': 'Academic and scholarly Islamic texts'},
            {'name': 'Quran Studies', 'slug': 'quran-studies', 'description': 'Books on Quranic sciences and studies'},
            {'name': 'Hadith', 'slug': 'hadith', 'description': 'Collections of Prophetic traditions'},
        ]
        
        # Create main categories
        main_cat_objects = {}
        for cat_data in main_categories:
            existing = Category.query.filter_by(slug=cat_data['slug']).first()
            if not existing:
                category = Category(
                    name=cat_data['name'],
                    slug=cat_data['slug'],
                    description=cat_data['description'],
                    is_active=True
                )
                db.session.add(category)
                db.session.flush()  # Get the ID
                main_cat_objects[cat_data['slug']] = category
                print(f"✅ Created main category: {cat_data['name']}")
            else:
                main_cat_objects[cat_data['slug']] = existing
                print(f"📚 Main category exists: {cat_data['name']}")
        
        # Create subcategories
        subcategories = [
            # English Quran Studies subcategories
            {'name': 'Quranic Commentary', 'slug': 'tafseer', 'parent_slug': 'quran-studies'},
            {'name': 'Quran & Science', 'slug': 'quran-science', 'parent_slug': 'quran-studies'},
            {'name': 'Memorization Guides', 'slug': 'memorization', 'parent_slug': 'quran-studies'},
            {'name': 'Recitation (Qiraat)', 'slug': 'recitation', 'parent_slug': 'quran-studies'},
            {'name': 'Thematic Studies', 'slug': 'themes', 'parent_slug': 'quran-studies'},
            {'name': 'Quranic Sciences', 'slug': 'quranic-sciences', 'parent_slug': 'quran-studies'},
            {'name': 'Nasikh & Mansukh', 'slug': 'nasikh-mansukh', 'parent_slug': 'quran-studies'},
            {'name': 'Asbab al-Nuzul', 'slug': 'asbab-nuzul', 'parent_slug': 'quran-studies'},
            
            # English Hadith subcategories  
            {'name': 'Sahih Bukhari', 'slug': 'sahih-bukhari', 'parent_slug': 'hadith'},
            {'name': 'Sahih Muslim', 'slug': 'sahih-muslim', 'parent_slug': 'hadith'},
            {'name': 'Sunan Abu Dawood', 'slug': 'sunan-abu-dawood', 'parent_slug': 'hadith'},
            {'name': 'Jami at-Tirmidhi', 'slug': 'jami-tirmidhi', 'parent_slug': 'hadith'},
            {'name': 'Sunan an-Nasai', 'slug': 'sunan-nasai', 'parent_slug': 'hadith'},
            {'name': 'Sunan Ibn Majah', 'slug': 'sunan-ibn-majah', 'parent_slug': 'hadith'},
            {'name': 'Muwatta Malik', 'slug': 'muwatta-malik', 'parent_slug': 'hadith'},
            {'name': 'Musnad Ahmad', 'slug': 'musnad-ahmad', 'parent_slug': 'hadith'},
            {'name': 'Hadith Qudsi', 'slug': 'hadith-qudsi', 'parent_slug': 'hadith'},
            {'name': 'Hadith Methodology', 'slug': 'hadith-methodology', 'parent_slug': 'hadith'},
            
            # Mushaf subcategories
            {'name': 'English Translation', 'slug': 'quran-translation', 'parent_slug': 'mushafs'},
            {'name': 'Transliteration', 'slug': 'quran-transliteration', 'parent_slug': 'mushafs'},
            {'name': 'Pocket Size Quran', 'slug': 'pocket-quran', 'parent_slug': 'mushafs'},
            {'name': 'Large Print Quran', 'slug': 'large-print-quran', 'parent_slug': 'mushafs'},
            {'name': 'Color Coded Quran', 'slug': 'color-coded-quran', 'parent_slug': 'mushafs'},
            {'name': 'Quran with Commentary', 'slug': 'quran-with-tafseer', 'parent_slug': 'mushafs'},
            {'name': 'Holy Quran Arabic', 'slug': 'mushaf-arabic', 'parent_slug': 'mushafs'},
            {'name': 'Mushaf Madinah', 'slug': 'mushaf-madinah', 'parent_slug': 'mushafs'},
            {'name': 'Uthmani Script', 'slug': 'mushaf-uthmani', 'parent_slug': 'mushafs'},
            {'name': 'Tajweed Quran', 'slug': 'mushaf-tajweed', 'parent_slug': 'mushafs'},
            {'name': 'Warsh Recitation', 'slug': 'mushaf-warsh', 'parent_slug': 'mushafs'},
            {'name': 'Hafs Recitation', 'slug': 'mushaf-hafs', 'parent_slug': 'mushafs'},
            
            # Academic subcategories
            {'name': 'Islamic Studies', 'slug': 'islamic-studies', 'parent_slug': 'academics'},
            {'name': 'Arabic Language', 'slug': 'arabic-language', 'parent_slug': 'academics'},
            {'name': 'Islamic Law', 'slug': 'islamic-law', 'parent_slug': 'academics'},
            {'name': 'Islamic Theology', 'slug': 'theology', 'parent_slug': 'academics'},
            {'name': 'Research Methodology', 'slug': 'research-methodology', 'parent_slug': 'academics'},
            {'name': 'Dissertation Guides', 'slug': 'dissertation-guides', 'parent_slug': 'academics'},
            {'name': 'Conference Proceedings', 'slug': 'conference-proceedings', 'parent_slug': 'academics'},
            {'name': 'Journal Publications', 'slug': 'journal-publications', 'parent_slug': 'academics'},
            {'name': 'Usul al-Fiqh', 'slug': 'usul-fiqh', 'parent_slug': 'academics'},
            {'name': 'Usul al-Hadith', 'slug': 'usul-hadith', 'parent_slug': 'academics'},
            {'name': 'Usul at-Tafseer', 'slug': 'usul-tafseer', 'parent_slug': 'academics'},
            {'name': 'Logic (Mantiq)', 'slug': 'logic', 'parent_slug': 'academics'},
            {'name': 'Rhetoric (Balagha)', 'slug': 'rhetoric', 'parent_slug': 'academics'},
            {'name': 'Prosody (Arud)', 'slug': 'prosody', 'parent_slug': 'academics'},
            
            # General Islamic categories
            {'name': 'Islamic Jurisprudence', 'slug': 'fiqh'},
            {'name': 'Biography of Prophet', 'slug': 'seerah'},
            {'name': 'Islamic History', 'slug': 'islamic-history'},
            {'name': 'Contemporary Issues', 'slug': 'contemporary-issues'},
            {'name': 'Spirituality & Sufism', 'slug': 'spirituality'},
            {'name': 'Comparative Religion', 'slug': 'comparative-religion'},
            {'name': 'Islamic Philosophy', 'slug': 'islamic-philosophy'},
            {'name': 'Islamic Ethics', 'slug': 'akhlaq'},
            {'name': 'Dua Books', 'slug': 'dua-books'},
            {'name': 'Islamic Poetry', 'slug': 'poetry'},
            {'name': 'Children Books', 'slug': 'children'},
            {'name': 'Islamic Creed', 'slug': 'aqeedah'},
            {'name': 'Arabic Grammar', 'slug': 'arabic-grammar'},
            {'name': 'Classical Texts', 'slug': 'classical-texts'},
        ]
        
        # Create subcategories
        for subcat_data in subcategories:
            existing = Category.query.filter_by(slug=subcat_data['slug']).first()
            if not existing:
                parent_id = None
                if 'parent_slug' in subcat_data and subcat_data['parent_slug'] in main_cat_objects:
                    parent_id = main_cat_objects[subcat_data['parent_slug']].id
                
                category = Category(
                    name=subcat_data['name'],
                    slug=subcat_data['slug'],
                    description=subcat_data.get('description', f"Books on {subcat_data['name']}"),
                    parent_id=parent_id,
                    is_active=True
                )
                db.session.add(category)
                print(f"✅ Created subcategory: {subcat_data['name']}")
            else:
                print(f"📚 Subcategory exists: {subcat_data['name']}")
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\n🎉 Successfully created/verified all navigation categories!")
            
            # Count categories
            total_categories = Category.query.count()
            main_categories_count = Category.query.filter_by(parent_id=None).count()
            subcategories_count = Category.query.filter(Category.parent_id != None).count()
            
            print(f"📊 Database Summary:")
            print(f"   • Total categories: {total_categories}")
            print(f"   • Main categories: {main_categories_count}")
            print(f"   • Subcategories: {subcategories_count}")
            
        except Exception as e:
            print(f"❌ Error creating categories: {str(e)}")
            db.session.rollback()
            return False
        
        return True

if __name__ == '__main__':
    print("🚀 Creating navigation categories...")
    success = create_categories()
    if success:
        print("✅ Navigation categories setup complete!")
    else:
        print("❌ Failed to setup categories")
        sys.exit(1)
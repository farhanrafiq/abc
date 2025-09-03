"""Initialize demo data for Islamic bookstore"""
from app import app, db
from models import (
    User, Category, Author, Publisher, Product, Price, Inventory, 
    ProductStatus, Language, Format, UserRole, Review
)
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

def init_demo_data():
    """Initialize database with Islamic literature demo data"""
    
    with app.app_context():
        # Clear existing data
        print("Clearing existing data...")
        db.drop_all()
        db.create_all()
        
        # Create Admin User
        admin = User(
            name="Admin User",
            email="admin@abcpublishing.com",
            phone="+92-300-1234567",
            role=UserRole.ADMIN,
            active=True
        )
        admin.set_password("admin123")
        db.session.add(admin)
        
        # Create Customer Users
        customer1 = User(
            name="Ahmad Hassan",
            email="ahmad@example.com",
            phone="+92-321-9876543",
            role=UserRole.CUSTOMER,
            active=True
        )
        customer1.set_password("customer123")
        db.session.add(customer1)
        
        customer2 = User(
            name="Fatima Ali",
            email="fatima@example.com",
            phone="+92-333-5554444",
            role=UserRole.CUSTOMER,
            active=True
        )
        customer2.set_password("customer123")
        db.session.add(customer2)
        
        # Create Categories
        categories = [
            Category(
                name="Tafaseer-ul-Quran",
                slug="tafaseer-ul-quran",
                description="Commentaries and explanations of the Holy Quran by renowned scholars",
                is_active=True
            ),
            Category(
                name="Hadith Collections",
                slug="hadith-collections",
                description="Authentic collections of Prophet Muhammad's (PBUH) sayings and traditions",
                is_active=True
            ),
            Category(
                name="Seerat & Biography",
                slug="seerat-biography",
                description="Life stories of Prophet Muhammad (PBUH) and Islamic personalities",
                is_active=True
            ),
            Category(
                name="Fiqh & Islamic Law",
                slug="fiqh-islamic-law",
                description="Islamic jurisprudence and legal texts",
                is_active=True
            ),
            Category(
                name="Tasawwuf & Spirituality",
                slug="tasawwuf-spirituality",
                description="Islamic spirituality, sufism, and self-purification",
                is_active=True
            ),
            Category(
                name="Islamic History",
                slug="islamic-history",
                description="Historical accounts of Islamic civilization and Muslim rulers",
                is_active=True
            ),
            Category(
                name="Aqeedah & Theology",
                slug="aqeedah-theology",
                description="Islamic beliefs, creed, and theological discussions",
                is_active=True
            ),
            Category(
                name="Arabic Literature",
                slug="arabic-literature",
                description="Classical and modern Arabic literary works",
                is_active=True
            ),
            Category(
                name="Children's Islamic Books",
                slug="childrens-islamic",
                description="Islamic stories and education for young readers",
                is_active=True
            ),
            Category(
                name="Contemporary Islamic Thought",
                slug="contemporary-islamic",
                description="Modern Islamic scholarship and contemporary issues",
                is_active=True
            )
        ]
        db.session.add_all(categories)
        db.session.commit()
        
        # Create Authors
        authors = [
            Author(name="Dr. Israr Ahmed", slug="dr-israr-ahmed", 
                   bio="Renowned Pakistani Islamic scholar and founder of Tanzeem-e-Islami"),
            Author(name="Imam Ibn Kathir", slug="imam-ibn-kathir",
                   bio="Famous 14th century Islamic scholar known for his Tafsir"),
            Author(name="Maulana Mufti Taqi Usmani", slug="mufti-taqi-usmani",
                   bio="Leading Islamic scholar and expert in Islamic finance"),
            Author(name="Imam Al-Ghazali", slug="imam-al-ghazali",
                   bio="Medieval Muslim theologian and mystic"),
            Author(name="Allama Iqbal", slug="allama-iqbal",
                   bio="Poet-philosopher of the East and spiritual father of Pakistan"),
            Author(name="Maulana Abul A'la Maududi", slug="maulana-maududi",
                   bio="Islamic scholar and founder of Jamaat-e-Islami"),
            Author(name="Sheikh Abdul Qadir Jilani", slug="abdul-qadir-jilani",
                   bio="Hanbali Sunni Muslim preacher and founder of Qadiriyya Sufi order"),
            Author(name="Dr. Muhammad Hamidullah", slug="dr-hamidullah",
                   bio="Islamic scholar and researcher of Islamic history"),
            Author(name="Maulana Ashraf Ali Thanwi", slug="ashraf-ali-thanwi",
                   bio="Islamic scholar of the Deobandi school of thought"),
            Author(name="Shah Waliullah Dehlawi", slug="shah-waliullah",
                   bio="18th century Islamic scholar and reformer")
        ]
        db.session.add_all(authors)
        db.session.commit()
        
        # Create Publishers
        publishers = [
            Publisher(name="Darul Ishaat", slug="darul-ishaat",
                     description="Leading Islamic publisher based in Karachi"),
            Publisher(name="Darussalam Publishers", slug="darussalam",
                     description="International Islamic publishing house"),
            Publisher(name="Idara-e-Islamiat", slug="idara-islamiat",
                     description="Renowned publisher of Islamic books in Urdu"),
            Publisher(name="Maktaba Al-Bushra", slug="maktaba-bushra",
                     description="Publisher of classical Islamic texts"),
            Publisher(name="Zam Zam Publishers", slug="zamzam",
                     description="Publishers of authentic Islamic literature")
        ]
        db.session.add_all(publishers)
        db.session.commit()
        
        # Create Products
        products_data = [
            # Tafseer Books
            {
                "title": "Tafseer Bayan-ul-Quran (7 Volume Set)",
                "title_urdu": "تفسیر بیان القرآن",
                "author": authors[0],  # Dr. Israr Ahmed
                "category": categories[0],  # Tafaseer
                "publisher": publishers[0],
                "language": "UR",
                "isbn": "9789694960128",
                "pages": 4500,
                "format": "Hardcover",
                "description": "Comprehensive Urdu commentary on the Holy Quran by Dr. Israr Ahmed, providing deep insights into Quranic verses with contemporary relevance.",
                "mrp": 750000,  # ₹7500
                "sale_price": 550000,  # ₹5500
                "stock": 25
            },
            {
                "title": "Tafseer Ibn Kathir (English Translation)",
                "title_arabic": "تفسير ابن كثير",
                "author": authors[1],  # Ibn Kathir
                "category": categories[0],
                "publisher": publishers[1],
                "language": "EN",
                "isbn": "9789960892719",
                "pages": 6600,
                "format": "Hardcover",
                "description": "The most popular interpretation of the Quran in the Arabic language, now available in comprehensive English translation.",
                "mrp": 900000,
                "sale_price": 700000,
                "stock": 15
            },
            {
                "title": "Ma'ariful Quran (8 Volume Set)",
                "title_urdu": "معارف القرآن",
                "author": authors[2],  # Mufti Taqi Usmani
                "category": categories[0],
                "publisher": publishers[2],
                "language": "UR",
                "isbn": "9789695740156",
                "pages": 7200,
                "format": "Hardcover",
                "description": "A comprehensive and detailed commentary of the Holy Quran written by Mufti Muhammad Shafi, revised by Mufti Taqi Usmani.",
                "mrp": 1200000,
                "sale_price": 960000,
                "stock": 20
            },
            
            # Hadith Books
            {
                "title": "Sahih Bukhari (Urdu Translation)",
                "title_arabic": "صحيح البخاري",
                "author": authors[1],
                "category": categories[1],  # Hadith
                "publisher": publishers[1],
                "language": "UR",
                "isbn": "9789960717357",
                "pages": 3800,
                "format": "Hardcover",
                "description": "The most authentic book after the Holy Quran, containing sayings and actions of Prophet Muhammad (PBUH).",
                "mrp": 500000,
                "sale_price": 400000,
                "stock": 30
            },
            {
                "title": "Riyad-us-Saliheen",
                "title_arabic": "رياض الصالحين",
                "author": authors[1],
                "category": categories[1],
                "publisher": publishers[1],
                "language": "EN",
                "isbn": "9789960899633",
                "pages": 1200,
                "format": "Paperback",
                "description": "Gardens of the Righteous - A collection of authentic hadiths compiled by Imam Nawawi.",
                "mrp": 150000,
                "sale_price": 120000,
                "stock": 50
            },
            
            # Spirituality Books
            {
                "title": "Ihya Ulum-ud-Din (Revival of Religious Sciences)",
                "title_arabic": "إحياء علوم الدين",
                "author": authors[3],  # Al-Ghazali
                "category": categories[4],  # Tasawwuf
                "publisher": publishers[3],
                "language": "EN",
                "isbn": "9789830651996",
                "pages": 2400,
                "format": "Hardcover",
                "description": "Al-Ghazali's magnum opus on Islamic spirituality, ethics, and philosophy.",
                "mrp": 600000,
                "sale_price": 480000,
                "stock": 18
            },
            {
                "title": "The Alchemy of Happiness",
                "title_urdu": "کیمیائے سعادت",
                "author": authors[3],
                "category": categories[4],
                "publisher": publishers[3],
                "language": "EN",
                "isbn": "9781847740069",
                "pages": 350,
                "format": "Paperback",
                "description": "A guide to spiritual development and achieving true happiness through Islamic teachings.",
                "mrp": 80000,
                "sale_price": 65000,
                "stock": 40
            },
            
            # Seerat Books
            {
                "title": "Seerat-un-Nabi (The Life of the Prophet)",
                "title_urdu": "سیرت النبی",
                "author": authors[5],  # Maulana Maududi
                "category": categories[2],  # Seerat
                "publisher": publishers[2],
                "language": "UR",
                "isbn": "9789694960234",
                "pages": 1800,
                "format": "Hardcover",
                "description": "Complete biography of Prophet Muhammad (PBUH) with authentic sources and detailed analysis.",
                "mrp": 350000,
                "sale_price": 280000,
                "stock": 35
            },
            {
                "title": "Ar-Raheeq Al-Makhtum (The Sealed Nectar)",
                "title_arabic": "الرحيق المختوم",
                "author": authors[7],
                "category": categories[2],
                "publisher": publishers[1],
                "language": "EN",
                "isbn": "9789960899558",
                "pages": 600,
                "format": "Paperback",
                "description": "Award-winning biography of Prophet Muhammad (PBUH) by Sheikh Safi-ur-Rahman al-Mubarakpuri.",
                "mrp": 120000,
                "sale_price": 95000,
                "stock": 60
            },
            
            # Fiqh Books
            {
                "title": "Bahishti Zewar (Heavenly Ornaments)",
                "title_urdu": "بہشتی زیور",
                "author": authors[8],  # Ashraf Ali Thanwi
                "category": categories[3],  # Fiqh
                "publisher": publishers[2],
                "language": "UR",
                "isbn": "9789695740897",
                "pages": 900,
                "format": "Hardcover",
                "description": "Complete guide to Islamic law and daily life practices for Muslim families.",
                "mrp": 150000,
                "sale_price": 120000,
                "stock": 45
            },
            
            # Islamic History
            {
                "title": "The History of Islamic Civilization",
                "title_urdu": "تاریخ تمدن اسلامی",
                "author": authors[7],  # Dr. Hamidullah
                "category": categories[5],  # History
                "publisher": publishers[0],
                "language": "EN",
                "isbn": "9789694961234",
                "pages": 1200,
                "format": "Hardcover",
                "description": "Comprehensive history of Islamic civilization from its inception to modern times.",
                "mrp": 250000,
                "sale_price": 200000,
                "stock": 22
            },
            
            # Poetry
            {
                "title": "Kulliyat-e-Iqbal (Complete Works of Iqbal)",
                "title_urdu": "کلیات اقبال",
                "author": authors[4],  # Allama Iqbal
                "category": categories[7],  # Arabic Literature
                "publisher": publishers[2],
                "language": "UR",
                "isbn": "9789694962345",
                "pages": 1500,
                "format": "Hardcover",
                "description": "Complete collection of Allama Iqbal's Urdu and Persian poetry with commentary.",
                "mrp": 300000,
                "sale_price": 240000,
                "stock": 38
            },
            {
                "title": "Bang-e-Dara (The Call of the Marching Bell)",
                "title_urdu": "بانگ درا",
                "author": authors[4],
                "category": categories[7],
                "publisher": publishers[2],
                "language": "UR",
                "isbn": "9789694963456",
                "pages": 400,
                "format": "Paperback",
                "description": "First Urdu philosophical poetry book by Allama Iqbal.",
                "mrp": 60000,
                "sale_price": 48000,
                "stock": 55
            },
            
            # Contemporary Islamic Thought
            {
                "title": "Islam and Modern Challenges",
                "author": authors[2],  # Mufti Taqi Usmani
                "category": categories[9],
                "publisher": publishers[0],
                "language": "EN",
                "isbn": "9789694964567",
                "pages": 450,
                "format": "Paperback",
                "description": "Addressing contemporary issues faced by Muslims in the modern world.",
                "mrp": 90000,
                "sale_price": 72000,
                "stock": 42
            },
            
            # Children's Books
            {
                "title": "Stories of the Prophets for Children",
                "title_urdu": "قصص الانبیاء برائے اطفال",
                "author": authors[5],
                "category": categories[8],
                "publisher": publishers[1],
                "language": "EN",
                "isbn": "9789960965678",
                "pages": 200,
                "format": "Paperback",
                "description": "Beautifully illustrated stories of the Prophets for young readers.",
                "mrp": 50000,
                "sale_price": 40000,
                "stock": 70
            }
        ]
        
        # Create products with relationships
        for prod_data in products_data:
            product = Product(
                title=prod_data["title"],
                title_urdu=prod_data.get("title_urdu"),
                title_arabic=prod_data.get("title_arabic"),
                slug=prod_data["title"].lower().replace(" ", "-").replace("(", "").replace(")", ""),
                isbn=prod_data["isbn"],
                description=prod_data["description"],
                pages=prod_data["pages"],
                language=prod_data["language"],
                format=prod_data["format"],
                status=ProductStatus.ACTIVE,
                publisher_id=prod_data["publisher"].id,
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 90))
            )
            
            # Add author
            product.authors.append(prod_data["author"])
            
            # Add category
            product.categories.append(prod_data["category"])
            
            db.session.add(product)
            db.session.flush()  # Get the product ID
            
            # Add price
            price = Price(
                product_id=product.id,
                mrp_inr=prod_data["mrp"],
                sale_inr=prod_data["sale_price"],
                tax_rate_pct=5  # 5% GST on books
            )
            db.session.add(price)
            
            # Add inventory
            inventory = Inventory(
                product_id=product.id,
                sku="SKU-" + str(product.id).zfill(6),
                stock_on_hand=prod_data["stock"],
                low_stock_threshold=5
            )
            db.session.add(inventory)
            
            # Add sample reviews
            if random.random() > 0.3:  # 70% chance of having reviews
                for _ in range(random.randint(1, 5)):
                    review = Review(
                        product_id=product.id,
                        user_id=random.choice([customer1.id, customer2.id]),
                        rating=random.randint(4, 5),
                        title="Excellent Book",
                        body=random.choice([
                            "Excellent book! Highly recommended for anyone seeking Islamic knowledge.",
                            "Beautiful edition with clear print. Very satisfied with the purchase.",
                            "A must-have in every Muslim's library. Great quality and fast delivery.",
                            "Authentic translation with helpful commentary. Worth every penny.",
                            "Outstanding work by the author. Packaging was excellent too."
                        ]),
                        is_approved=True,
                        created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
                    )
                    db.session.add(review)
        
        # Commit all changes
        db.session.commit()
        print("Demo data initialized successfully!")
        print(f"Created {len(products_data)} products with prices and inventory")
        print(f"Created {len(categories)} categories")
        print(f"Created {len(authors)} authors")
        print(f"Created {len(publishers)} publishers")
        print("Admin login: admin@abcpublishing.com / admin123")
        print("Customer login: ahmad@example.com / customer123")

if __name__ == "__main__":
    init_demo_data()
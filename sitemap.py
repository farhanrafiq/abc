from flask import Blueprint, Response, request, url_for
from models import Product, Category, ContentPage, ProductStatus
from app import db
from datetime import datetime

sitemap_bp = Blueprint('sitemap', __name__)

@sitemap_bp.route('/sitemap.xml')
def sitemap():
    """Generate dynamic XML sitemap for SEO"""
    pages = []
    host = request.url_root.rstrip('/')
    
    # Static pages
    static_pages = [
        {'loc': host + '/', 'priority': '1.0', 'changefreq': 'daily'},
        {'loc': host + '/catalog', 'priority': '0.9', 'changefreq': 'daily'},
        {'loc': host + '/about', 'priority': '0.7', 'changefreq': 'weekly'},
        {'loc': host + '/contact', 'priority': '0.7', 'changefreq': 'monthly'},
        {'loc': host + '/faq', 'priority': '0.6', 'changefreq': 'monthly'},
        {'loc': host + '/privacy', 'priority': '0.5', 'changefreq': 'monthly'},
        {'loc': host + '/terms', 'priority': '0.5', 'changefreq': 'monthly'},
        {'loc': host + '/returns', 'priority': '0.6', 'changefreq': 'monthly'},
    ]
    
    for page in static_pages:
        pages.append(page)
    
    # Category pages
    categories = Category.query.filter_by(is_active=True).all()
    for category in categories:
        pages.append({
            'loc': host + url_for('web.catalog', category_slug=category.slug),
            'priority': '0.8',
            'changefreq': 'weekly',
            'lastmod': category.updated_at.strftime('%Y-%m-%d') if category.updated_at else None
        })
    
    # Product pages
    products = Product.query.filter_by(status=ProductStatus.ACTIVE).all()
    for product in products:
        pages.append({
            'loc': host + url_for('web.product_detail', slug=product.slug),
            'priority': '0.9',
            'changefreq': 'weekly',
            'lastmod': product.updated_at.strftime('%Y-%m-%d') if product.updated_at else None
        })
    
    # Content pages
    content_pages = ContentPage.query.filter_by(is_active=True).all()
    for page in content_pages:
        pages.append({
            'loc': host + url_for('web.page', slug=page.slug),
            'priority': '0.6',
            'changefreq': 'monthly',
            'lastmod': page.updated_at.strftime('%Y-%m-%d') if page.updated_at else None
        })
    
    # Generate XML
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for page in pages:
        xml += '  <url>\n'
        xml += f'    <loc>{page["loc"]}</loc>\n'
        if page.get('lastmod'):
            xml += f'    <lastmod>{page["lastmod"]}</lastmod>\n'
        xml += f'    <changefreq>{page["changefreq"]}</changefreq>\n'
        xml += f'    <priority>{page["priority"]}</priority>\n'
        xml += '  </url>\n'
    
    xml += '</urlset>'
    
    return Response(xml, mimetype='text/xml')

@sitemap_bp.route('/robots.txt')
def robots():
    """Generate robots.txt for search engines"""
    content = """User-agent: *
Allow: /

# Allow crawling of CSS and JS files
Allow: /static/css/
Allow: /static/js/
Allow: /static/images/

# Disallow admin and auth areas
Disallow: /admin/
Disallow: /auth/
Disallow: /api/
Disallow: /cart/checkout
Disallow: /account/

# Crawl delay
Crawl-delay: 1

# Sitemap location
Sitemap: {}/sitemap.xml
""".format(request.url_root.rstrip('/'))
    
    return Response(content, mimetype='text/plain')
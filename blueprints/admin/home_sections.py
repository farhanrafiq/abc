from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required
from app import db
from models import HomeSection, SectionType, MediaAsset
from models import Product, Author, Publisher, Category
import json
from datetime import datetime

admin_home_bp = Blueprint('admin_home', __name__)


@admin_home_bp.route('/admin/home')
@login_required
def home_sections_list():
    """Admin homepage builder - list and manage sections"""
    sections = HomeSection.query.order_by(HomeSection.position).all()
    return render_template('admin/home_sections_list.html', sections=sections)


@admin_home_bp.route('/admin/home/new', methods=['GET', 'POST'])
@login_required
def new_section():
    """Create a new homepage section"""
    if request.method == 'GET':
        return render_template('admin/home_section_form.html', 
                             section=None, 
                             section_types=SectionType)
    
    try:
        section_type = SectionType(request.form.get('type'))
        title = request.form.get('title', '')
        subtitle = request.form.get('subtitle', '')
        
        # Build config from form data
        config = build_config_from_form(section_type, request.form)
        
        # Validate config
        is_valid, errors = validate_section_config(section_type, config)
        if not is_valid:
            flash(f"Configuration errors: {', '.join(errors)}", 'error')
            return render_template('admin/home_section_form.html',
                                 section=None,
                                 section_types=SectionType,
                                 form_data=request.form,
                                 errors=errors)
        
        # Get next position
        max_position = db.session.query(db.func.max(HomeSection.position)).scalar() or 0
        
        section = HomeSection(
            type=section_type,
            title=title,
            subtitle=subtitle,
            config=config,
            position=max_position + 1,
            is_active=request.form.get('is_active') == 'on'
        )
        
        # Handle scheduling
        start_at = request.form.get('start_at')
        end_at = request.form.get('end_at')
        
        if start_at:
            section.start_at = datetime.fromisoformat(start_at)
        if end_at:
            section.end_at = datetime.fromisoformat(end_at)
        
        db.session.add(section)
        db.session.commit()
        
        flash('Section created successfully!', 'success')
        return redirect(url_for('admin_home.home_sections_list'))
        
    except Exception as e:
        flash(f'Error creating section: {str(e)}', 'error')
        return render_template('admin/home_section_form.html',
                             section=None,
                             section_types=SectionType,
                             form_data=request.form)


@admin_home_bp.route('/admin/home/<int:section_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_section(section_id):
    """Edit an existing homepage section"""
    section = HomeSection.query.get_or_404(section_id)
    
    if request.method == 'GET':
        return render_template('admin/home_section_form.html',
                             section=section,
                             section_types=SectionType)
    
    try:
        section.title = request.form.get('title', '')
        section.subtitle = request.form.get('subtitle', '')
        
        # Build and validate config
        config = build_config_from_form(section.type, request.form)
        is_valid, errors = validate_section_config(section.type, config)
        
        if not is_valid:
            flash(f"Configuration errors: {', '.join(errors)}", 'error')
            return render_template('admin/home_section_form.html',
                                 section=section,
                                 section_types=SectionType,
                                 form_data=request.form,
                                 errors=errors)
        
        section.config = config
        section.is_active = request.form.get('is_active') == 'on'
        
        # Handle scheduling
        start_at = request.form.get('start_at')
        end_at = request.form.get('end_at')
        
        section.start_at = datetime.fromisoformat(start_at) if start_at else None
        section.end_at = datetime.fromisoformat(end_at) if end_at else None
        
        db.session.commit()
        flash('Section updated successfully!', 'success')
        return redirect(url_for('admin_home.home_sections_list'))
        
    except Exception as e:
        flash(f'Error updating section: {str(e)}', 'error')
        return render_template('admin/home_section_form.html',
                             section=section,
                             section_types=SectionType,
                             form_data=request.form)


@admin_home_bp.route('/admin/home/reorder', methods=['POST'])
@login_required
def reorder_sections():
    """Reorder homepage sections via drag and drop"""
    try:
        section_orders = request.json.get('sections', [])
        
        for item in section_orders:
            section_id = item.get('id')
            new_position = item.get('position')
            
            section = HomeSection.query.get(section_id)
            if section:
                section.position = new_position
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Sections reordered successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@admin_home_bp.route('/admin/home/<int:section_id>/toggle', methods=['PATCH'])
@login_required
def toggle_section(section_id):
    """Toggle section active state"""
    try:
        section = HomeSection.query.get_or_404(section_id)
        section.is_active = not section.is_active
        db.session.commit()
        
        return jsonify({
            'success': True,
            'is_active': section.is_active,
            'message': f'Section {"activated" if section.is_active else "deactivated"}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@admin_home_bp.route('/admin/home/<int:section_id>/delete', methods=['DELETE'])
@login_required
def delete_section(section_id):
    """Delete a homepage section"""
    try:
        section = HomeSection.query.get_or_404(section_id)
        db.session.delete(section)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Section deleted successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@admin_home_bp.route('/api/home-preview/<int:section_id>')
@login_required
def preview_section(section_id):
    """Render section preview for admin panel"""
    section = HomeSection.query.get_or_404(section_id)
    
    # Get template name for section type
    template_name = f'storefront/sections/{section.type.value}.html'
    
    try:
        # Get section data
        section_data = get_section_data(section)
        
        return render_template(template_name, 
                             section=section,
                             **section_data)
    except Exception as e:
        return f"<div class='alert alert-error'>Error rendering preview: {str(e)}</div>"


def build_config_from_form(section_type, form_data):
    """Build section config from form data"""
    config = {}
    
    if section_type == SectionType.HERO_SLIDER:
        config = {
            'show_arrows': form_data.get('show_arrows') == 'on',
            'show_dots': form_data.get('show_dots') == 'on',
            'autoplay_enabled': form_data.get('autoplay_enabled') == 'on',
            'autoplay_interval_ms': int(form_data.get('autoplay_interval_ms', 5000)),
            'transition': form_data.get('transition', 'fade'),
            'transition_ms': int(form_data.get('transition_ms', 600))
        }
    
    elif section_type == SectionType.TRUST_BADGES:
        items = []
        item_count = int(form_data.get('item_count', 0))
        for i in range(item_count):
            item = {
                'icon_name': form_data.get(f'item_{i}_icon_name', ''),
                'label': form_data.get(f'item_{i}_label', ''),
                'sublabel': form_data.get(f'item_{i}_sublabel', '')
            }
            if item['label']:  # Only add if has content
                items.append(item)
        config = {'items': items}
    
    elif section_type == SectionType.CATEGORY_TILES:
        tiles = []
        tile_count = int(form_data.get('tile_count', 0))
        for i in range(tile_count):
            tile = {
                'title': form_data.get(f'tile_{i}_title', ''),
                'slug': form_data.get(f'tile_{i}_slug', ''),
                'image_url': form_data.get(f'tile_{i}_image_url', ''),
                'accent_color': form_data.get(f'tile_{i}_accent_color', '#E86A17')
            }
            if tile['title']:  # Only add if has content
                tiles.append(tile)
        config = {
            'tiles': tiles,
            'columns_mobile': int(form_data.get('columns_mobile', 2)),
            'columns_desktop': int(form_data.get('columns_desktop', 4))
        }
    
    elif section_type in [SectionType.FEATURED_COLLECTION, SectionType.NEW_ARRIVALS, SectionType.BESTSELLERS]:
        config = {
            'data_source': form_data.get('data_source', 'query'),
            'limit': int(form_data.get('limit', 8)),
            'layout': form_data.get('layout', 'grid'),
            'show_price_badges': form_data.get('show_price_badges') == 'on'
        }
        
        if config['data_source'] == 'manual':
            product_ids = form_data.get('manual_product_ids', '')
            config['manual_product_ids'] = [int(id.strip()) for id in product_ids.split(',') if id.strip().isdigit()]
        else:
            config['query'] = {
                'category_slug': form_data.get('category_slug', ''),
                'sort': form_data.get('sort', 'newest')
            }
    
    elif section_type == SectionType.STAFF_PICKS:
        items = []
        item_count = int(form_data.get('item_count', 0))
        for i in range(item_count):
            item = {
                'product_id': int(form_data.get(f'item_{i}_product_id', 0)),
                'editor_note': form_data.get(f'item_{i}_editor_note', '')
            }
            if item['product_id']:
                items.append(item)
        config = {'items': items}
    
    elif section_type == SectionType.DEALS_OF_DAY:
        items = []
        item_count = int(form_data.get('item_count', 0))
        for i in range(item_count):
            ends_at = form_data.get(f'item_{i}_ends_at')
            item = {
                'product_id': int(form_data.get(f'item_{i}_product_id', 0)),
                'deal_price': float(form_data.get(f'item_{i}_deal_price', 0)),
                'ends_at': ends_at
            }
            if item['product_id']:
                items.append(item)
        config = {'items': items}
    
    elif section_type == SectionType.AUTHOR_SPOTLIGHT:
        config = {
            'author_id': int(form_data.get('author_id', 0)),
            'portrait_url': form_data.get('portrait_url', ''),
            'blurb': form_data.get('blurb', '')
        }
    
    elif section_type == SectionType.PUBLISHER_SPOTLIGHT:
        config = {
            'publisher_id': int(form_data.get('publisher_id', 0)),
            'logo_url': form_data.get('logo_url', ''),
            'blurb': form_data.get('blurb', '')
        }
    
    elif section_type == SectionType.NEWSLETTER_BAR:
        config = {
            'title': form_data.get('newsletter_title', 'Stay Updated'),
            'subtitle': form_data.get('newsletter_subtitle', 'Subscribe to our newsletter'),
            'placeholder_text': form_data.get('placeholder_text', 'Enter your email'),
            'submit_label': form_data.get('submit_label', 'Subscribe')
        }
    
    elif section_type == SectionType.QUICK_ORDER_ISBN:
        config = {
            'enable_scanner': form_data.get('enable_scanner') == 'on',
            'note_text': form_data.get('note_text', '')
        }
    
    # Add more section types as needed...
    
    return config


def get_section_data(section):
    """Get data needed to render a section"""
    data = {}
    
    if section.type in [SectionType.FEATURED_COLLECTION, SectionType.NEW_ARRIVALS, SectionType.BESTSELLERS]:
        data_source = section.get_config_value('data_source', 'query')
        limit = section.get_config_value('limit', 8)
        
        if data_source == 'manual':
            product_ids = section.get_config_value('manual_product_ids', [])
            products = Product.query.filter(Product.id.in_(product_ids)).limit(limit).all()
        else:
            query_config = section.get_config_value('query', {})
            category_slug = query_config.get('category_slug')
            sort_by = query_config.get('sort', 'newest')
            
            query = Product.query.filter_by(status='active')
            
            if category_slug:
                query = query.join(Product.categories).filter_by(slug=category_slug)
            
            if sort_by == 'newest':
                query = query.order_by(Product.created_at.desc())
            elif sort_by == 'price_low':
                query = query.join(Product.price).order_by(Product.price.sale_inr.asc())
            elif sort_by == 'price_high':
                query = query.join(Product.price).order_by(Product.price.sale_inr.desc())
            
            products = query.limit(limit).all()
        
        data['products'] = products
    
    elif section.type == SectionType.AUTHOR_SPOTLIGHT:
        author_id = section.get_config_value('author_id')
        if author_id:
            data['author'] = Author.query.get(author_id)
    
    elif section.type == SectionType.PUBLISHER_SPOTLIGHT:
        publisher_id = section.get_config_value('publisher_id')
        if publisher_id:
            data['publisher'] = Publisher.query.get(publisher_id)
    
    elif section.type == SectionType.STAFF_PICKS:
        items = section.get_config_value('items', [])
        staff_picks = []
        for item in items:
            product = Product.query.get(item.get('product_id'))
            if product:
                staff_picks.append({
                    'product': product,
                    'editor_note': item.get('editor_note', '')
                })
        data['staff_picks'] = staff_picks
    
    # Add more data loading for other section types...
    
    return data
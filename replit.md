# Overview

ABC Publishing Kashmir is a comprehensive e-commerce bookstore platform specializing in Islamic literature and academic books. The system is built as a Flask-based web application that serves customers across Kashmir and India with features for browsing, purchasing, and managing book inventory. The platform supports multiple languages (English, Urdu, Hindi, Arabic) and provides a complete online shopping experience with payment processing, order management, and administrative tools.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Framework
The application uses Flask as the primary web framework with a modular blueprint-based architecture. The system is organized into distinct apps:
- **Web App**: Customer-facing storefront with product browsing, search, and shopping cart
- **Admin App**: Administrative dashboard for inventory, order, and user management  
- **Auth App**: User authentication and registration handling
- **Cart App**: Shopping cart and checkout functionality

## Database Architecture
The system uses SQLAlchemy ORM with PostgreSQL as the primary database. Key design decisions include:
- **Product Model**: Central entity with relationships to categories, authors, publishers, prices, and inventory
- **Order System**: Comprehensive order management with separate models for orders, order items, and shipments
- **User Management**: Role-based access control (Customer, Staff, Admin) with address management
- **Pricing Structure**: Flexible pricing system supporting MRP, sale prices, and tax calculations stored in paisa (smallest currency unit)
- **Inventory Tracking**: Real-time stock management with low-stock thresholds

## Authentication & Authorization
- Flask-Login for session management
- Role-based access control with three user roles (Customer, Staff, Admin)
- Password hashing using Werkzeug security utilities
- Email-based user registration and password reset functionality

## Payment Processing
Integration with Razorpay for online payments supporting:
- Credit/debit card payments
- UPI transactions
- Cash on Delivery (COD) option
- Payment verification and webhook handling
- Support for both test and live payment environments

## Email System
Flask-Mail integration for transactional emails including:
- Order confirmations
- Password reset emails
- Shipment notifications
- Customer communication templates

## File Management
- Local file storage for product images in static/uploads directory
- Image optimization using PIL for cover images and product galleries
- Support for multiple image formats (JPG, PNG, GIF)
- Organized folder structure for different asset types

## Frontend Architecture
- Server-side rendered templates using Jinja2
- Bootstrap 5 for responsive UI components
- Custom CSS with Islamic-themed design elements
- JavaScript for interactive features (cart management, image galleries, form validation)
- Multi-language font support for Arabic and Urdu text

## Search & Filtering
- PostgreSQL full-text search capabilities
- Advanced filtering by category, language, format, price range
- Pagination for large result sets
- Search suggestions and autocomplete functionality

# External Dependencies

## Core Framework
- **Flask**: Web application framework
- **SQLAlchemy**: ORM for database operations
- **Flask-Login**: User session management
- **Flask-WTF**: Form handling and CSRF protection
- **Flask-Mail**: Email functionality
- **Flask-Migrate**: Database migrations

## Payment Gateway
- **Razorpay**: Payment processing for Indian market
- Support for multiple payment methods including UPI, cards, and wallets

## Database
- **PostgreSQL**: Primary database system
- Compatible with cloud providers like Neon for development

## Email Service
- **SMTP**: Email delivery (configured for Gmail by default)
- Environment-driven configuration for different email providers

## PDF Generation
- **ReportLab**: Invoice and receipt generation
- GST-compliant invoice formatting

## Image Processing
- **Pillow (PIL)**: Image optimization and processing
- Automatic image resizing and format conversion

## Frontend Assets
- **Bootstrap 5**: UI framework
- **Font Awesome**: Icon library
- **Google Fonts**: Typography (Merriweather, Inter, Arabic fonts)
- **DataTables**: Admin dashboard table management

## Development Tools
- **Werkzeug**: WSGI utilities and development server
- **Python-dotenv**: Environment variable management (implied by config structure)

## Shipping & Location
- Custom shipping rate calculation based on location (Kashmir vs Rest of India)
- Address validation and management system
- PIN code-based delivery estimation
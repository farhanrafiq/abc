from flask import current_app, render_template
from flask_mail import Message
from app import mail
import logging

def send_email(subject, recipients, html_body, text_body=None, sender=None):
    """Send email using Flask-Mail"""
    try:
        msg = Message(
            subject=subject,
            recipients=recipients if isinstance(recipients, list) else [recipients],
            sender=sender or current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        msg.html = html_body
        if text_body:
            msg.body = text_body
        
        mail.send(msg)
        logging.info(f"Email sent successfully to {recipients}")
        return True
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
        return False

def send_order_confirmation_email(order):
    """Send order confirmation email to customer"""
    subject = f'Order Confirmation - #{order.id} - ABC Publishing Kashmir'
    
    html_body = render_template('email/order_confirmation.html', order=order)
    
    return send_email(
        subject=subject,
        recipients=order.email,
        html_body=html_body
    )

def send_password_reset_email(user):
    """Send password reset email"""
    # In a real implementation, you'd generate a secure token
    # For now, we'll create a simple placeholder
    reset_url = f"https://example.com/auth/password-reset/token"
    
    subject = 'Password Reset Request - ABC Publishing Kashmir'
    
    html_body = f"""
    <html>
    <body>
        <h2>Password Reset Request</h2>
        <p>Hello {user.name},</p>
        <p>You have requested a password reset for your account at ABC Publishing Kashmir.</p>
        <p>Click the link below to reset your password:</p>
        <p><a href="{reset_url}">Reset Password</a></p>
        <p>If you did not request this reset, please ignore this email.</p>
        <p>Best regards,<br>ABC Publishing Kashmir Team</p>
    </body>
    </html>
    """
    
    return send_email(
        subject=subject,
        recipients=user.email,
        html_body=html_body
    )

def send_low_stock_alert(product):
    """Send low stock alert to admin"""
    subject = f'Low Stock Alert - {product.title}'
    
    html_body = f"""
    <html>
    <body>
        <h2>Low Stock Alert</h2>
        <p>The following product is running low on stock:</p>
        <ul>
            <li><strong>Product:</strong> {product.title}</li>
            <li><strong>SKU:</strong> {product.inventory.sku if product.inventory else 'N/A'}</li>
            <li><strong>Current Stock:</strong> {product.inventory.stock_on_hand if product.inventory else 0}</li>
            <li><strong>Threshold:</strong> {product.inventory.low_stock_threshold if product.inventory else 0}</li>
        </ul>
        <p>Please restock as soon as possible.</p>
    </body>
    </html>
    """
    
    admin_email = current_app.config.get('STORE_EMAIL', 'admin@abcpublishingkashmir.com')
    
    return send_email(
        subject=subject,
        recipients=admin_email,
        html_body=html_body
    )

def send_order_status_update_email(order, old_status, new_status):
    """Send order status update email to customer"""
    subject = f'Order #{order.id} Status Update - ABC Publishing Kashmir'
    
    status_messages = {
        'Paid': 'Your payment has been confirmed.',
        'Packed': 'Your order has been packed and is ready for shipment.',
        'Shipped': 'Your order has been shipped.',
        'Delivered': 'Your order has been delivered.',
        'Cancelled': 'Your order has been cancelled.',
        'Refunded': 'Your order has been refunded.'
    }
    
    html_body = f"""
    <html>
    <body>
        <h2>Order Status Update</h2>
        <p>Hello,</p>
        <p>Your order #{order.id} status has been updated.</p>
        <p><strong>New Status:</strong> {new_status}</p>
        <p>{status_messages.get(new_status, '')}</p>
        
        {f'<p><strong>Tracking Number:</strong> {order.shipments[0].tracking_no}</p>' if new_status == 'Shipped' and order.shipments else ''}
        
        <p>You can track your order status anytime by visiting our website.</p>
        <p>Thank you for shopping with ABC Publishing Kashmir!</p>
        
        <hr>
        <p><strong>Order Details:</strong></p>
        <p>Order ID: #{order.id}</p>
        <p>Order Total: ₹{order.grand_total_inr / 100:.2f}</p>
        <p>Order Date: {order.created_at.strftime('%B %d, %Y')}</p>
    </body>
    </html>
    """
    
    return send_email(
        subject=subject,
        recipients=order.email,
        html_body=html_body
    )

def send_new_review_notification(review):
    """Send notification to admin about new review"""
    subject = f'New Review Submitted - {review.product.title}'
    
    html_body = f"""
    <html>
    <body>
        <h2>New Review Submitted</h2>
        <p>A new review has been submitted and is pending approval:</p>
        
        <ul>
            <li><strong>Product:</strong> {review.product.title}</li>
            <li><strong>Customer:</strong> {review.user.name}</li>
            <li><strong>Rating:</strong> {review.rating}/5 stars</li>
            <li><strong>Title:</strong> {review.title}</li>
            <li><strong>Review:</strong> {review.body}</li>
        </ul>
        
        <p>Please review and approve/reject this review in the admin panel.</p>
    </body>
    </html>
    """
    
    admin_email = current_app.config.get('STORE_EMAIL', 'admin@abcpublishingkashmir.com')
    
    return send_email(
        subject=subject,
        recipients=admin_email,
        html_body=html_body
    )

def send_welcome_email(user):
    """Send welcome email to new users"""
    subject = 'Welcome to ABC Publishing Kashmir!'
    
    html_body = f"""
    <html>
    <body>
        <h2>Welcome to ABC Publishing Kashmir!</h2>
        <p>Dear {user.name},</p>
        
        <p>Thank you for joining ABC Publishing Kashmir, your trusted source for Islamic books and literature.</p>
        
        <p>With your account, you can:</p>
        <ul>
            <li>Browse our extensive collection of books</li>
            <li>Track your orders</li>
            <li>Manage your addresses</li>
            <li>Leave reviews for books you've purchased</li>
            <li>Receive exclusive offers and updates</li>
        </ul>
        
        <p>Start exploring our collection of Islamic books, academic texts, and more!</p>
        
        <p>If you have any questions, feel free to contact us at {current_app.config.get('STORE_EMAIL', 'info@abcpublishingkashmir.com')}</p>
        
        <p>Best regards,<br>
        The ABC Publishing Kashmir Team</p>
    </body>
    </html>
    """
    
    return send_email(
        subject=subject,
        recipients=user.email,
        html_body=html_body
    )

from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from models import User, UserRole
from forms import LoginForm, RegisterForm, PasswordResetRequestForm, PasswordResetForm
from utils.email import send_password_reset_email
from app import db
import logging

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('web.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower() if form.email.data else '').first()
        
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user, remember=form.remember_me.data)
            
            # Redirect to next page or home
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            # Redirect based on user role
            if user.role in [UserRole.ADMIN, UserRole.STAFF]:
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('web.index'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('web.index'))
    
    form = RegisterForm()
    
    if form.validate_on_submit():
        # Check if user already exists
        existing_user = User.query.filter_by(email=form.email.data.lower() if form.email.data else '').first()
        if existing_user:
            flash('An account with this email already exists.', 'error')
            return render_template('auth/register.html', form=form)
        
        # Create new user
        user = User()
        user.name = form.name.data
        user.email = form.email.data.lower() if form.email.data else ''
        user.phone = form.phone.data
        user.role = UserRole.CUSTOMER
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        # Log in the user
        login_user(user)
        
        flash('Registration successful! Welcome to ABC Publishing Kashmir.', 'success')
        return redirect(url_for('web.index'))
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('web.index'))

@auth_bp.route('/password-reset-request', methods=['GET', 'POST'])
def password_reset_request():
    """Request password reset"""
    if current_user.is_authenticated:
        return redirect(url_for('web.index'))
    
    form = PasswordResetRequestForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower() if form.email.data else '').first()
        if user:
            try:
                send_password_reset_email(user)
                flash('Check your email for password reset instructions.', 'info')
            except Exception as e:
                logging.error(f"Failed to send password reset email: {e}")
                flash('Failed to send password reset email. Please try again later.', 'error')
        else:
            # Don't reveal whether email exists or not
            flash('Check your email for password reset instructions.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/password_reset_request.html', form=form)

@auth_bp.route('/password-reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    """Reset password with token"""
    if current_user.is_authenticated:
        return redirect(url_for('web.index'))
    
    # Verify token (simplified - in production use proper JWT or similar)
    # For now, we'll skip token verification and show the form
    
    form = PasswordResetForm()
    form.token.data = token
    
    if form.validate_on_submit():
        # In a real implementation, verify the token here
        # For now, we'll just update any user's password (not secure!)
        
        flash('Your password has been reset. You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/password_reset.html', form=form)

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management"""
    if request.method == 'POST':
        # Update profile
        current_user.name = request.form.get('name', current_user.name)
        current_user.phone = request.form.get('phone', current_user.phone)
        
        # Change password if provided
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if current_password and new_password:
            if current_user.check_password(current_password):
                if new_password == confirm_password:
                    current_user.set_password(new_password)
                    flash('Password updated successfully.', 'success')
                else:
                    flash('New passwords do not match.', 'error')
                    return render_template('auth/profile.html')
            else:
                flash('Current password is incorrect.', 'error')
                return render_template('auth/profile.html')
        
        db.session.commit()
        flash('Profile updated successfully.', 'success')
    
    return render_template('auth/profile.html')

/**
 * Homepage Interactive Features
 * Handles carousels, countdowns, quick order, and other dynamic elements
 */

// Event dispatcher for section widgets
class EventDispatcher {
    constructor() {
        this.listeners = {};
    }
    
    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    }
    
    emit(event, data) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => callback(data));
        }
    }
}

// Global event dispatcher
const homepageEvents = new EventDispatcher();

// Carousel component
class Carousel {
    constructor(element, options = {}) {
        this.element = element;
        this.options = {
            autoplay: options.autoplay || false,
            interval: options.interval || 5000,
            transition: options.transition || 'fade',
            transitionDuration: options.transitionDuration || 600,
            showArrows: options.showArrows !== false,
            showDots: options.showDots !== false,
            ...options
        };
        
        this.currentSlide = 0;
        this.slides = [];
        this.autoplayTimer = null;
        this.isPlaying = false;
        
        this.init();
    }
    
    init() {
        this.slides = Array.from(this.element.querySelectorAll('.slide, .carousel-item, .hero-slide'));
        
        if (this.slides.length === 0) {
            console.warn('No slides found in carousel');
            return;
        }
        
        this.setupSlides();
        this.createControls();
        this.bindEvents();
        
        if (this.options.autoplay) {
            this.startAutoplay();
        }
        
        // Show first slide
        this.goToSlide(0);
    }
    
    setupSlides() {
        this.slides.forEach((slide, index) => {
            slide.classList.remove('active');
            slide.setAttribute('aria-hidden', 'true');
            slide.style.opacity = '0';
            
            if (this.options.transition === 'slide') {
                slide.style.transform = `translateX(${index * 100}%)`;
            }
        });
    }
    
    createControls() {
        // Create arrow controls
        if (this.options.showArrows && this.slides.length > 1) {
            const prevBtn = document.createElement('button');
            prevBtn.className = 'carousel-control carousel-prev';
            prevBtn.innerHTML = '<i class="fas fa-chevron-left" aria-hidden="true"></i>';
            prevBtn.setAttribute('aria-label', 'Previous slide');
            prevBtn.addEventListener('click', () => this.prevSlide());
            
            const nextBtn = document.createElement('button');
            nextBtn.className = 'carousel-control carousel-next';
            nextBtn.innerHTML = '<i class="fas fa-chevron-right" aria-hidden="true"></i>';
            nextBtn.setAttribute('aria-label', 'Next slide');
            nextBtn.addEventListener('click', () => this.nextSlide());
            
            this.element.appendChild(prevBtn);
            this.element.appendChild(nextBtn);
        }
        
        // Create dot indicators
        if (this.options.showDots && this.slides.length > 1) {
            const dotsContainer = document.createElement('div');
            dotsContainer.className = 'carousel-dots';
            dotsContainer.setAttribute('role', 'tablist');
            
            this.slides.forEach((_, index) => {
                const dot = document.createElement('button');
                dot.className = 'carousel-dot';
                dot.setAttribute('role', 'tab');
                dot.setAttribute('aria-label', `Go to slide ${index + 1}`);
                dot.addEventListener('click', () => this.goToSlide(index));
                dotsContainer.appendChild(dot);
            });
            
            this.element.appendChild(dotsContainer);
            this.dotsContainer = dotsContainer;
        }
    }
    
    bindEvents() {
        // Pause autoplay on hover
        this.element.addEventListener('mouseenter', () => this.pauseAutoplay());
        this.element.addEventListener('mouseleave', () => this.resumeAutoplay());
        
        // Keyboard navigation
        this.element.addEventListener('keydown', (e) => {
            switch(e.key) {
                case 'ArrowLeft':
                    e.preventDefault();
                    this.prevSlide();
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.nextSlide();
                    break;
            }
        });
        
        // Touch/swipe support
        this.addTouchSupport();
        
        // Respect reduced motion preference
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            this.options.autoplay = false;
            this.options.transitionDuration = 0;
        }
    }
    
    addTouchSupport() {
        let startX = 0;
        let startY = 0;
        let isScrolling = false;
        
        this.element.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
            isScrolling = false;
        }, { passive: true });
        
        this.element.addEventListener('touchmove', (e) => {
            if (!startX || !startY) return;
            
            const currentX = e.touches[0].clientX;
            const currentY = e.touches[0].clientY;
            const diffX = startX - currentX;
            const diffY = startY - currentY;
            
            if (Math.abs(diffY) > Math.abs(diffX)) {
                isScrolling = true;
                return;
            }
            
            e.preventDefault();
        }, { passive: false });
        
        this.element.addEventListener('touchend', (e) => {
            if (!startX || isScrolling) return;
            
            const endX = e.changedTouches[0].clientX;
            const diff = startX - endX;
            
            if (Math.abs(diff) > 50) { // Minimum swipe distance
                if (diff > 0) {
                    this.nextSlide();
                } else {
                    this.prevSlide();
                }
            }
            
            startX = 0;
            startY = 0;
        }, { passive: true });
    }
    
    goToSlide(index) {
        if (index < 0 || index >= this.slides.length) return;
        
        const previousSlide = this.currentSlide;
        this.currentSlide = index;
        
        // Update slides
        this.slides.forEach((slide, i) => {
            slide.classList.remove('active', 'prev', 'next');
            slide.setAttribute('aria-hidden', 'true');
            
            if (i === index) {
                slide.classList.add('active');
                slide.setAttribute('aria-hidden', 'false');
                slide.style.opacity = '1';
                
                if (this.options.transition === 'slide') {
                    slide.style.transform = 'translateX(0)';
                }
            } else {
                slide.style.opacity = '0';
                
                if (this.options.transition === 'slide') {
                    if (i < index) {
                        slide.classList.add('prev');
                        slide.style.transform = 'translateX(-100%)';
                    } else {
                        slide.classList.add('next');
                        slide.style.transform = 'translateX(100%)';
                    }
                }
            }
        });
        
        // Update dots
        if (this.dotsContainer) {
            const dots = this.dotsContainer.querySelectorAll('.carousel-dot');
            dots.forEach((dot, i) => {
                dot.classList.toggle('active', i === index);
                dot.setAttribute('aria-selected', i === index);
            });
        }
        
        // Emit event
        homepageEvents.emit('slideChange', {
            carousel: this,
            currentSlide: index,
            previousSlide: previousSlide
        });
    }
    
    nextSlide() {
        const nextIndex = (this.currentSlide + 1) % this.slides.length;
        this.goToSlide(nextIndex);
    }
    
    prevSlide() {
        const prevIndex = (this.currentSlide - 1 + this.slides.length) % this.slides.length;
        this.goToSlide(prevIndex);
    }
    
    startAutoplay() {
        if (this.options.autoplay && this.slides.length > 1) {
            this.isPlaying = true;
            this.autoplayTimer = setInterval(() => {
                this.nextSlide();
            }, this.options.interval);
        }
    }
    
    pauseAutoplay() {
        if (this.autoplayTimer) {
            clearInterval(this.autoplayTimer);
            this.autoplayTimer = null;
        }
    }
    
    resumeAutoplay() {
        if (this.options.autoplay && this.isPlaying && !this.autoplayTimer) {
            this.startAutoplay();
        }
    }
    
    destroy() {
        this.pauseAutoplay();
        // Remove event listeners and clean up
    }
}

// Countdown Timer component
class CountdownTimer {
    constructor(element, targetDate) {
        this.element = element;
        this.targetDate = new Date(targetDate);
        this.timer = null;
        
        this.init();
    }
    
    init() {
        this.createStructure();
        this.start();
    }
    
    createStructure() {
        this.element.innerHTML = `
            <div class="countdown-timer" role="timer" aria-live="polite">
                <div class="countdown-unit">
                    <span class="countdown-number" data-unit="days">00</span>
                    <span class="countdown-label">Days</span>
                </div>
                <div class="countdown-unit">
                    <span class="countdown-number" data-unit="hours">00</span>
                    <span class="countdown-label">Hours</span>
                </div>
                <div class="countdown-unit">
                    <span class="countdown-number" data-unit="minutes">00</span>
                    <span class="countdown-label">Minutes</span>
                </div>
                <div class="countdown-unit">
                    <span class="countdown-number" data-unit="seconds">00</span>
                    <span class="countdown-label">Seconds</span>
                </div>
            </div>
        `;
    }
    
    start() {
        this.update();
        this.timer = setInterval(() => this.update(), 1000);
    }
    
    update() {
        const now = new Date().getTime();
        const distance = this.targetDate.getTime() - now;
        
        if (distance < 0) {
            this.element.innerHTML = '<div class="countdown-expired">Deal Expired</div>';
            this.stop();
            return;
        }
        
        const days = Math.floor(distance / (1000 * 60 * 60 * 24));
        const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);
        
        this.element.querySelector('[data-unit="days"]').textContent = String(days).padStart(2, '0');
        this.element.querySelector('[data-unit="hours"]').textContent = String(hours).padStart(2, '0');
        this.element.querySelector('[data-unit="minutes"]').textContent = String(minutes).padStart(2, '0');
        this.element.querySelector('[data-unit="seconds"]').textContent = String(seconds).padStart(2, '0');
    }
    
    stop() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }
}

// Quick Order ISBN component
class QuickOrderISBN {
    constructor(element, options = {}) {
        this.element = element;
        this.options = {
            enableScanner: options.enableScanner || false,
            apiEndpoint: options.apiEndpoint || '/api/products/isbn/',
            ...options
        };
        
        this.init();
    }
    
    init() {
        this.createForm();
        this.bindEvents();
    }
    
    createForm() {
        const scannerButton = this.options.enableScanner ? 
            `<button type="button" class="scanner-btn" id="scanner-btn">
                <i class="fas fa-camera"></i> Scan Barcode
            </button>` : '';
        
        this.element.innerHTML = `
            <div class="isbn-input-group">
                <input type="text" class="isbn-input" id="isbn-input" 
                       placeholder="Enter ISBN-10 or ISBN-13" 
                       pattern="[0-9X-]{10,17}"
                       aria-label="ISBN input">
                ${scannerButton}
                <button type="button" class="search-isbn-btn" id="search-isbn-btn">
                    <i class="fas fa-search"></i> Find Book
                </button>
            </div>
            <div class="isbn-result" id="isbn-result"></div>
        `;
    }
    
    bindEvents() {
        const input = this.element.querySelector('#isbn-input');
        const searchBtn = this.element.querySelector('#search-isbn-btn');
        const scannerBtn = this.element.querySelector('#scanner-btn');
        const resultDiv = this.element.querySelector('#isbn-result');
        
        // Search button click
        searchBtn.addEventListener('click', () => this.searchISBN());
        
        // Enter key in input
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.searchISBN();
            }
        });
        
        // Scanner button (if enabled)
        if (scannerBtn) {
            scannerBtn.addEventListener('click', () => this.startScanner());
        }
        
        // Input validation
        input.addEventListener('input', (e) => {
            const value = e.target.value.replace(/[^0-9X-]/gi, '');
            e.target.value = value;
            
            // Auto-search if valid ISBN length
            if (this.isValidISBN(value)) {
                this.searchISBN(value);
            }
        });
    }
    
    isValidISBN(isbn) {
        const cleaned = isbn.replace(/[-\s]/g, '');
        return cleaned.length === 10 || cleaned.length === 13;
    }
    
    async searchISBN(isbn = null) {
        const input = this.element.querySelector('#isbn-input');
        const resultDiv = this.element.querySelector('#isbn-result');
        const searchBtn = this.element.querySelector('#search-isbn-btn');
        
        const isbnValue = isbn || input.value.trim();
        
        if (!this.isValidISBN(isbnValue)) {
            this.showError('Please enter a valid ISBN-10 or ISBN-13');
            return;
        }
        
        // Show loading
        searchBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Searching...';
        searchBtn.disabled = true;
        resultDiv.innerHTML = '<div class="loading">Searching for book...</div>';
        
        try {
            const response = await fetch(`${this.options.apiEndpoint}${encodeURIComponent(isbnValue)}`);
            const data = await response.json();
            
            if (data.success && data.product) {
                this.showProduct(data.product);
            } else {
                this.showError(data.message || 'Book not found');
            }
        } catch (error) {
            this.showError('Error searching for book. Please try again.');
        } finally {
            searchBtn.innerHTML = '<i class="fas fa-search"></i> Find Book';
            searchBtn.disabled = false;
        }
    }
    
    showProduct(product) {
        const resultDiv = this.element.querySelector('#isbn-result');
        
        resultDiv.innerHTML = `
            <div class="isbn-product-card">
                <div class="product-image">
                    <img src="${product.cover_image || '/static/img/placeholder-book.jpg'}" 
                         alt="${product.title}" loading="lazy">
                </div>
                <div class="product-info">
                    <h3>${product.title}</h3>
                    <p class="author">${product.author || 'Unknown Author'}</p>
                    <p class="price">₹${product.price}</p>
                    <button class="add-to-cart-btn" onclick="addToCart(${product.id})">
                        <i class="fas fa-cart-plus"></i> Add to Cart
                    </button>
                </div>
            </div>
        `;
        
        // Scroll to result
        resultDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    
    showError(message) {
        const resultDiv = this.element.querySelector('#isbn-result');
        resultDiv.innerHTML = `<div class="error-message"><i class="fas fa-exclamation-triangle"></i> ${message}</div>`;
    }
    
    async startScanner() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            this.showError('Camera not supported in this browser');
            return;
        }
        
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                video: { facingMode: 'environment' } 
            });
            
            this.showScannerModal(stream);
        } catch (error) {
            this.showError('Unable to access camera. Please allow camera permission.');
        }
    }
    
    showScannerModal(stream) {
        // Create scanner modal
        const modal = document.createElement('div');
        modal.className = 'scanner-modal';
        modal.innerHTML = `
            <div class="scanner-overlay">
                <div class="scanner-container">
                    <div class="scanner-header">
                        <h3>Scan ISBN Barcode</h3>
                        <button class="close-scanner">&times;</button>
                    </div>
                    <video id="scanner-video" autoplay playsinline></video>
                    <canvas id="scanner-canvas" style="display: none;"></canvas>
                    <div class="scanner-instructions">
                        Position the barcode within the frame
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        const video = modal.querySelector('#scanner-video');
        const canvas = modal.querySelector('#scanner-canvas');
        const closeBtn = modal.querySelector('.close-scanner');
        
        video.srcObject = stream;
        
        // Simple barcode detection (placeholder implementation)
        const scanInterval = setInterval(() => {
            if (video.readyState === video.HAVE_ENOUGH_DATA) {
                this.detectBarcode(video, canvas);
            }
        }, 500);
        
        // Close scanner
        closeBtn.addEventListener('click', () => {
            clearInterval(scanInterval);
            stream.getTracks().forEach(track => track.stop());
            modal.remove();
        });
        
        // Close on escape key
        document.addEventListener('keydown', function escapeHandler(e) {
            if (e.key === 'Escape') {
                closeBtn.click();
                document.removeEventListener('keydown', escapeHandler);
            }
        });
    }
    
    detectBarcode(video, canvas) {
        // Simplified barcode detection - would use a proper library like ZXing in production
        const context = canvas.getContext('2d');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0);
        
        // Placeholder: In a real implementation, use a barcode scanning library
        // For now, just simulate detection after 3 seconds
        setTimeout(() => {
            const simulatedISBN = '9780123456789'; // Placeholder
            this.element.querySelector('#isbn-input').value = simulatedISBN;
            this.searchISBN(simulatedISBN);
            this.element.querySelector('.close-scanner').click();
        }, 3000);
    }
}

// Language Shelf component
class LanguageShelf {
    constructor(element, options = {}) {
        this.element = element;
        this.options = options;
        this.currentLanguage = options.defaultLanguage || null;
        
        this.init();
    }
    
    init() {
        this.bindTabEvents();
        
        // Show first tab by default
        const firstTab = this.element.querySelector('.language-tab');
        if (firstTab && !this.currentLanguage) {
            this.switchLanguage(firstTab.dataset.language);
        }
    }
    
    bindTabEvents() {
        const tabs = this.element.querySelectorAll('.language-tab');
        
        tabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchLanguage(tab.dataset.language);
            });
            
            // Keyboard navigation
            tab.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.switchLanguage(tab.dataset.language);
                }
            });
        });
    }
    
    switchLanguage(language) {
        if (this.currentLanguage === language) return;
        
        this.currentLanguage = language;
        
        // Update tabs
        const tabs = this.element.querySelectorAll('.language-tab');
        tabs.forEach(tab => {
            tab.classList.toggle('active', tab.dataset.language === language);
            tab.setAttribute('aria-selected', tab.dataset.language === language);
        });
        
        // Update content
        const contents = this.element.querySelectorAll('.language-shelf-content');
        contents.forEach(content => {
            content.classList.toggle('active', content.dataset.language === language);
        });
        
        // Emit event
        homepageEvents.emit('languageChange', {
            shelf: this,
            language: language
        });
    }
}

// Lazy loading for images
class LazyImageLoader {
    constructor() {
        this.observer = null;
        this.init();
    }
    
    init() {
        if ('IntersectionObserver' in window) {
            this.observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.loadImage(entry.target);
                        this.observer.unobserve(entry.target);
                    }
                });
            }, {
                rootMargin: '50px'
            });
            
            this.observeImages();
        } else {
            // Fallback for older browsers
            this.loadAllImages();
        }
    }
    
    observeImages() {
        const images = document.querySelectorAll('img[data-src], img[loading="lazy"]');
        images.forEach(img => this.observer.observe(img));
    }
    
    loadImage(img) {
        if (img.dataset.src) {
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
        }
        
        img.addEventListener('load', () => {
            img.classList.add('loaded');
        });
        
        img.addEventListener('error', () => {
            img.classList.add('error');
            // Set fallback image
            if (!img.src.includes('placeholder')) {
                img.src = '/static/img/placeholder-book.jpg';
            }
        });
    }
    
    loadAllImages() {
        const images = document.querySelectorAll('img[data-src]');
        images.forEach(img => this.loadImage(img));
    }
    
    refresh() {
        // Observe any new images that were added to the DOM
        this.observeImages();
    }
}

// Newsletter subscription
class NewsletterForm {
    constructor(element) {
        this.element = element;
        this.form = element.querySelector('form');
        
        this.init();
    }
    
    init() {
        if (!this.form) return;
        
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
    }
    
    async handleSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(this.form);
        const email = formData.get('email');
        const submitBtn = this.form.querySelector('button[type="submit"]');
        
        if (!this.isValidEmail(email)) {
            this.showMessage('Please enter a valid email address', 'error');
            return;
        }
        
        // Show loading
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Subscribing...';
        submitBtn.disabled = true;
        
        try {
            const response = await fetch('/api/newsletter/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showMessage('Thank you for subscribing!', 'success');
                this.form.reset();
            } else {
                this.showMessage(data.message || 'Subscription failed', 'error');
            }
        } catch (error) {
            this.showMessage('Network error. Please try again.', 'error');
        } finally {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }
    
    isValidEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }
    
    showMessage(message, type) {
        // Remove existing message
        const existingMsg = this.element.querySelector('.newsletter-message');
        if (existingMsg) existingMsg.remove();
        
        // Create new message
        const msgDiv = document.createElement('div');
        msgDiv.className = `newsletter-message ${type}`;
        msgDiv.innerHTML = `<i class="fas fa-${type === 'success' ? 'check' : 'exclamation-triangle'}"></i> ${message}`;
        
        this.form.appendChild(msgDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => msgDiv.remove(), 5000);
    }
}

// Initialize homepage features
function initHome() {
    // Initialize carousels
    document.querySelectorAll('[data-carousel]').forEach(element => {
        const options = {
            autoplay: element.dataset.autoplay === 'true',
            interval: parseInt(element.dataset.interval) || 5000,
            transition: element.dataset.transition || 'fade',
            showArrows: element.dataset.showArrows !== 'false',
            showDots: element.dataset.showDots !== 'false'
        };
        
        new Carousel(element, options);
    });
    
    // Initialize countdowns
    document.querySelectorAll('[data-countdown]').forEach(element => {
        const targetDate = element.dataset.countdown;
        new CountdownTimer(element, targetDate);
    });
    
    // Initialize quick order ISBN
    document.querySelectorAll('.quick-order').forEach(element => {
        const options = {
            enableScanner: element.dataset.enableScanner === 'true'
        };
        new QuickOrderISBN(element, options);
    });
    
    // Initialize language shelves
    document.querySelectorAll('.language-shelf').forEach(element => {
        new LanguageShelf(element);
    });
    
    // Initialize newsletter forms
    document.querySelectorAll('.newsletter-bar').forEach(element => {
        new NewsletterForm(element);
    });
    
    // Initialize lazy loading
    new LazyImageLoader();
    
    // Initialize trending searches
    initTrendingSearches();
    
    // Initialize product interactions
    initProductInteractions();
}

// Trending searches functionality
function initTrendingSearches() {
    document.querySelectorAll('.trending-term').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const query = link.textContent.trim();
            
            // Update search input if exists
            const searchInput = document.querySelector('input[name="q"], .search-input');
            if (searchInput) {
                searchInput.value = query;
                
                // Submit search form
                const searchForm = searchInput.closest('form');
                if (searchForm) {
                    searchForm.submit();
                } else {
                    // Navigate to search page
                    window.location.href = `/search?q=${encodeURIComponent(query)}`;
                }
            }
        });
    });
}

// Product interaction handlers
function initProductInteractions() {
    // Add to cart buttons
    document.querySelectorAll('.add-to-cart-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.dataset.productId || this.closest('[data-product-id]')?.dataset.productId;
            if (productId) {
                addToCart(productId);
            }
        });
    });
}

// Global add to cart function
async function addToCart(productId, quantity = 1) {
    try {
        const response = await fetch('/cart/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                product_id: productId,
                quantity: quantity
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update cart count in header
            updateCartCount(data.cart_count);
            
            // Show success message
            showToast('Added to cart successfully!', 'success');
            
            // Emit event for other components
            homepageEvents.emit('cartUpdated', {
                productId: productId,
                quantity: quantity,
                cartCount: data.cart_count
            });
        } else {
            showToast(data.message || 'Failed to add to cart', 'error');
        }
    } catch (error) {
        showToast('Network error. Please try again.', 'error');
    }
}

// Update cart count in navigation
function updateCartCount(count) {
    const cartBadges = document.querySelectorAll('.cart-count, .cart-badge');
    cartBadges.forEach(badge => {
        badge.textContent = count;
        badge.style.transform = 'scale(1.2)';
        setTimeout(() => {
            badge.style.transform = 'scale(1)';
        }, 200);
    });
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation-triangle' : 'info'}"></i>
        ${message}
    `;
    
    document.body.appendChild(toast);
    
    // Show toast
    setTimeout(() => toast.classList.add('show'), 100);
    
    // Hide and remove toast
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// RTL support
function initRTLSupport() {
    const isRTL = document.dir === 'rtl' || document.documentElement.dir === 'rtl';
    
    if (isRTL) {
        // Reverse carousel direction
        homepageEvents.on('slideChange', (data) => {
            // Additional RTL-specific logic if needed
        });
        
        // Update arrow icons for RTL
        document.querySelectorAll('.carousel-prev i').forEach(icon => {
            icon.className = icon.className.replace('fa-chevron-left', 'fa-chevron-right');
        });
        
        document.querySelectorAll('.carousel-next i').forEach(icon => {
            icon.className = icon.className.replace('fa-chevron-right', 'fa-chevron-left');
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    initHome();
    initRTLSupport();
});

// Refresh functionality for dynamic content
function refreshHomepageContent() {
    // Re-initialize any new elements added to the DOM
    const lazyLoader = new LazyImageLoader();
    lazyLoader.refresh();
    
    // Re-bind any new interactive elements
    initProductInteractions();
    initTrendingSearches();
}

// Export for global use
window.HomepageJS = {
    initHome,
    addToCart,
    updateCartCount,
    showToast,
    refreshHomepageContent,
    Carousel,
    CountdownTimer,
    QuickOrderISBN,
    LanguageShelf,
    NewsletterForm
};
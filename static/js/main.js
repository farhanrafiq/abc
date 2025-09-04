// Main JavaScript for ABC Publishing Kashmir

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeSearch();
    initializeCartCounter();
    initializeToasts();
    initializeScrollEffects();
    initializeImageLazyLoading();
    initializeQuantityControls();
    initializePriceFormatting();
    initializeFormValidation();
    initializeHeroSlider();
});

// Hero Slider functionality
function initializeHeroSlider() {
    const heroSlider = document.querySelector('.simple-hero-slider');
    if (!heroSlider) return;
    
    const slides = heroSlider.querySelectorAll('.hero-slide-link');
    const dots = heroSlider.querySelectorAll('.hero-dot');
    let currentSlide = 0;
    let slideInterval;
    
    if (slides.length <= 1) return;
    
    // Auto-play functionality
    const autoplay = heroSlider.dataset.autoplay === 'true';
    const interval = parseInt(heroSlider.dataset.interval) || 5000;
    
    function showSlide(index) {
        // Remove active class from all slides and dots
        slides.forEach(slide => slide.classList.remove('active'));
        dots.forEach(dot => dot.classList.remove('active'));
        
        // Add active class to current slide and dot
        slides[index].classList.add('active');
        if (dots[index]) dots[index].classList.add('active');
        
        currentSlide = index;
    }
    
    function nextSlide() {
        const next = (currentSlide + 1) % slides.length;
        showSlide(next);
    }
    
    function startAutoplay() {
        if (autoplay) {
            slideInterval = setInterval(nextSlide, interval);
        }
    }
    
    function stopAutoplay() {
        if (slideInterval) {
            clearInterval(slideInterval);
            slideInterval = null;
        }
    }
    
    // Dot navigation
    dots.forEach((dot, index) => {
        dot.addEventListener('click', () => {
            showSlide(index);
            stopAutoplay();
            startAutoplay(); // Restart autoplay
        });
    });
    
    // Pause on hover
    heroSlider.addEventListener('mouseenter', stopAutoplay);
    heroSlider.addEventListener('mouseleave', startAutoplay);
    
    // Start autoplay
    startAutoplay();
}

// Search functionality
function initializeSearch() {
    const searchInput = document.querySelector('#search-input');
    const searchForm = document.querySelector('#search-form');
    
    if (searchInput) {
        let searchTimeout;
        
        // Debounced search suggestions
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length >= 2) {
                searchTimeout = setTimeout(() => {
                    fetchSearchSuggestions(query);
                }, 300);
            } else {
                hideSearchSuggestions();
            }
        });
        
        // Close suggestions when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.search-container')) {
                hideSearchSuggestions();
            }
        });
    }
}

function fetchSearchSuggestions(query) {
    fetch(`/api/search-suggestions?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            if (data.suggestions && data.suggestions.length > 0) {
                displaySearchSuggestions(data.suggestions);
            } else {
                hideSearchSuggestions();
            }
        })
        .catch(error => {
            console.error('Search suggestions error:', error);
            hideSearchSuggestions();
        });
}

function displaySearchSuggestions(suggestions) {
    let suggestionsContainer = document.querySelector('#search-suggestions');
    
    if (!suggestionsContainer) {
        suggestionsContainer = document.createElement('div');
        suggestionsContainer.id = 'search-suggestions';
        suggestionsContainer.className = 'search-suggestions';
        document.querySelector('.search-container').appendChild(suggestionsContainer);
    }
    
    suggestionsContainer.innerHTML = suggestions.map(suggestion => 
        `<div class="search-suggestion-item" data-query="${suggestion.query}">
            <i class="fas fa-search"></i>
            <span>${suggestion.text}</span>
        </div>`
    ).join('');
    
    suggestionsContainer.style.display = 'block';
    
    // Add click handlers
    suggestionsContainer.querySelectorAll('.search-suggestion-item').forEach(item => {
        item.addEventListener('click', function() {
            const query = this.dataset.query;
            document.querySelector('#search-input').value = query;
            document.querySelector('#search-form').submit();
        });
    });
}

function hideSearchSuggestions() {
    const suggestionsContainer = document.querySelector('#search-suggestions');
    if (suggestionsContainer) {
        suggestionsContainer.style.display = 'none';
    }
}

// Cart counter functionality
function initializeCartCounter() {
    updateCartCounter();
    
    // Update cart counter after any cart action
    document.addEventListener('cartUpdated', function() {
        updateCartCounter();
    });
}

function updateCartCounter() {
    fetch('/cart/api/count')
        .then(response => response.json())
        .then(data => {
            const counters = document.querySelectorAll('.cart-counter');
            counters.forEach(counter => {
                counter.textContent = data.count;
                counter.style.display = data.count > 0 ? 'inline' : 'none';
            });
        })
        .catch(error => console.error('Cart counter error:', error));
}

// Toast notifications
function initializeToasts() {
    // Auto-hide toasts after 5 seconds
    const toasts = document.querySelectorAll('.toast');
    toasts.forEach(toast => {
        setTimeout(() => {
            hideToast(toast);
        }, 5000);
    });
    
    // Toast close buttons
    document.querySelectorAll('.toast-close').forEach(button => {
        button.addEventListener('click', function() {
            hideToast(this.closest('.toast'));
        });
    });
}

function showToast(message, type = 'info') {
    const toastContainer = getOrCreateToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type} slide-up`;
    toast.innerHTML = `
        <div class="toast-content">
            <i class="fas fa-${getToastIcon(type)}"></i>
            <span>${message}</span>
            <button class="toast-close" type="button">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        hideToast(toast);
    }, 5000);
    
    // Add close button handler
    toast.querySelector('.toast-close').addEventListener('click', function() {
        hideToast(toast);
    });
}

function hideToast(toast) {
    toast.style.animation = 'slideDown 0.3s ease-out forwards';
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 300);
}

function getOrCreateToastContainer() {
    let container = document.querySelector('#toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    return container;
}

function getToastIcon(type) {
    const icons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// Scroll effects
function initializeScrollEffects() {
    const navbar = document.querySelector('.navbar');
    const backToTopBtn = document.querySelector('#back-to-top');
    
    window.addEventListener('scroll', function() {
        const scrollY = window.scrollY;
        
        // Navbar background on scroll
        if (navbar) {
            if (scrollY > 100) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        }
        
        // Back to top button
        if (backToTopBtn) {
            if (scrollY > 500) {
                backToTopBtn.style.display = 'block';
            } else {
                backToTopBtn.style.display = 'none';
            }
        }
    });
    
    // Smooth scroll for back to top
    if (backToTopBtn) {
        backToTopBtn.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
    
    // Parallax effect for hero section
    const heroSection = document.querySelector('.hero-section');
    if (heroSection) {
        window.addEventListener('scroll', function() {
            const scrolled = window.pageYOffset;
            const rate = scrolled * -0.5;
            heroSection.style.transform = `translateY(${rate}px)`;
        });
    }
}

// Lazy loading for images
function initializeImageLazyLoading() {
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    } else {
        // Fallback for browsers without IntersectionObserver
        document.querySelectorAll('img[data-src]').forEach(img => {
            img.src = img.dataset.src;
            img.classList.remove('lazy');
        });
    }
}

// Quantity controls
function initializeQuantityControls() {
    document.querySelectorAll('.quantity-controls').forEach(controls => {
        const decreaseBtn = controls.querySelector('.quantity-decrease');
        const increaseBtn = controls.querySelector('.quantity-increase');
        const input = controls.querySelector('.quantity-input');
        
        if (decreaseBtn && increaseBtn && input) {
            decreaseBtn.addEventListener('click', function() {
                const currentValue = parseInt(input.value) || 1;
                if (currentValue > 1) {
                    input.value = currentValue - 1;
                    input.dispatchEvent(new Event('change'));
                }
            });
            
            increaseBtn.addEventListener('click', function() {
                const currentValue = parseInt(input.value) || 1;
                const maxValue = parseInt(input.getAttribute('max')) || 999;
                if (currentValue < maxValue) {
                    input.value = currentValue + 1;
                    input.dispatchEvent(new Event('change'));
                }
            });
            
            input.addEventListener('input', function() {
                const value = parseInt(this.value);
                const min = parseInt(this.getAttribute('min')) || 1;
                const max = parseInt(this.getAttribute('max')) || 999;
                
                if (isNaN(value) || value < min) {
                    this.value = min;
                } else if (value > max) {
                    this.value = max;
                }
            });
        }
    });
}

// Price formatting
function initializePriceFormatting() {
    document.querySelectorAll('[data-price]').forEach(element => {
        const price = parseFloat(element.dataset.price);
        if (!isNaN(price)) {
            element.textContent = formatCurrency(price);
        }
    });
}

function formatCurrency(amount, currency = 'INR') {
    if (currency === 'INR') {
        return `₹${amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
    return `${currency} ${amount.toFixed(2)}`;
}

// Form validation
function initializeFormValidation() {
    document.querySelectorAll('form[data-validate]').forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                return false;
            }
        });
        
        // Real-time validation
        form.querySelectorAll('input, textarea, select').forEach(field => {
            field.addEventListener('blur', function() {
                validateField(this);
            });
        });
    });
}

function validateForm(form) {
    let isValid = true;
    const fields = form.querySelectorAll('input[required], textarea[required], select[required]');
    
    fields.forEach(field => {
        if (!validateField(field)) {
            isValid = false;
        }
    });
    
    return isValid;
}

function validateField(field) {
    const value = field.value.trim();
    const type = field.type;
    let isValid = true;
    let message = '';
    
    // Required validation
    if (field.hasAttribute('required') && !value) {
        isValid = false;
        message = 'This field is required.';
    }
    
    // Email validation
    else if (type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            isValid = false;
            message = 'Please enter a valid email address.';
        }
    }
    
    // Phone validation
    else if (field.name === 'phone' && value) {
        const phoneRegex = /^[+]?[\d\s\-\(\)]{10,}$/;
        if (!phoneRegex.test(value)) {
            isValid = false;
            message = 'Please enter a valid phone number.';
        }
    }
    
    // Password validation
    else if (type === 'password' && value) {
        if (value.length < 6) {
            isValid = false;
            message = 'Password must be at least 6 characters long.';
        }
    }
    
    // PIN code validation
    else if (field.name === 'pincode' && value) {
        const pincodeRegex = /^\d{6}$/;
        if (!pincodeRegex.test(value)) {
            isValid = false;
            message = 'Please enter a valid 6-digit PIN code.';
        }
    }
    
    // Display validation result
    displayFieldValidation(field, isValid, message);
    
    return isValid;
}

function displayFieldValidation(field, isValid, message) {
    // Remove existing validation classes
    field.classList.remove('is-valid', 'is-invalid');
    
    // Remove existing feedback
    const existingFeedback = field.parentNode.querySelector('.invalid-feedback, .valid-feedback');
    if (existingFeedback) {
        existingFeedback.remove();
    }
    
    if (!isValid && message) {
        field.classList.add('is-invalid');
        
        const feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        feedback.textContent = message;
        field.parentNode.appendChild(feedback);
    } else if (field.value.trim()) {
        field.classList.add('is-valid');
    }
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// AJAX helpers
function ajaxRequest(url, options = {}) {
    const defaults = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    };
    
    const config = { ...defaults, ...options };
    
    return fetch(url, config)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        });
}

// Export functions for use in other scripts
window.ABCPublishing = {
    showToast,
    hideToast,
    formatCurrency,
    updateCartCounter,
    validateForm,
    validateField,
    ajaxRequest,
    debounce,
    throttle
};

// Custom events
document.addEventListener('productAdded', function(e) {
    showToast(`${e.detail.productName} added to cart!`, 'success');
    updateCartCounter();
});

document.addEventListener('productRemoved', function(e) {
    showToast(`${e.detail.productName} removed from cart.`, 'info');
    updateCartCounter();
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K for search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('#search-input');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Escape to close modals/suggestions
    if (e.key === 'Escape') {
        hideSearchSuggestions();
        
        // Close any open modals
        const openModals = document.querySelectorAll('.modal.show');
        openModals.forEach(modal => {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                modalInstance.hide();
            }
        });
    }
});

// Service Worker registration for PWA
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/static/js/sw.js')
            .then(function(registration) {
                console.log('ServiceWorker registration successful');
            })
            .catch(function(err) {
                console.log('ServiceWorker registration failed: ', err);
            });
    });
}

// Performance monitoring
window.addEventListener('load', function() {
    // Log page load time
    const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
    console.log('Page load time:', loadTime + 'ms');
    
    // Send performance data (in production, send to analytics)
    if (loadTime > 3000) {
        console.warn('Slow page load detected:', loadTime + 'ms');
    }
});

// Cart-specific JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    initializeCartFunctionality();
    initializeCouponValidation();
    initializeCheckoutForm();
    initializeAddToCartButtons();
});

// Initialize cart functionality
function initializeCartFunctionality() {
    // Update cart item quantities
    document.querySelectorAll('.cart-quantity-input').forEach(input => {
        input.addEventListener('change', function() {
            updateCartItemQuantity(this);
        });
    });
    
    // Remove cart items
    document.querySelectorAll('.remove-cart-item').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            removeCartItem(this);
        });
    });
    
    // Clear entire cart
    const clearCartBtn = document.querySelector('#clear-cart-btn');
    if (clearCartBtn) {
        clearCartBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (confirm('Are you sure you want to clear your cart?')) {
                clearCart();
            }
        });
    }
    
    // Quick add to cart from catalog
    document.querySelectorAll('.quick-add-to-cart').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            quickAddToCart(this);
        });
    });
}

// Update cart item quantity
function updateCartItemQuantity(input) {
    const itemId = input.dataset.itemId;
    const quantity = parseInt(input.value);
    const originalQuantity = parseInt(input.dataset.originalQuantity);
    
    if (quantity === originalQuantity) {
        return; // No change
    }
    
    if (quantity <= 0) {
        if (confirm('Remove this item from cart?')) {
            removeCartItemById(itemId);
        } else {
            input.value = originalQuantity;
        }
        return;
    }
    
    // Show loading state
    input.disabled = true;
    const loadingSpinner = input.parentNode.querySelector('.loading-spinner');
    if (loadingSpinner) {
        loadingSpinner.style.display = 'inline-block';
    }
    
    // Update via AJAX
    fetch(`/cart/update/${itemId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: `quantity=${quantity}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update the original quantity
            input.dataset.originalQuantity = quantity;
            
            // Update line total
            const lineTotal = input.closest('.cart-item').querySelector('.line-total');
            if (lineTotal && data.line_total) {
                lineTotal.textContent = data.line_total;
            }
            
            // Update cart totals
            updateCartTotals();
            
            // Show success message
            ABCPublishing.showToast('Cart updated successfully', 'success');
        } else {
            // Revert quantity on error
            input.value = originalQuantity;
            ABCPublishing.showToast(data.message || 'Failed to update cart', 'error');
        }
    })
    .catch(error => {
        console.error('Cart update error:', error);
        input.value = originalQuantity;
        ABCPublishing.showToast('Failed to update cart', 'error');
    })
    .finally(() => {
        // Hide loading state
        input.disabled = false;
        if (loadingSpinner) {
            loadingSpinner.style.display = 'none';
        }
    });
}

// Remove cart item
function removeCartItem(button) {
    const cartItem = button.closest('.cart-item');
    const itemId = button.dataset.itemId;
    const productName = cartItem.querySelector('.product-title').textContent;
    
    if (!confirm(`Remove "${productName}" from cart?`)) {
        return;
    }
    
    removeCartItemById(itemId, cartItem);
}

function removeCartItemById(itemId, cartItemElement = null) {
    // Find cart item element if not provided
    if (!cartItemElement) {
        cartItemElement = document.querySelector(`[data-item-id="${itemId}"]`).closest('.cart-item');
    }
    
    // Show loading state
    cartItemElement.style.opacity = '0.5';
    cartItemElement.style.pointerEvents = 'none';
    
    fetch(`/cart/remove/${itemId}`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (response.ok) {
            // Animate removal
            cartItemElement.style.animation = 'slideUp 0.3s ease-out forwards';
            setTimeout(() => {
                cartItemElement.remove();
                updateCartTotals();
                
                // Check if cart is empty
                if (document.querySelectorAll('.cart-item').length === 0) {
                    showEmptyCartMessage();
                }
            }, 300);
            
            ABCPublishing.showToast('Item removed from cart', 'info');
        } else {
            // Revert loading state
            cartItemElement.style.opacity = '1';
            cartItemElement.style.pointerEvents = 'auto';
            ABCPublishing.showToast('Failed to remove item', 'error');
        }
    })
    .catch(error => {
        console.error('Remove item error:', error);
        cartItemElement.style.opacity = '1';
        cartItemElement.style.pointerEvents = 'auto';
        ABCPublishing.showToast('Failed to remove item', 'error');
    });
}

// Clear entire cart
function clearCart() {
    const cartContainer = document.querySelector('.cart-items-container');
    
    fetch('/cart/clear', {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (response.ok) {
            cartContainer.innerHTML = '';
            showEmptyCartMessage();
            updateCartTotals();
            ABCPublishing.showToast('Cart cleared', 'info');
        } else {
            ABCPublishing.showToast('Failed to clear cart', 'error');
        }
    })
    .catch(error => {
        console.error('Clear cart error:', error);
        ABCPublishing.showToast('Failed to clear cart', 'error');
    });
}

// Show empty cart message
function showEmptyCartMessage() {
    const cartContainer = document.querySelector('.cart-items-container');
    cartContainer.innerHTML = `
        <div class="empty-cart-message text-center py-5">
            <i class="fas fa-shopping-cart fa-3x text-muted mb-3"></i>
            <h4>Your cart is empty</h4>
            <p class="text-muted">Start shopping to add items to your cart.</p>
            <a href="/catalog" class="btn btn-brand-primary">
                <i class="fas fa-book"></i> Browse Books
            </a>
        </div>
    `;
    
    // Hide checkout section
    const checkoutSection = document.querySelector('.cart-summary');
    if (checkoutSection) {
        checkoutSection.style.display = 'none';
    }
}

// Update cart totals
function updateCartTotals() {
    fetch('/cart/api/totals', {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        // Update subtotal
        const subtotalElement = document.querySelector('#cart-subtotal');
        if (subtotalElement && data.subtotal !== undefined) {
            subtotalElement.textContent = ABCPublishing.formatCurrency(data.subtotal / 100);
        }
        
        // Update shipping
        const shippingElement = document.querySelector('#cart-shipping');
        if (shippingElement && data.shipping !== undefined) {
            shippingElement.textContent = data.shipping > 0 ? 
                ABCPublishing.formatCurrency(data.shipping / 100) : 'Free';
        }
        
        // Update total
        const totalElement = document.querySelector('#cart-total');
        if (totalElement && data.total !== undefined) {
            totalElement.textContent = ABCPublishing.formatCurrency(data.total / 100);
        }
        
        // Update cart counter
        ABCPublishing.updateCartCounter();
    })
    .catch(error => {
        console.error('Update totals error:', error);
    });
}

// Coupon validation
function initializeCouponValidation() {
    const couponForm = document.querySelector('#coupon-form');
    const couponInput = document.querySelector('#coupon-code');
    const applyCouponBtn = document.querySelector('#apply-coupon-btn');
    
    if (couponForm && couponInput && applyCouponBtn) {
        couponForm.addEventListener('submit', function(e) {
            e.preventDefault();
            applyCoupon();
        });
        
        // Real-time validation
        couponInput.addEventListener('input', function() {
            const code = this.value.trim().toUpperCase();
            this.value = code;
            
            if (code.length >= 3) {
                validateCouponCode(code);
            } else {
                clearCouponValidation();
            }
        });
    }
}

function applyCoupon() {
    const couponInput = document.querySelector('#coupon-code');
    const applyCouponBtn = document.querySelector('#apply-coupon-btn');
    const code = couponInput.value.trim().toUpperCase();
    
    if (!code) {
        ABCPublishing.showToast('Please enter a coupon code', 'warning');
        return;
    }
    
    // Show loading state
    applyCouponBtn.disabled = true;
    applyCouponBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Applying...';
    
    const subtotal = getCartSubtotal();
    
    fetch('/cart/api/validate-coupon', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            code: code,
            subtotal: subtotal
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.valid) {
            // Apply discount to totals
            applyCouponDiscount(data.discount, code);
            ABCPublishing.showToast(data.message || 'Coupon applied successfully!', 'success');
            
            // Hide coupon form and show applied coupon
            showAppliedCoupon(code, data.discount);
        } else {
            ABCPublishing.showToast(data.message || 'Invalid coupon code', 'error');
            couponInput.classList.add('is-invalid');
        }
    })
    .catch(error => {
        console.error('Coupon validation error:', error);
        ABCPublishing.showToast('Failed to apply coupon', 'error');
    })
    .finally(() => {
        // Reset button state
        applyCouponBtn.disabled = false;
        applyCouponBtn.innerHTML = 'Apply';
    });
}

function validateCouponCode(code) {
    const couponInput = document.querySelector('#coupon-code');
    const subtotal = getCartSubtotal();
    
    ABCPublishing.debounce(() => {
        fetch('/cart/api/validate-coupon', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                code: code,
                subtotal: subtotal,
                preview: true
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.valid) {
                couponInput.classList.remove('is-invalid');
                couponInput.classList.add('is-valid');
                showCouponPreview(data.discount);
            } else {
                couponInput.classList.remove('is-valid');
                couponInput.classList.add('is-invalid');
                clearCouponPreview();
            }
        })
        .catch(error => {
            console.error('Coupon preview error:', error);
        });
    }, 500)();
}

function showCouponPreview(discount) {
    let previewElement = document.querySelector('#coupon-preview');
    if (!previewElement) {
        previewElement = document.createElement('div');
        previewElement.id = 'coupon-preview';
        previewElement.className = 'coupon-preview mt-2 p-2 bg-success text-white rounded';
        document.querySelector('#coupon-form').appendChild(previewElement);
    }
    
    previewElement.innerHTML = `
        <i class="fas fa-check-circle"></i>
        You will save ${ABCPublishing.formatCurrency(discount / 100)}
    `;
    previewElement.style.display = 'block';
}

function clearCouponPreview() {
    const previewElement = document.querySelector('#coupon-preview');
    if (previewElement) {
        previewElement.style.display = 'none';
    }
}

function clearCouponValidation() {
    const couponInput = document.querySelector('#coupon-code');
    couponInput.classList.remove('is-valid', 'is-invalid');
    clearCouponPreview();
}

function applyCouponDiscount(discount, code) {
    // Update discount row in cart totals
    let discountRow = document.querySelector('#cart-discount-row');
    if (!discountRow) {
        // Create discount row
        const cartTotals = document.querySelector('.cart-totals');
        const subtotalRow = cartTotals.querySelector('.subtotal-row');
        
        discountRow = document.createElement('div');
        discountRow.id = 'cart-discount-row';
        discountRow.className = 'discount-row d-flex justify-content-between py-2 border-bottom';
        discountRow.innerHTML = `
            <span>Discount (${code}):</span>
            <span id="cart-discount" class="text-success">-${ABCPublishing.formatCurrency(discount / 100)}</span>
        `;
        
        subtotalRow.insertAdjacentElement('afterend', discountRow);
    } else {
        // Update existing discount
        discountRow.querySelector('span:first-child').textContent = `Discount (${code}):`;
        discountRow.querySelector('#cart-discount').textContent = `-${ABCPublishing.formatCurrency(discount / 100)}`;
    }
    
    // Update grand total
    updateCartTotals();
}

function showAppliedCoupon(code, discount) {
    const couponForm = document.querySelector('#coupon-form');
    
    // Create applied coupon display
    const appliedCoupon = document.createElement('div');
    appliedCoupon.id = 'applied-coupon';
    appliedCoupon.className = 'applied-coupon alert alert-success d-flex justify-content-between align-items-center';
    appliedCoupon.innerHTML = `
        <div>
            <i class="fas fa-tag"></i>
            <strong>${code}</strong> applied
            <small class="d-block">You saved ${ABCPublishing.formatCurrency(discount / 100)}</small>
        </div>
        <button type="button" class="btn btn-sm btn-outline-success" onclick="removeCoupon()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    couponForm.style.display = 'none';
    couponForm.insertAdjacentElement('afterend', appliedCoupon);
}

function removeCoupon() {
    const appliedCoupon = document.querySelector('#applied-coupon');
    const couponForm = document.querySelector('#coupon-form');
    const discountRow = document.querySelector('#cart-discount-row');
    
    if (appliedCoupon) {
        appliedCoupon.remove();
    }
    
    if (discountRow) {
        discountRow.remove();
    }
    
    if (couponForm) {
        couponForm.style.display = 'block';
        couponForm.querySelector('#coupon-code').value = '';
        clearCouponValidation();
    }
    
    updateCartTotals();
    ABCPublishing.showToast('Coupon removed', 'info');
}

function getCartSubtotal() {
    const subtotalElement = document.querySelector('#cart-subtotal');
    if (subtotalElement) {
        const subtotalText = subtotalElement.textContent.replace(/[₹,]/g, '');
        return Math.round(parseFloat(subtotalText) * 100); // Convert to paisa
    }
    return 0;
}

// Checkout form functionality
function initializeCheckoutForm() {
    const checkoutForm = document.querySelector('#checkout-form');
    if (!checkoutForm) return;
    
    // Payment method change handler
    const paymentMethodInputs = checkoutForm.querySelectorAll('input[name="payment_method"]');
    paymentMethodInputs.forEach(input => {
        input.addEventListener('change', function() {
            togglePaymentMethodSections(this.value);
        });
    });
    
    // Address selection handlers
    const addressSelects = checkoutForm.querySelectorAll('select[name$="_address_id"]');
    addressSelects.forEach(select => {
        select.addEventListener('change', function() {
            handleAddressSelection(this);
        });
    });
    
    // Form submission
    checkoutForm.addEventListener('submit', function(e) {
        if (!validateCheckoutForm()) {
            e.preventDefault();
            return false;
        }
        
        // Show processing state
        const submitBtn = this.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    });
}

function togglePaymentMethodSections(paymentMethod) {
    const razorpaySection = document.querySelector('#razorpay-section');
    const codSection = document.querySelector('#cod-section');
    
    if (razorpaySection && codSection) {
        if (paymentMethod === 'razorpay') {
            razorpaySection.style.display = 'block';
            codSection.style.display = 'none';
        } else {
            razorpaySection.style.display = 'none';
            codSection.style.display = 'block';
        }
    }
}

function handleAddressSelection(select) {
    const addressId = select.value;
    const addressType = select.name.includes('billing') ? 'billing' : 'shipping';
    
    if (addressId) {
        // Fetch and display address details
        fetchAddressDetails(addressId, addressType);
    }
}

function fetchAddressDetails(addressId, type) {
    fetch(`/api/address/${addressId}`, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        const previewElement = document.querySelector(`#${type}-address-preview`);
        if (previewElement && data.address) {
            previewElement.innerHTML = formatAddressPreview(data.address);
            previewElement.style.display = 'block';
        }
    })
    .catch(error => {
        console.error('Address fetch error:', error);
    });
}

function formatAddressPreview(address) {
    return `
        <div class="address-preview p-3 border rounded">
            <strong>${address.name}</strong><br>
            ${address.line1}<br>
            ${address.line2 ? address.line2 + '<br>' : ''}
            ${address.city}, ${address.district}<br>
            ${address.state} - ${address.pincode}
        </div>
    `;
}

function validateCheckoutForm() {
    const form = document.querySelector('#checkout-form');
    let isValid = true;
    
    // Validate payment method
    const paymentMethod = form.querySelector('input[name="payment_method"]:checked');
    if (!paymentMethod) {
        ABCPublishing.showToast('Please select a payment method', 'warning');
        isValid = false;
    }
    
    // Validate addresses for logged-in users
    const billingAddress = form.querySelector('select[name="billing_address_id"]');
    if (billingAddress && !billingAddress.value) {
        ABCPublishing.showToast('Please select a billing address', 'warning');
        isValid = false;
    }
    
    // Validate guest user details
    const guestEmail = form.querySelector('input[name="guest_email"]');
    if (guestEmail && guestEmail.style.display !== 'none' && !guestEmail.value) {
        ABCPublishing.showToast('Please enter your email address', 'warning');
        isValid = false;
    }
    
    return isValid;
}

// Add to cart buttons
function initializeAddToCartButtons() {
    document.querySelectorAll('.add-to-cart-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            addToCart(this);
        });
    });
}

function addToCart(button) {
    const productId = button.dataset.productId;
    const quantityInput = button.closest('form').querySelector('input[name="quantity"]');
    const quantity = quantityInput ? parseInt(quantityInput.value) || 1 : 1;
    
    // Show loading state
    const originalText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';
    
    fetch('/cart/api/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            ABCPublishing.showToast(data.message, 'success');
            
            // Update cart counter
            ABCPublishing.updateCartCounter();
            
            // Trigger custom event
            document.dispatchEvent(new CustomEvent('productAdded', {
                detail: { productId: productId, quantity: quantity }
            }));
            
            // Reset quantity to 1
            if (quantityInput) {
                quantityInput.value = 1;
            }
            
            // Show success animation
            button.classList.add('btn-success');
            button.innerHTML = '<i class="fas fa-check"></i> Added!';
            
            setTimeout(() => {
                button.classList.remove('btn-success');
                button.innerHTML = originalText;
            }, 2000);
        } else {
            ABCPublishing.showToast(data.message || 'Failed to add to cart', 'error');
        }
    })
    .catch(error => {
        console.error('Add to cart error:', error);
        ABCPublishing.showToast('Failed to add to cart', 'error');
    })
    .finally(() => {
        // Reset button state
        button.disabled = false;
        if (button.innerHTML.includes('Adding...')) {
            button.innerHTML = originalText;
        }
    });
}

function quickAddToCart(button) {
    const productId = button.dataset.productId;
    
    addToCartAjax(productId, 1)
        .then(data => {
            if (data.success) {
                // Show mini cart or redirect to cart
                if (window.innerWidth > 768) {
                    showMiniCartModal();
                } else {
                    // On mobile, show toast and update counter
                    ABCPublishing.showToast(data.message, 'success');
                }
            }
        });
}

function addToCartAjax(productId, quantity = 1) {
    return fetch('/cart/api/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            ABCPublishing.updateCartCounter();
        }
        return data;
    });
}

// Mini cart modal
function showMiniCartModal() {
    // Implementation for mini cart modal
    // This would show a small modal with cart contents
    console.log('Show mini cart modal');
}

// Expose functions globally
window.CartManager = {
    addToCart,
    removeCartItem,
    updateCartItemQuantity,
    applyCoupon,
    removeCoupon,
    updateCartTotals,
    validateCheckoutForm
};

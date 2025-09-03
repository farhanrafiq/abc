// Admin-specific JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    initializeAdminDashboard();
    initializeProductManagement();
    initializeOrderManagement();
    initializeDataTables();
    initializeBulkActions();
    initializeImageUpload();
    initializeInventoryManagement();
    initializeCouponManagement();
});

// Initialize admin dashboard
function initializeAdminDashboard() {
    // Initialize charts if Chart.js is available
    if (typeof Chart !== 'undefined') {
        initializeSalesChart();
        initializeCategoryChart();
    }
    
    // Auto-refresh dashboard stats
    if (document.querySelector('.dashboard')) {
        setInterval(refreshDashboardStats, 300000); // Refresh every 5 minutes
    }
    
    // Initialize real-time notifications
    initializeNotifications();
}

// Sales chart for dashboard
function initializeSalesChart() {
    const salesChartCanvas = document.querySelector('#salesChart');
    if (!salesChartCanvas) return;
    
    const ctx = salesChartCanvas.getContext('2d');
    
    // Fetch sales data
    fetch('/admin/api/sales-data')
        .then(response => response.json())
        .then(data => {
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        label: 'Daily Sales',
                        data: data.sales || [],
                        borderColor: '#E86A17',
                        backgroundColor: 'rgba(232, 106, 23, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Sales Overview (Last 30 Days)'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return '₹' + value.toLocaleString('en-IN');
                                }
                            }
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Failed to load sales data:', error);
            salesChartCanvas.style.display = 'none';
        });
}

// Category distribution chart
function initializeCategoryChart() {
    const categoryChartCanvas = document.querySelector('#categoryChart');
    if (!categoryChartCanvas) return;
    
    const ctx = categoryChartCanvas.getContext('2d');
    
    fetch('/admin/api/category-data')
        .then(response => response.json())
        .then(data => {
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        data: data.sales || [],
                        backgroundColor: [
                            '#E86A17',
                            '#5A4034',
                            '#3B2A22',
                            '#D4AF37',
                            '#228B22',
                            '#191970'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Sales by Category'
                        },
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Failed to load category data:', error);
            categoryChartCanvas.style.display = 'none';
        });
}

// Refresh dashboard statistics
function refreshDashboardStats() {
    fetch('/admin/api/dashboard-stats')
        .then(response => response.json())
        .then(data => {
            updateStatCard('today-orders', data.today_orders);
            updateStatCard('today-sales', formatCurrency(data.today_sales));
            updateStatCard('mtd-orders', data.mtd_orders);
            updateStatCard('mtd-sales', formatCurrency(data.mtd_sales));
            updateStatCard('pending-reviews', data.pending_reviews);
            updateStatCard('low-stock-count', data.low_stock_count);
        })
        .catch(error => {
            console.error('Failed to refresh dashboard stats:', error);
        });
}

function updateStatCard(cardId, value) {
    const element = document.querySelector(`#${cardId}`);
    if (element) {
        element.textContent = value;
        element.classList.add('updated');
        setTimeout(() => element.classList.remove('updated'), 1000);
    }
}

// Product management
function initializeProductManagement() {
    // Product status toggle
    document.querySelectorAll('.product-status-toggle').forEach(toggle => {
        toggle.addEventListener('change', function() {
            toggleProductStatus(this);
        });
    });
    
    // Bulk product actions
    const bulkActionSelect = document.querySelector('#bulk-product-action');
    const bulkActionBtn = document.querySelector('#bulk-action-btn');
    
    if (bulkActionSelect && bulkActionBtn) {
        bulkActionBtn.addEventListener('click', function() {
            const action = bulkActionSelect.value;
            const selectedProducts = getSelectedProducts();
            
            if (action && selectedProducts.length > 0) {
                performBulkProductAction(action, selectedProducts);
            } else {
                showToast('Please select products and an action', 'warning');
            }
        });
    }
    
    // Product search with debounce
    const productSearchInput = document.querySelector('#product-search');
    if (productSearchInput) {
        productSearchInput.addEventListener('input', debounce(function() {
            filterProducts(this.value);
        }, 500));
    }
    
    // Initialize product form enhancements
    initializeProductForm();
}

function toggleProductStatus(toggle) {
    const productId = toggle.dataset.productId;
    const newStatus = toggle.checked ? 'Active' : 'Archived';
    
    fetch(`/admin/api/products/${productId}/toggle_status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(`Product status updated to ${data.new_status}`, 'success');
            
            // Update status badge
            const statusBadge = toggle.closest('tr').querySelector('.status-badge');
            if (statusBadge) {
                statusBadge.textContent = data.new_status;
                statusBadge.className = `badge status-badge ${data.new_status.toLowerCase() === 'active' ? 'bg-success' : 'bg-secondary'}`;
            }
        } else {
            // Revert toggle on error
            toggle.checked = !toggle.checked;
            showToast('Failed to update product status', 'error');
        }
    })
    .catch(error => {
        console.error('Toggle status error:', error);
        toggle.checked = !toggle.checked;
        showToast('Failed to update product status', 'error');
    });
}

function getSelectedProducts() {
    const checkboxes = document.querySelectorAll('input[name="selected_products"]:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

function performBulkProductAction(action, productIds) {
    if (!confirm(`Are you sure you want to ${action.toLowerCase()} ${productIds.length} product(s)?`)) {
        return;
    }
    
    fetch('/admin/api/products/bulk-action', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            action: action,
            product_ids: productIds
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(`${action} completed for ${productIds.length} product(s)`, 'success');
            location.reload(); // Reload to show changes
        } else {
            showToast(data.message || 'Bulk action failed', 'error');
        }
    })
    .catch(error => {
        console.error('Bulk action error:', error);
        showToast('Bulk action failed', 'error');
    });
}

function filterProducts(searchTerm) {
    const rows = document.querySelectorAll('#products-table tbody tr');
    
    rows.forEach(row => {
        const productTitle = row.querySelector('.product-title').textContent.toLowerCase();
        const isbn = row.querySelector('.product-isbn').textContent.toLowerCase();
        
        if (productTitle.includes(searchTerm.toLowerCase()) || 
            isbn.includes(searchTerm.toLowerCase())) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// Product form enhancements
function initializeProductForm() {
    const titleInput = document.querySelector('#title');
    const slugInput = document.querySelector('#slug');
    
    // Auto-generate slug from title
    if (titleInput && slugInput) {
        titleInput.addEventListener('input', function() {
            if (!slugInput.dataset.manual) {
                slugInput.value = generateSlug(this.value);
            }
        });
        
        slugInput.addEventListener('input', function() {
            this.dataset.manual = 'true';
        });
    }
    
    // Category and author multi-select
    initializeMultiSelect();
    
    // Price calculations
    initializePriceCalculations();
    
    // Image preview
    initializeImagePreview();
}

function generateSlug(text) {
    return text
        .toLowerCase()
        .replace(/[^a-z0-9 -]/g, '')
        .replace(/\s+/g, '-')
        .replace(/-+/g, '-')
        .trim('-');
}

function initializeMultiSelect() {
    // Initialize Select2 or similar for multi-select dropdowns
    if (typeof $ !== 'undefined' && $.fn.select2) {
        $('.multi-select').select2({
            placeholder: 'Select options...',
            allowClear: true
        });
    }
}

function initializePriceCalculations() {
    const mrpInput = document.querySelector('#mrp_inr');
    const saleInput = document.querySelector('#sale_inr');
    const discountDisplay = document.querySelector('#discount-percentage');
    
    if (mrpInput && saleInput && discountDisplay) {
        function calculateDiscount() {
            const mrp = parseFloat(mrpInput.value) || 0;
            const sale = parseFloat(saleInput.value) || 0;
            
            if (mrp > 0 && sale > 0 && sale < mrp) {
                const discount = ((mrp - sale) / mrp * 100).toFixed(1);
                discountDisplay.textContent = `${discount}% discount`;
                discountDisplay.className = 'text-success';
            } else {
                discountDisplay.textContent = '';
            }
        }
        
        mrpInput.addEventListener('input', calculateDiscount);
        saleInput.addEventListener('input', calculateDiscount);
    }
}

function initializeImagePreview() {
    const imageInput = document.querySelector('#cover_image');
    const imagePreview = document.querySelector('#image-preview');
    
    if (imageInput && imagePreview) {
        imageInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    imagePreview.src = e.target.result;
                    imagePreview.style.display = 'block';
                };
                reader.readAsDataURL(file);
            }
        });
    }
}

// Order management
function initializeOrderManagement() {
    // Order status update
    document.querySelectorAll('.order-status-select').forEach(select => {
        select.addEventListener('change', function() {
            updateOrderStatus(this);
        });
    });
    
    // Order search and filters
    const orderSearchInput = document.querySelector('#order-search');
    if (orderSearchInput) {
        orderSearchInput.addEventListener('input', debounce(function() {
            filterOrders(this.value);
        }, 500));
    }
    
    // Order actions
    document.querySelectorAll('.order-action-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const action = this.dataset.action;
            const orderId = this.dataset.orderId;
            performOrderAction(action, orderId);
        });
    });
}

function updateOrderStatus(select) {
    const orderId = select.dataset.orderId;
    const newStatus = select.value;
    const originalStatus = select.dataset.originalStatus;
    
    if (newStatus === originalStatus) return;
    
    if (!confirm(`Change order status to ${newStatus}?`)) {
        select.value = originalStatus;
        return;
    }
    
    fetch(`/admin/orders/${orderId}/update_status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: `status=${encodeURIComponent(newStatus)}`
    })
    .then(response => {
        if (response.ok) {
            showToast(`Order status updated to ${newStatus}`, 'success');
            select.dataset.originalStatus = newStatus;
            
            // Update status badge
            const statusBadge = select.closest('tr').querySelector('.status-badge');
            if (statusBadge) {
                statusBadge.textContent = newStatus;
                statusBadge.className = `badge status-badge ${getStatusBadgeClass(newStatus)}`;
            }
        } else {
            select.value = originalStatus;
            showToast('Failed to update order status', 'error');
        }
    })
    .catch(error => {
        console.error('Update status error:', error);
        select.value = originalStatus;
        showToast('Failed to update order status', 'error');
    });
}

function getStatusBadgeClass(status) {
    const statusClasses = {
        'Pending': 'bg-warning',
        'Paid': 'bg-info',
        'Packed': 'bg-primary',
        'Shipped': 'bg-secondary',
        'Delivered': 'bg-success',
        'Cancelled': 'bg-danger',
        'Refunded': 'bg-dark'
    };
    return statusClasses[status] || 'bg-secondary';
}

function performOrderAction(action, orderId) {
    let confirmMessage = '';
    let endpoint = '';
    
    switch (action) {
        case 'generate_invoice':
            window.open(`/admin/orders/${orderId}/invoice`, '_blank');
            return;
        case 'send_confirmation':
            confirmMessage = 'Send order confirmation email?';
            endpoint = `/admin/api/orders/${orderId}/send-confirmation`;
            break;
        case 'cancel_order':
            confirmMessage = 'Cancel this order? This action cannot be undone.';
            endpoint = `/admin/api/orders/${orderId}/cancel`;
            break;
        case 'refund_order':
            confirmMessage = 'Process refund for this order?';
            endpoint = `/admin/api/orders/${orderId}/refund`;
            break;
        default:
            return;
    }
    
    if (confirm(confirmMessage)) {
        fetch(endpoint, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast(data.message || 'Action completed successfully', 'success');
                if (action === 'cancel_order' || action === 'refund_order') {
                    location.reload();
                }
            } else {
                showToast(data.message || 'Action failed', 'error');
            }
        })
        .catch(error => {
            console.error('Order action error:', error);
            showToast('Action failed', 'error');
        });
    }
}

function filterOrders(searchTerm) {
    const rows = document.querySelectorAll('#orders-table tbody tr');
    
    rows.forEach(row => {
        const orderId = row.querySelector('.order-id').textContent.toLowerCase();
        const customerEmail = row.querySelector('.customer-email').textContent.toLowerCase();
        const customerPhone = row.querySelector('.customer-phone').textContent.toLowerCase();
        
        if (orderId.includes(searchTerm.toLowerCase()) || 
            customerEmail.includes(searchTerm.toLowerCase()) ||
            customerPhone.includes(searchTerm.toLowerCase())) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// Data tables initialization
function initializeDataTables() {
    if (typeof DataTable !== 'undefined') {
        // Initialize DataTables for large tables
        const tables = document.querySelectorAll('.data-table');
        tables.forEach(table => {
            new DataTable(table, {
                pageLength: 25,
                responsive: true,
                order: [[0, 'desc']], // Default sort by first column descending
                language: {
                    search: 'Search:',
                    lengthMenu: 'Show _MENU_ entries',
                    info: 'Showing _START_ to _END_ of _TOTAL_ entries',
                    infoEmpty: 'No entries available',
                    infoFiltered: '(filtered from _MAX_ total entries)',
                    paginate: {
                        first: 'First',
                        last: 'Last',
                        next: 'Next',
                        previous: 'Previous'
                    }
                }
            });
        });
    }
}

// Bulk actions
function initializeBulkActions() {
    // Select all checkbox
    const selectAllCheckbox = document.querySelector('#select-all');
    const itemCheckboxes = document.querySelectorAll('input[name="selected_items"]');
    
    if (selectAllCheckbox && itemCheckboxes.length > 0) {
        selectAllCheckbox.addEventListener('change', function() {
            itemCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateBulkActionButtons();
        });
        
        itemCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                updateSelectAllState();
                updateBulkActionButtons();
            });
        });
    }
}

function updateSelectAllState() {
    const selectAllCheckbox = document.querySelector('#select-all');
    const itemCheckboxes = document.querySelectorAll('input[name="selected_items"]');
    
    if (selectAllCheckbox && itemCheckboxes.length > 0) {
        const checkedCount = document.querySelectorAll('input[name="selected_items"]:checked').length;
        
        if (checkedCount === 0) {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = false;
        } else if (checkedCount === itemCheckboxes.length) {
            selectAllCheckbox.checked = true;
            selectAllCheckbox.indeterminate = false;
        } else {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = true;
        }
    }
}

function updateBulkActionButtons() {
    const selectedCount = document.querySelectorAll('input[name="selected_items"]:checked').length;
    const bulkActionButtons = document.querySelectorAll('.bulk-action-btn');
    
    bulkActionButtons.forEach(btn => {
        btn.disabled = selectedCount === 0;
        const countSpan = btn.querySelector('.selected-count');
        if (countSpan) {
            countSpan.textContent = selectedCount;
        }
    });
}

// Image upload handling
function initializeImageUpload() {
    const imageUploadZones = document.querySelectorAll('.image-upload-zone');
    
    imageUploadZones.forEach(zone => {
        const input = zone.querySelector('input[type="file"]');
        const preview = zone.querySelector('.image-preview');
        
        // Drag and drop
        zone.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('dragover');
        });
        
        zone.addEventListener('dragleave', function(e) {
            e.preventDefault();
            this.classList.remove('dragover');
        });
        
        zone.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                input.files = files;
                handleImageUpload(files[0], preview);
            }
        });
        
        // Click to upload
        zone.addEventListener('click', function() {
            input.click();
        });
        
        input.addEventListener('change', function() {
            if (this.files.length > 0) {
                handleImageUpload(this.files[0], preview);
            }
        });
    });
}

function handleImageUpload(file, previewElement) {
    // Validate file type
    if (!file.type.match(/^image\/(jpeg|jpg|png|gif)$/)) {
        showToast('Please select a valid image file (JPEG, PNG, or GIF)', 'error');
        return;
    }
    
    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
        showToast('Image file size must be less than 5MB', 'error');
        return;
    }
    
    // Show preview
    if (previewElement) {
        const reader = new FileReader();
        reader.onload = function(e) {
            previewElement.src = e.target.result;
            previewElement.style.display = 'block';
        };
        reader.readAsDataURL(file);
    }
}

// Inventory management
function initializeInventoryManagement() {
    // Inline stock editing
    document.querySelectorAll('.stock-inline-edit').forEach(element => {
        element.addEventListener('blur', function() {
            updateProductStock(this);
        });
        
        element.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                this.blur();
            }
        });
    });
    
    // Low stock alerts
    checkLowStockAlerts();
}

function updateProductStock(input) {
    const productId = input.dataset.productId;
    const newStock = parseInt(input.value);
    const originalStock = parseInt(input.dataset.originalValue);
    
    if (newStock === originalStock) return;
    
    if (isNaN(newStock) || newStock < 0) {
        input.value = originalStock;
        showToast('Please enter a valid stock quantity', 'error');
        return;
    }
    
    fetch(`/admin/api/inventory/${productId}/update`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            stock: newStock
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            input.dataset.originalValue = newStock;
            showToast('Stock updated successfully', 'success');
            
            // Update low stock indicator
            const lowStockIndicator = input.closest('tr').querySelector('.low-stock-indicator');
            if (lowStockIndicator) {
                const threshold = parseInt(input.dataset.threshold) || 5;
                if (newStock <= threshold) {
                    lowStockIndicator.style.display = 'inline';
                } else {
                    lowStockIndicator.style.display = 'none';
                }
            }
        } else {
            input.value = originalStock;
            showToast(data.error || 'Failed to update stock', 'error');
        }
    })
    .catch(error => {
        console.error('Stock update error:', error);
        input.value = originalStock;
        showToast('Failed to update stock', 'error');
    });
}

function checkLowStockAlerts() {
    const lowStockItems = document.querySelectorAll('.low-stock-item');
    if (lowStockItems.length > 0) {
        showToast(`${lowStockItems.length} items are running low on stock`, 'warning');
    }
}

// Coupon management
function initializeCouponManagement() {
    const couponTypeSelect = document.querySelector('#coupon-type');
    const valueLabel = document.querySelector('#value-label');
    const valueInput = document.querySelector('#coupon-value');
    
    if (couponTypeSelect && valueLabel && valueInput) {
        couponTypeSelect.addEventListener('change', function() {
            if (this.value === 'PERCENT') {
                valueLabel.textContent = 'Percentage (%)';
                valueInput.max = '100';
                valueInput.step = '0.01';
            } else {
                valueLabel.textContent = 'Amount (₹)';
                valueInput.max = '';
                valueInput.step = '0.01';
            }
        });
    }
    
    // Coupon code generator
    const generateCodeBtn = document.querySelector('#generate-coupon-code');
    if (generateCodeBtn) {
        generateCodeBtn.addEventListener('click', function() {
            const codeInput = document.querySelector('#coupon-code');
            if (codeInput) {
                codeInput.value = generateCouponCode();
            }
        });
    }
}

function generateCouponCode() {
    const prefix = 'ABC';
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let result = prefix;
    
    for (let i = 0; i < 6; i++) {
        result += characters.charAt(Math.floor(Math.random() * characters.length));
    }
    
    return result;
}

// Notifications
function initializeNotifications() {
    // Check for new notifications every 2 minutes
    setInterval(checkNotifications, 120000);
    
    // Mark notifications as read when clicked
    document.querySelectorAll('.notification-item').forEach(item => {
        item.addEventListener('click', function() {
            markNotificationAsRead(this.dataset.notificationId);
        });
    });
}

function checkNotifications() {
    fetch('/admin/api/notifications')
        .then(response => response.json())
        .then(data => {
            updateNotificationCounter(data.unread_count);
            if (data.new_notifications && data.new_notifications.length > 0) {
                showNewNotifications(data.new_notifications);
            }
        })
        .catch(error => {
            console.error('Notification check error:', error);
        });
}

function updateNotificationCounter(count) {
    const counter = document.querySelector('.notification-counter');
    if (counter) {
        if (count > 0) {
            counter.textContent = count > 99 ? '99+' : count;
            counter.style.display = 'inline';
        } else {
            counter.style.display = 'none';
        }
    }
}

function showNewNotifications(notifications) {
    notifications.forEach(notification => {
        showToast(notification.message, notification.type || 'info');
    });
}

function markNotificationAsRead(notificationId) {
    fetch(`/admin/api/notifications/${notificationId}/read`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .catch(error => {
        console.error('Mark notification read error:', error);
    });
}

// Utility functions
function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type} show`;
    toast.innerHTML = `
        <div class="toast-body d-flex align-items-center">
            <i class="fas fa-${getToastIcon(type)} me-2"></i>
            <span class="flex-grow-1">${message}</span>
            <button type="button" class="btn-close btn-close-white ms-2" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    // Add to toast container
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    toastContainer.appendChild(toast);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        toast.remove();
    }, 5000);
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

function formatCurrency(amount, currency = 'INR') {
    if (amount === null || amount === undefined) return '₹0.00';
    
    const value = parseFloat(amount) / 100; // Convert from paisa
    if (currency === 'INR') {
        return `₹${value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
    return `${currency} ${value.toFixed(2)}`;
}

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

// Export functions for global use
window.AdminManager = {
    showToast,
    formatCurrency,
    toggleProductStatus,
    updateOrderStatus,
    updateProductStock,
    performBulkProductAction,
    generateSlug,
    debounce
};

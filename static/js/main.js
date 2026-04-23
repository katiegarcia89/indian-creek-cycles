/**
 * Indian Creek Cycles - Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initNavigation();
    initMessages();
    initSmoothScroll();
});

/**
 * Mobile Navigation Toggle
 */
function initNavigation() {
    const navbarToggle = document.getElementById('navbar-toggle');
    const navbarNav = document.getElementById('navbar-nav');
    
    if (navbarToggle && navbarNav) {
        navbarToggle.addEventListener('click', function() {
            navbarNav.classList.toggle('active');
            
            // Animate hamburger to X
            const spans = navbarToggle.querySelectorAll('span');
            if (navbarNav.classList.contains('active')) {
                spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
                spans[1].style.opacity = '0';
                spans[2].style.transform = 'rotate(-45deg) translate(5px, -5px)';
            } else {
                spans[0].style.transform = 'none';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'none';
            }
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!navbarToggle.contains(e.target) && !navbarNav.contains(e.target)) {
                navbarNav.classList.remove('active');
                const spans = navbarToggle.querySelectorAll('span');
                spans[0].style.transform = 'none';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'none';
            }
        });
    }
    
    // Navbar scroll effect
    const navbar = document.getElementById('navbar');
    if (navbar) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 50) {
                navbar.style.background = 'rgba(10, 10, 10, 0.98)';
            } else {
                navbar.style.background = 'rgba(10, 10, 10, 0.95)';
            }
        });
    }
}

/**
 * Message/Alert Dismissal
 */
function initMessages() {
    const alerts = document.querySelectorAll('.alert');
    
    alerts.forEach(alert => {
        const closeBtn = alert.querySelector('.alert-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                alert.style.opacity = '0';
                alert.style.transform = 'translateX(100%)';
                setTimeout(() => alert.remove(), 300);
            });
        }
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.style.opacity = '0';
                alert.style.transform = 'translateX(100%)';
                setTimeout(() => alert.remove(), 300);
            }
        }, 5000);
    });
}

/**
 * Smooth Scroll for Anchor Links
 */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                e.preventDefault();
                const navbarHeight = document.getElementById('navbar')?.offsetHeight || 0;
                const targetPosition = targetElement.offsetTop - navbarHeight - 20;
                
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
}

/**
 * Form Validation Helpers
 */
function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            isValid = false;
            field.classList.add('is-invalid');
            
            // Add error message if not exists
            let errorMsg = field.parentNode.querySelector('.form-error');
            if (!errorMsg) {
                errorMsg = document.createElement('span');
                errorMsg.className = 'form-error';
                errorMsg.textContent = 'This field is required';
                field.parentNode.appendChild(errorMsg);
            }
        } else {
            field.classList.remove('is-invalid');
            const errorMsg = field.parentNode.querySelector('.form-error');
            if (errorMsg) errorMsg.remove();
        }
    });
    
    return isValid;
}

/**
 * Date Input Helpers
 */
function setMinDate(inputId, daysFromNow = 0) {
    const input = document.getElementById(inputId);
    if (input) {
        const date = new Date();
        date.setDate(date.getDate() + daysFromNow);
        input.min = date.toISOString().split('T')[0];
    }
}

/**
 * AJAX Helper
 */
function ajaxRequest(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    };
    
    return fetch(url, { ...defaultOptions, ...options })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        });
}

/**
 * Debounce Function
 */
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

/**
 * Throttle Function
 */
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Intersection Observer for Animations
 */
function initScrollAnimations() {
    const animatedElements = document.querySelectorAll('[data-animate]');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animated');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });
    
    animatedElements.forEach(el => observer.observe(el));
}

/**
 * Lazy Loading Images
 */
function initLazyLoading() {
    const lazyImages = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                imageObserver.unobserve(img);
            }
        });
    });
    
    lazyImages.forEach(img => imageObserver.observe(img));
}

/**
 * Print Functionality
 */
function printPage() {
    window.print();
}

/**
 * Copy to Clipboard
 */
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Copied to clipboard!', 'success');
        }).catch(() => {
            showNotification('Failed to copy', 'error');
        });
    } else {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        
        try {
            document.execCommand('copy');
            showNotification('Copied to clipboard!', 'success');
        } catch (err) {
            showNotification('Failed to copy', 'error');
        }
        
        document.body.removeChild(textarea);
    }
}

/**
 * Show Notification
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    notification.innerHTML = `
        <span class="alert-message">${message}</span>
        <button type="button" class="alert-close">&times;</button>
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    requestAnimationFrame(() => {
        notification.style.animation = 'slideIn 0.3s ease';
    });
    
    // Auto dismiss
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
    
    // Close button
    notification.querySelector('.alert-close').addEventListener('click', () => {
        notification.remove();
    });
}

/**
 * Format Currency
 */
function formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

/**
 * Format Date
 */
function formatDate(date, options = {}) {
    const defaultOptions = {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    };
    
    return new Intl.DateTimeFormat('en-US', { ...defaultOptions, ...options })
        .format(new Date(date));
}

/**
 * Countdown Timer
 */
function initCountdown(targetDate, elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const target = new Date(targetDate).getTime();
    
    const updateCountdown = () => {
        const now = new Date().getTime();
        const distance = target - now;
        
        if (distance < 0) {
            element.innerHTML = 'Expired';
            return;
        }
        
        const days = Math.floor(distance / (1000 * 60 * 60 * 24));
        const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);
        
        element.innerHTML = `${days}d ${hours}h ${minutes}m ${seconds}s`;
    };
    
    updateCountdown();
    setInterval(updateCountdown, 1000);
}

// Export functions for global access
window.IndianCreekCycles = {
    validateForm,
    ajaxRequest,
    debounce,
    throttle,
    copyToClipboard,
    showNotification,
    formatCurrency,
    formatDate,
    initCountdown,
    setMinDate
};

document.addEventListener('DOMContentLoaded', function () {

    const disabledDates = window.bookedDates || [];
    const warningBox = document.getElementById('time-warning');
    const submitBtn = document.getElementById('submit-btn');

    let rentalPicker, returnPicker, timePickerStart, timePickerEnd;

    const validateTimes = () => {
        const startDay = rentalPicker.selectedDates[0];
        const endDay = returnPicker.selectedDates[0];
        const startTime = timePickerStart.selectedDates[0];
        const endTime = timePickerEnd.selectedDates[0];

        if (startDay && endDay && startTime && endTime) {
            const fullStart = new Date(startDay.getFullYear(), startDay.getMonth(), startDay.getDate(), startTime.getHours(), 0);
            const fullEnd = new Date(endDay.getFullYear(), endDay.getMonth(), endDay.getDate(), endTime.getHours(), 0);

            const diffInHours = (fullEnd - fullStart) / (1000 * 60 * 60);
            const daysPaid = Math.ceil((endDay - startDay) / (1000 * 60 * 60 * 24)) || 1;
            const maxAllowedHours = daysPaid * 24;

            document.getElementById('day-display').innerText = `${daysPaid} Day(s)`;

            if (diffInHours > 0 && diffInHours <= maxAllowedHours + 0.02) {
                warningBox.innerHTML = "✓ Within rental window";
                warningBox.style.color = "#27ae60";
                submitBtn.disabled = false;
                submitBtn.style.opacity = "1";
            } else if (diffInHours <= 0) {
                warningBox.innerHTML = "⚠ Return must be after pickup";
                warningBox.style.color = "#e74c3c";
                submitBtn.disabled = true;
                submitBtn.style.opacity = "0.5";
            } else {
                warningBox.innerHTML = `⚠ Exceeds ${daysPaid} day limit`;
                warningBox.style.color = "#e74c3c";
                submitBtn.disabled = true;
                submitBtn.style.opacity = "0.5";
            }
        }
    };

    // TIME PICKERS
    if (document.getElementById("pickup_time_picker")) {
        timePickerStart = flatpickr("#pickup_time_picker", {
            enableTime: true,
            noCalendar: true,
            altInput: true,
            altFormat: "h:i K",
            dateFormat: "H:i",
            defaultDate: "09:00",
            minTime: "08:00",
            maxTime: "17:00",
            minuteIncrement: 60,
            static: true,
            onChange: validateTimes
        });
    }

    if (document.getElementById("return_time_picker")) {
        timePickerEnd = flatpickr("#return_time_picker", {
            enableTime: true,
            noCalendar: true,
            altInput: true,
            altFormat: "h:i K",
            dateFormat: "H:i",
            defaultDate: "09:00",
            minuteIncrement: 60,
            static: true,
            onChange: validateTimes
        });
    }


    // DATE PICKERS
    if (window.rentalDateId && document.getElementById(window.rentalDateId)) {
        rentalPicker = flatpickr(`#${window.rentalDateId}`, {
            minDate: "today",
            disable: disabledDates,
            dateFormat: "Y-m-d",
            onChange: (selectedDates, dateStr) => {
                if (returnPicker) {
                    returnPicker.set('minDate', dateStr);
                }
                validateTimes();
            }
        });
    }

    if (window.returnDateId && document.getElementById(window.returnDateId)) {
        returnPicker = flatpickr(`#${window.returnDateId}`, {
            minDate: "today",
            disable: disabledDates,
            dateFormat: "Y-m-d",
            onChange: validateTimes
        });
    }
}); 
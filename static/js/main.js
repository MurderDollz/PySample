// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Initialize popovers
    if (typeof bootstrap !== 'undefined') {
        var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }

    // Handle Navbar Scroll Effect
    const navbar = document.querySelector('.navbar');
    
    if (navbar) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 50) {
                navbar.classList.add('bg-white', 'shadow-sm');
                navbar.classList.remove('navbar-dark');
                navbar.classList.add('navbar-light');
            } else {
                navbar.classList.remove('bg-white', 'shadow-sm');
                navbar.classList.add('navbar-dark');
                navbar.classList.remove('navbar-light');
            }
        });
    }

    // Handle form submissions with animation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            // Get submit button
            const submitBtn = form.querySelector('button[type="submit"]');
            if (!submitBtn) return;
            
            const originalText = submitBtn.textContent;
            const originalWidth = submitBtn.offsetWidth;
            
            // Set width to avoid resizing during state changes
            submitBtn.style.width = originalWidth + 'px';
            
            // Disable button and show loading
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Sending...';
            
            // Simulate API call with timeout
            setTimeout(function() {
                // Success state
                submitBtn.innerHTML = '<i class="fas fa-check"></i> Sent!';
                submitBtn.classList.remove('btn-primary');
                submitBtn.classList.add('btn-success');
                
                // Reset form
                form.reset();
                
                // Reset button after delay
                setTimeout(function() {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                    submitBtn.classList.remove('btn-success');
                    submitBtn.classList.add('btn-primary');
                    submitBtn.style.width = 'auto';
                }, 2000);
            }, 1500);
        });
    });

    // Handle favorite buttons
    const favoriteButtons = document.querySelectorAll('.btn-light .fa-heart, .btn-light .far.fa-heart');
    favoriteButtons.forEach(btn => {
        btn.parentElement.addEventListener('click', function(e) {
            e.preventDefault();
            const icon = this.querySelector('i');
            if (icon.classList.contains('far')) {
                icon.classList.remove('far');
                icon.classList.add('fas', 'text-danger');
                this.classList.add('favorited');
                
                // Add a little bounce animation
                this.animate([
                    { transform: 'scale(1)' },
                    { transform: 'scale(1.2)' },
                    { transform: 'scale(1)' }
                ], {
                    duration: 300,
                    easing: 'ease-in-out'
                });
            } else {
                icon.classList.remove('fas', 'text-danger');
                icon.classList.add('far');
                this.classList.remove('favorited');
            }
        });
    });

    // Category hover effects
    const categoryItems = document.querySelectorAll('.category-item');
    categoryItems.forEach(item => {
        item.addEventListener('mouseenter', function() {
            const icon = this.querySelector('.category-icon i');
            if (icon) {
                icon.animate([
                    { transform: 'translateY(0)' },
                    { transform: 'translateY(-10px)' },
                    { transform: 'translateY(0)' }
                ], {
                    duration: 500,
                    easing: 'ease-in-out'
                });
            }
        });
    });

    // Counter animation for statistics
    const animateCounter = (element, start, end, duration) => {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const currentCount = Math.floor(progress * (end - start) + start);
            element.textContent = currentCount;
            if (progress < 1) {
                window.requestAnimationFrame(step);
            } else {
                element.textContent = end + "+";
            }
        };
        window.requestAnimationFrame(step);
    };

    // Find all counter elements and animate them when they come into view
    const counterElements = document.querySelectorAll('.h3.fw-bold.text-primary');
    
    if (counterElements.length > 0) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const element = entry.target;
                    const targetValue = parseInt(element.textContent);
                    animateCounter(element, 0, targetValue, 2000);
                    observer.unobserve(element);
                }
            });
        }, { threshold: 0.5 });

        counterElements.forEach(element => {
            observer.observe(element);
        });
    }

    // Mobile menu enhancements
    const navbarToggler = document.querySelector('.navbar-toggler');
    if (navbarToggler) {
        navbarToggler.addEventListener('click', function() {
            document.body.classList.toggle('mobile-menu-open');
        });
    }

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                e.preventDefault();
                window.scrollTo({
                    top: targetElement.offsetTop - 100,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Initialize AOS animations
    AOS.init({
        duration: 800,
        easing: 'ease-in-out',
        once: true
    });

    // Add navbar scroll class
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 50) {
                navbar.classList.add('navbar-scrolled', 'shadow-sm');
            } else {
                navbar.classList.remove('navbar-scrolled', 'shadow-sm');
            }
        });
    }

    // Form validation for login and register
    const loginForm = document.querySelector('form[action="/login"]');
    const registerForm = document.querySelector('form[action="/register"]');
    
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            validateLoginForm();
        });
    }
    
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            validateRegisterForm();
        });
    }
});

// Simple form validation for login
function validateLoginForm() {
    const email = document.getElementById('email');
    const password = document.getElementById('password');
    let isValid = true;
    
    // Reset error states
    resetFormErrors();
    
    // Email validation
    if (!email.value.trim()) {
        showError(email, 'Email is required');
        isValid = false;
    } else if (!isValidEmail(email.value)) {
        showError(email, 'Please enter a valid email');
        isValid = false;
    }
    
    // Password validation
    if (!password.value.trim()) {
        showError(password, 'Password is required');
        isValid = false;
    }
    
    if (isValid) {
        // Here you would typically submit the form to a backend
        showSuccessMessage('Login successful! Redirecting...');
        // In a real application, form would be submitted or AJAX call made
    }
}

// Simple form validation for register
function validateRegisterForm() {
    const firstName = document.getElementById('firstName');
    const lastName = document.getElementById('lastName');
    const email = document.getElementById('email');
    const phone = document.getElementById('phone');
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirmPassword');
    const terms = document.getElementById('terms');
    let isValid = true;
    
    // Reset error states
    resetFormErrors();
    
    // Name validation
    if (!firstName.value.trim()) {
        showError(firstName, 'First name is required');
        isValid = false;
    }
    
    if (!lastName.value.trim()) {
        showError(lastName, 'Last name is required');
        isValid = false;
    }
    
    // Email validation
    if (!email.value.trim()) {
        showError(email, 'Email is required');
        isValid = false;
    } else if (!isValidEmail(email.value)) {
        showError(email, 'Please enter a valid email');
        isValid = false;
    }
    
    // Phone validation (optional field but must be valid if provided)
    if (phone.value.trim() && !isValidPhone(phone.value)) {
        showError(phone, 'Please enter a valid phone number');
        isValid = false;
    }
    
    // Password validation
    if (!password.value.trim()) {
        showError(password, 'Password is required');
        isValid = false;
    } else if (password.value.length < 8) {
        showError(password, 'Password must be at least 8 characters');
        isValid = false;
    }
    
    // Confirm password
    if (password.value !== confirmPassword.value) {
        showError(confirmPassword, 'Passwords do not match');
        isValid = false;
    }
    
    // Terms agreement
    if (!terms.checked) {
        showError(terms, 'You must agree to the terms and conditions');
        isValid = false;
    }
    
    if (isValid) {
        // Here you would typically submit the form to a backend
        showSuccessMessage('Registration successful! Redirecting...');
        // In a real application, form would be submitted or AJAX call made
    }
}

// Helper functions
function isValidEmail(email) {
    const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(String(email).toLowerCase());
}

function isValidPhone(phone) {
    // Philippines phone number validation
    // Accepts formats like:
    // - +63 917 123 4567
    // - +63917123456
    // - 09171234567
    // - 0917 123 4567
    // - 0917-123-4567
    const re = /^(\+63|0)([0-9]{9,10}|[0-9]{3}[\s.-]?[0-9]{3}[\s.-]?[0-9]{4})$/;
    return re.test(phone);
}

function showError(input, message) {
    const formGroup = input.closest('.mb-4') || input.closest('.form-check');
    
    // Remove existing error messages
    const existingError = formGroup.querySelector('.text-danger');
    if (existingError) {
        existingError.remove();
    }
    
    // Add error message
    const errorElement = document.createElement('div');
    errorElement.className = 'text-danger small mt-1';
    errorElement.textContent = message;
    
    if (input.type === 'checkbox') {
        input.closest('.form-check').appendChild(errorElement);
    } else {
        input.closest('.input-group').after(errorElement);
    }
    
    // Add error class to input
    input.classList.add('is-invalid');
}

function resetFormErrors() {
    // Remove all error messages
    document.querySelectorAll('.text-danger').forEach(el => el.remove());
    
    // Remove error class from inputs
    document.querySelectorAll('.is-invalid').forEach(input => {
        input.classList.remove('is-invalid');
    });
}

function showSuccessMessage(message) {
    // Create success alert
    const alert = document.createElement('div');
    alert.className = 'alert alert-success mt-3';
    alert.textContent = message;
    
    // Add to form
    const form = document.querySelector('form');
    form.appendChild(alert);
    
    // Remove after 3 seconds
    setTimeout(() => {
        alert.remove();
    }, 3000);
} 
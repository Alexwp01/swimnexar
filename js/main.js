// Mobile menu toggle
const menuToggle = document.getElementById('menuToggle');
const nav = document.getElementById('nav');

if (menuToggle && nav) {
    menuToggle.addEventListener('click', () => {
        menuToggle.classList.toggle('active');
        nav.classList.toggle('active');
    });

    // Close menu when clicking a link
    nav.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
            menuToggle.classList.remove('active');
            nav.classList.remove('active');
        });
    });
}

// Header scroll effect
const header = document.querySelector('.header');

if (header) {
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            header.style.boxShadow = '0 4px 20px rgba(0,0,0,0.1)';
        } else {
            header.style.boxShadow = 'none';
        }
    });
}

// Scroll animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
        }
    });
}, observerOptions);

// Observe elements for scroll animation
document.querySelectorAll('.program-card, .feature, .product-card, .coach-card').forEach(el => {
    observer.observe(el);
});

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (href !== '#') {
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        }
    });
});

// Form validation (for contact page)
const contactForm = document.querySelector('.contact-form form');

if (contactForm) {
    contactForm.addEventListener('submit', (e) => {
        e.preventDefault();

        // Basic validation
        const name = contactForm.querySelector('input[name="name"]');
        const email = contactForm.querySelector('input[name="email"]');
        const message = contactForm.querySelector('textarea[name="message"]');

        let isValid = true;

        if (name && !name.value.trim()) {
            showError(name, 'Please enter your name');
            isValid = false;
        }

        if (email && !isValidEmail(email.value)) {
            showError(email, 'Please enter a valid email');
            isValid = false;
        }

        if (message && !message.value.trim()) {
            showError(message, 'Please enter a message');
            isValid = false;
        }

        if (isValid) {
            // Show success message
            alert('Thank you for your message! We will get back to you soon.');
            contactForm.reset();
        }
    });
}

function showError(input, message) {
    input.style.borderColor = '#ef4444';
    input.placeholder = message;

    setTimeout(() => {
        input.style.borderColor = '';
        input.placeholder = '';
    }, 3000);
}

function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// Add to cart notification
document.querySelectorAll('.snipcart-add-item').forEach(btn => {
    btn.addEventListener('click', () => {
        // Visual feedback
        const originalText = btn.textContent;
        btn.textContent = 'Added!';
        btn.style.background = '#10b981';

        setTimeout(() => {
            btn.textContent = originalText;
            btn.style.background = '';
        }, 1500);
    });
});

// Page transition effect
document.addEventListener('DOMContentLoaded', () => {
    document.body.style.opacity = '0';
    setTimeout(() => {
        document.body.style.transition = 'opacity 0.3s ease';
        document.body.style.opacity = '1';
    }, 100);
});

// Active nav link based on current page
const currentPage = window.location.pathname.split('/').pop() || 'index.html';
document.querySelectorAll('.nav-link').forEach(link => {
    const href = link.getAttribute('href');
    if (href === currentPage) {
        link.classList.add('active');
    } else {
        link.classList.remove('active');
    }
});

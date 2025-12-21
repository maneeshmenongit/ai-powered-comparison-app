// Waitlist Form Handler
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('waitlistForm');
    const emailInput = document.getElementById('emailInput');
    const successMessage = document.getElementById('successMessage');
    
    // Form submission handler
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const email = emailInput.value.trim();
        
        // Validate email
        if (!isValidEmail(email)) {
            showError('Please enter a valid email address');
            return;
        }
        
        // Submit to your backend or email service
        submitToWaitlist(email);
    });
    
    // Email validation
    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    // Submit to waitlist (you'll replace this with your actual backend)
    function submitToWaitlist(email) {
        // Disable button during submission
        const submitBtn = form.querySelector('.submit-btn');
        const originalText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="btn-text">Joining...</span>';
        
        // Simulate API call (replace with your actual API endpoint)
        // Submit to Formspree
        fetch('https://formspree.io/f/xrbnlzoa', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email: email })
        })
        .then(response => response.json())
        .then(data => {
            // Success!
            showSuccess();
            form.reset();
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
            trackWaitlistSignup(email);
        })
        .catch(error => {
            showError('Something went wrong. Please try again.');
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        });
        
        /* 
        // PRODUCTION: Replace the setTimeout above with actual API call:
        
        fetch('https://your-backend.com/api/waitlist', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email: email })
        })
        .then(response => response.json())
        .then(data => {
            showSuccess();
            form.reset();
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
            trackWaitlistSignup(email);
        })
        .catch(error => {
            showError('Something went wrong. Please try again.');
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        });
        */
    }
    
    // Show success message
    function showSuccess() {
        form.style.display = 'none';
        successMessage.classList.add('show');
        
        // Confetti effect (optional)
        createConfetti();
    }
    
    // Show error message
    function showError(message) {
        // Create error element if it doesn't exist
        let errorEl = document.getElementById('errorMessage');
        if (!errorEl) {
            errorEl = document.createElement('p');
            errorEl.id = 'errorMessage';
            errorEl.style.cssText = `
                color: #FF6B6B;
                margin-top: 1rem;
                text-align: center;
                font-weight: 500;
            `;
            form.appendChild(errorEl);
        }
        
        errorEl.textContent = message;
        
        // Remove error after 3 seconds
        setTimeout(() => {
            errorEl.textContent = '';
        }, 3000);
    }
    
    // Store email in localStorage (temporary solution)
    function storeEmail(email) {
        const emails = JSON.parse(localStorage.getItem('hopwise_waitlist') || '[]');
        if (!emails.includes(email)) {
            emails.push(email);
            localStorage.setItem('hopwise_waitlist', JSON.stringify(emails));
        }
    }
    
    // Track analytics
    function trackWaitlistSignup(email) {
        // Google Analytics
        if (typeof gtag !== 'undefined') {
            gtag('event', 'waitlist_signup', {
                'event_category': 'engagement',
                'event_label': 'waitlist'
            });
        }
        
        // Facebook Pixel
        if (typeof fbq !== 'undefined') {
            fbq('track', 'Lead');
        }
        
        // Console log for development
        console.log('Waitlist signup:', email);
    }
    
    // Confetti effect (optional fun animation)
    function createConfetti() {
        const colors = ['#FF6B35', '#4ECDC4', '#FFE66D'];
        const confettiCount = 50;
        
        for (let i = 0; i < confettiCount; i++) {
            setTimeout(() => {
                const confetti = document.createElement('div');
                confetti.style.cssText = `
                    position: fixed;
                    width: 10px;
                    height: 10px;
                    background: ${colors[Math.floor(Math.random() * colors.length)]};
                    left: ${Math.random() * 100}vw;
                    top: -10px;
                    opacity: 1;
                    pointer-events: none;
                    z-index: 9999;
                    border-radius: ${Math.random() > 0.5 ? '50%' : '0'};
                `;
                
                document.body.appendChild(confetti);
                
                const duration = 3000 + Math.random() * 2000;
                const startTime = Date.now();
                
                function animate() {
                    const elapsed = Date.now() - startTime;
                    const progress = elapsed / duration;
                    
                    if (progress < 1) {
                        const y = progress * window.innerHeight;
                        const x = Math.sin(progress * 10) * 100;
                        const rotation = progress * 720;
                        const opacity = 1 - progress;
                        
                        confetti.style.transform = `translate(${x}px, ${y}px) rotate(${rotation}deg)`;
                        confetti.style.opacity = opacity;
                        
                        requestAnimationFrame(animate);
                    } else {
                        confetti.remove();
                    }
                }
                
                animate();
            }, i * 30);
        }
    }
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Intersection Observer for fade-in animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe feature cards
    document.querySelectorAll('.feature-card').forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = `all 0.6s ease ${index * 0.1}s`;
        observer.observe(card);
    });
    
    // Observe value points
    document.querySelectorAll('.value-point').forEach((point, index) => {
        point.style.opacity = '0';
        point.style.transform = 'translateY(30px)';
        point.style.transition = `all 0.6s ease ${index * 0.15}s`;
        observer.observe(point);
    });
});

// Console Easter Egg
console.log(`
🌍 Hopwise - Every stop matters!

Interested in joining our team?
Email: hello@hopwise.app

Built with ❤️ for travelers everywhere.
`);

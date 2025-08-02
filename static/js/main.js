document.addEventListener('DOMContentLoaded', function() {
    // Mobile navbar toggle
    const navbarToggle = document.querySelector('.navbar-toggle');
    const navbarLinks = document.querySelector('.navbar-links');
    
    if (navbarToggle && navbarLinks) {
        navbarToggle.addEventListener('click', function() {
            navbarLinks.classList.toggle('active');
        });
    }
    
    // Close flash messages
    const flashMessages = document.querySelectorAll('.flash');
    flashMessages.forEach(flash => {
        setTimeout(() => {
            flash.style.animation = 'slideIn 0.3s ease-out reverse';
            setTimeout(() => flash.remove(), 300);
        }, 5000);
    });
    
    // Add ripple effect to buttons
    const buttons = document.querySelectorAll('.btn-effect');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const rect = button.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const ripple = document.createElement('span');
            ripple.classList.add('ripple');
            ripple.style.left = `${x}px`;
            ripple.style.top = `${y}px`;
            
            button.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 1000);
            
            // Continue with the original action
            setTimeout(() => {
                if (button.tagName === 'A') {
                    window.location.href = button.href;
                } else if (button.type === 'submit') {
                    button.form.submit();
                }
            }, 300);
        });
    });
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Initialize animations when elements come into view
    const animateOnScroll = () => {
        const elements = document.querySelectorAll('.slide-in, .fade-in');
        
        elements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            const windowHeight = window.innerHeight;
            
            if (elementTop < windowHeight - 100) {
                element.classList.add('animate');
            }
        });
    };
    
    window.addEventListener('scroll', animateOnScroll);
    animateOnScroll(); // Run once on load
});
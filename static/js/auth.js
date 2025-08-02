document.addEventListener('DOMContentLoaded', function() {
    // Login form validation
    const loginForm = document.querySelector('form[action="{{ url_for('login') }}"]');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            const memberId = this.querySelector('#member_id');
            const pin = this.querySelector('#pin');
            
            if (!memberId.value.trim()) {
                e.preventDefault();
                alert('Please enter your Member ID');
                memberId.focus();
                return false;
            }
            
            if (!pin.value.trim() || pin.value.length !== 4 || !/^\d+$/.test(pin.value)) {
                e.preventDefault();
                alert('Please enter a valid 4-digit PIN');
                pin.focus();
                return false;
            }
            
            // Show loading state
            const submitBtn = this.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner"></span> Logging in...';
        });
    }
    
    // Password visibility toggle
    const togglePassword = document.querySelector('.toggle-password');
    if (togglePassword) {
        togglePassword.addEventListener('click', function() {
            const passwordInput = this.previousElementSibling;
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            this.classList.toggle('fa-eye');
            this.classList.toggle('fa-eye-slash');
        });
    }
    
    // Store registration form data in localStorage before redirect
    const registerForm = document.querySelector('form[action="{{ url_for('register') }}"]');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            const formData = new FormData(this);
            const formObject = {};
            
            formData.forEach((value, key) => {
                formObject[key] = value;
            });
            
            localStorage.setItem('registrationData', JSON.stringify(formObject));
        });
    }
    
    // Check for registration success message
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('registration') && urlParams.get('registration') === 'success') {
        alert('Your registration has been submitted successfully. You will receive your login credentials shortly.');
    }
});
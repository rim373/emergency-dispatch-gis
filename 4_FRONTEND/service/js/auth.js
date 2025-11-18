const API_URL = 'http://localhost:8000';

document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    try {
        const response = await fetch(`${API_URL}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        if (!response.ok) {
            throw new Error('Login failed');
        }
        
        const data = await response.json();
        
        // Save token and service info
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('serviceId', data.service_id);
        localStorage.setItem('serviceName', data.service_name);
        localStorage.setItem('serviceType', data.service_type);
        
        // Redirect to dashboard
        window.location.href = 'dashboard.html';
        
    } catch (error) {
        document.getElementById('errorMessage').textContent = 'Invalid email or password';
        document.getElementById('errorMessage').style.display = 'block';
    }
});

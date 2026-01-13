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

        console.log('🔍 LOGIN RESPONSE:', data);
        console.log('  access_token:', data.access_token ? 'EXISTS' : 'MISSING');
        console.log('  service_id:', data.service_id);
        console.log('  service_name:', data.service_name);
        console.log('  service_type:', data.service_type);
        console.log('  latitude:', data.latitude, '(type:', typeof data.latitude, ')');
        console.log('  longitude:', data.longitude, '(type:', typeof data.longitude, ')');

        // Save token and service info
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('serviceId', data.service_id);
        localStorage.setItem('serviceName', data.service_name);
        localStorage.setItem('serviceType', data.service_type);
        localStorage.setItem('serviceLat', data.latitude);
        localStorage.setItem('serviceLng', data.longitude);

        console.log('✅ Saved to localStorage:');
        console.log('  serviceLat:', localStorage.getItem('serviceLat'));
        console.log('  serviceLng:', localStorage.getItem('serviceLng'));

        // Delay redirect to see console logs
        setTimeout(() => {
            window.location.href = 'dashboard.html';
        }, 3000); // 3 second delay
        
    } catch (error) {
        document.getElementById('errorMessage').textContent = 'Invalid email or password';
        document.getElementById('errorMessage').style.display = 'block';
    }
});

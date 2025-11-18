// Check authentication
const token = localStorage.getItem('token');
const serviceId = localStorage.getItem('serviceId');
const serviceName = localStorage.getItem('serviceName');
const serviceType = localStorage.getItem('serviceType');

if (!token) {
    window.location.href = 'login.html';
}

document.getElementById('serviceName').textContent = serviceName;
document.getElementById('logoutBtn').addEventListener('click', () => {
    localStorage.clear();
    window.location.href = 'login.html';
});

// WebSocket connection
const socket = io(CONFIG.WEBSOCKET_URL);
let requests = {};

socket.on('connect', () => {
    console.log('Connected to WebSocket');
    document.getElementById('connectionStatus').innerHTML = '🟢 Connected';
    
    socket.emit('register_service', {
        service_id: serviceId,
        service_type: serviceType
    });
});

socket.on('disconnect', () => {
    document.getElementById('connectionStatus').innerHTML = '🔴 Disconnected';
});

socket.on('new_emergency_request', (data) => {
    console.log('New request:', data);
    requests[data.request_id] = data;
    renderRequests();
});

socket.on('request_assigned_to_you', (data) => {
    alert(`Request ${data.request_id} has been assigned to you!`);
    if (requests[data.request_id]) {
        delete requests[data.request_id];
        renderRequests();
    }
});

socket.on('request_assigned_to_other', (data) => {
    if (requests[data.request_id]) {
        delete requests[data.request_id];
        renderRequests();
    }
});

function renderRequests() {
    const container = document.getElementById('requestsList');
    const requestArray = Object.values(requests);
    
    document.getElementById('pendingCount').textContent = requestArray.length;
    
    if (requestArray.length === 0) {
        container.innerHTML = '<p class="no-requests">No pending requests</p>';
        return;
    }
    
    container.innerHTML = requestArray.map(req => `
        <div class="request-card">
            <div class="request-header">
                <span class="request-type">${req.request_type}</span>
                <span class="request-time">${new Date(req.created_at).toLocaleTimeString()}</span>
            </div>
            <div class="request-details">
                <p><strong>Location:</strong> ${req.location.latitude}, ${req.location.longitude}</p>
                <p><strong>Address:</strong> ${req.location.address || 'N/A'}</p>
                ${req.user_note ? `<p><strong>Note:</strong> ${req.user_note}</p>` : ''}
                ${req.user_phone ? `<p><strong>Phone:</strong> ${req.user_phone}</p>` : ''}
            </div>
            <div class="request-actions">
                <button class="btn btn-success" onclick="respondToRequest('${req.request_id}', 'accepted')">Accept</button>
                <button class="btn btn-danger" onclick="respondToRequest('${req.request_id}', 'rejected')">Reject</button>
            </div>
        </div>
    `).join('');
}

async function respondToRequest(requestId, responseType) {
    try {
        const response = await fetch(`${CONFIG.API_URL}/api/requests/respond`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                request_id: requestId,
                response_type: responseType,
                estimated_time_minutes: 15
            })
        });
        
        if (!response.ok) throw new Error('Response failed');
        
        console.log('Response sent successfully');
        
    } catch (error) {
        console.error('Error responding:', error);
        alert('Failed to respond to request');
    }
}

// Load pending requests on startup
async function loadPendingRequests() {
    try {
        const response = await fetch(`${CONFIG.API_URL}/api/requests/pending/by-type/${serviceType}`);
        const data = await response.json();
        
        data.requests.forEach(req => {
            requests[req.request_id] = req;
        });
        
        renderRequests();
    } catch (error) {
        console.error('Error loading requests:', error);
    }
}

loadPendingRequests();

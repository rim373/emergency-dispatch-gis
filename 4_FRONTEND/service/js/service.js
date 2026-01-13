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
let reserveRequests = {};

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
    showNotification(`✅ Request ${data.request_id} assigned to you!`, 'success');
    playNotificationSound();

    if (requests[data.request_id]) {
        const requestData = requests[data.request_id];

        // Show route visualization and car animation
        if (typeof showRouteAndAnimate === 'function') {
            // Get service location from localStorage or API
            const serviceLat = parseFloat(localStorage.getItem('serviceLat')) || null;
            const serviceLng = parseFloat(localStorage.getItem('serviceLng')) || null;

            if (serviceLat && serviceLng && requestData.location) {
                showRouteAndAnimate({
                    fromLat: serviceLat,
                    fromLng: serviceLng,
                    toLat: requestData.location.latitude,
                    toLng: requestData.location.longitude,
                    serviceType: serviceType,
                    routeColor: getServiceColor(serviceType),
                    animationDuration: 15000, // 15 seconds animation
                    onComplete: () => {
                        console.log('Route animation completed for', data.request_id);
                    }
                }).catch(err => {
                    console.error('Error displaying route:', err);
                });
            } else {
                console.warn('Service or request location not available for route visualization');
            }
        }

        delete requests[data.request_id];
        renderRequests();
    }

    // Also remove from reserve if it was there
    if (reserveRequests[data.request_id]) {
        delete reserveRequests[data.request_id];
        renderReserveRequests();
    }
});

// Get color for service type
function getServiceColor(type) {
    const colors = {
        'ambulance': '#e53935',
        'hospital': '#e53935',
        'fire': '#fb8c00',
        'police': '#1e88e5'
    };
    return colors[type.toLowerCase()] || '#2196F3';
}

socket.on('request_reserve_standby', (data) => {
    console.log('Reserve notification:', data);
    showNotification(
        `⏸️ Request ${data.request_id}: ${data.message}`,
        'warning'
    );

    // Move from active to reserve
    if (requests[data.request_id]) {
        delete requests[data.request_id];
        renderRequests();
    }

    // Add to reserve list
    reserveRequests[data.request_id] = {
        ...data,
        timestamp: new Date().toISOString()
    };
    renderReserveRequests();
});

socket.on('request_assigned_to_other', (data) => {
    if (requests[data.request_id]) {
        delete requests[data.request_id];
        renderRequests();
    }
});

socket.on('request_taken', (data) => {
    if (requests[data.request_id]) {
        delete requests[data.request_id];
        renderRequests();
    }
});

socket.on('request_unavailable', (data) => {
    if (requests[data.request_id]) {
        delete requests[data.request_id];
        renderRequests();
    }
    showNotification(`Request ${data.request_id}: ${data.reason}`, 'info');
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

// Render reserve/standby requests
function renderReserveRequests() {
    const container = document.getElementById('reserveList');
    if (!container) return; // Container might not exist in older HTML

    const reserveArray = Object.values(reserveRequests);

    if (reserveArray.length === 0) {
        container.innerHTML = '<p class="no-requests">No reserve requests</p>';
        return;
    }

    container.innerHTML = reserveArray.map(req => `
        <div class="request-card reserve-card">
            <div class="request-header">
                <span class="badge badge-warning">⏸️ RESERVE #${req.reserve_position}</span>
                <span class="request-time">${new Date(req.timestamp).toLocaleTimeString()}</span>
            </div>
            <div class="request-details">
                <p><strong>Request ID:</strong> ${req.request_id}</p>
                <p><strong>Handled by:</strong> ${req.assigned_to_service}</p>
                <p><strong>Your Distance:</strong> ${req.your_distance_km?.toFixed(2)} km</p>
                <p><strong>Assigned Distance:</strong> ${req.assigned_distance_km?.toFixed(2)} km</p>
                <p class="reserve-message">${req.message}</p>
            </div>
            <div class="request-actions">
                <button class="btn btn-secondary btn-sm" onclick="removeReserve('${req.request_id}')">Dismiss</button>
            </div>
        </div>
    `).join('');
}

// Remove reserve request from list
function removeReserve(requestId) {
    if (reserveRequests[requestId]) {
        delete reserveRequests[requestId];
        renderReserveRequests();
    }
}

// Show notification
function showNotification(message, type = 'info') {
    const notificationArea = document.getElementById('notificationArea');
    if (!notificationArea) {
        // Fallback to alert if no notification area
        alert(message);
        return;
    }

    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()">×</button>
    `;

    notificationArea.appendChild(notification);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Play notification sound
function playNotificationSound() {
    try {
        const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBTGH0fPTgjMGHm7A7+OZURE=');
        audio.volume = 0.3;
        audio.play().catch(err => console.log('Audio play failed:', err));
    } catch (err) {
        console.log('Could not play notification sound');
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

// Main user interface logic
let selectedEmergencyType = null;

// Emergency type selection
document.querySelectorAll('.emergency-card').forEach(card => {
    card.addEventListener('click', () => {
        document.querySelectorAll('.emergency-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        selectedEmergencyType = card.dataset.type;
        document.getElementById('submitRequestBtn').disabled = false;
    });
});

// Submit request
document.getElementById('submitRequestBtn').addEventListener('click', submitRequest);

async function submitRequest() {
    if (!currentLocation || !selectedEmergencyType) {
        alert('Please select emergency type and get your location first');
        return;
    }
    
    const requestData = {
        request_type: selectedEmergencyType,
        location: currentLocation,
        user_phone: document.getElementById('userPhone').value || null,
        user_note: document.getElementById('userNote').value || null
    };
    
    document.getElementById('submitRequestBtn').disabled = true;
    document.getElementById('submitRequestBtn').textContent = 'Submitting...';
    
    try {
        const response = await fetch(`${CONFIG.API_URL}/api/requests/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) throw new Error('Failed to create request');
        
        const data = await response.json();
        currentRequestId = data.request_id;
        
        // Register with WebSocket
        socket.emit('register_user', {
            user_id: `USER-${currentRequestId}`,
            request_id: currentRequestId
        });
        
        showStatus(data);
        
    } catch (error) {
        console.error('Error submitting request:', error);
        alert('Failed to submit request. Please try again.');
        document.getElementById('submitRequestBtn').disabled = false;
        document.getElementById('submitRequestBtn').textContent = 'Submit Emergency Request';
    }
}

function showStatus(data) {
    document.getElementById('requestForm').style.display = 'none';
    document.getElementById('statusDisplay').style.display = 'block';
    
    document.getElementById('requestId').textContent = data.request_id;
    document.getElementById('requestType').textContent = data.request_type.toUpperCase();
    document.getElementById('requestStatus').textContent = 'Waiting for service providers to respond...';
    document.getElementById('statusBadge').textContent = data.status.toUpperCase();
    document.getElementById('statusBadge').className = 'status-badge status-pending';
}

function showAssignedService(data) {
    document.getElementById('statusBadge').textContent = 'ACCEPTED';
    document.getElementById('statusBadge').className = 'status-badge status-accepted';
    document.getElementById('requestStatus').textContent = 'Service assigned and on the way!';
    
    document.getElementById('assignedServiceInfo').style.display = 'block';
    document.getElementById('serviceName').textContent = data.service_name || 'N/A';
    document.getElementById('servicePhone').textContent = data.service_phone || 'N/A';
    document.getElementById('serviceETA').textContent = data.estimated_arrival_time ? 
        `${data.estimated_arrival_time} minutes` : 'N/A';
    document.getElementById('serviceDistance').textContent = data.distance_km ? 
        `${data.distance_km} km` : 'N/A';
}

document.getElementById('newRequestBtn').addEventListener('click', () => {
    location.reload();
});


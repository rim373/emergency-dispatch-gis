// WebSocket connection management
let socket;
let currentRequestId = null;

function connectWebSocket() {
    socket = io(CONFIG.WEBSOCKET_URL);
    
    socket.on('connect', () => {
        console.log('WebSocket connected');
        document.getElementById('connectionStatus').textContent = '🟢 Connected';
        document.getElementById('connectionStatus').style.color = '#4caf50';
        
        if (currentRequestId) {
            socket.emit('register_user', {
                user_id: `USER-${currentRequestId}`,
                request_id: currentRequestId
            });
        }
    });
    
    socket.on('disconnect', () => {
        console.log('WebSocket disconnected');
        document.getElementById('connectionStatus').textContent = '🔴 Disconnected';
        document.getElementById('connectionStatus').style.color = '#f44336';
    });
    
    socket.on('registration_success', (data) => {
        console.log('Registration successful:', data);
    });
    
    socket.on('request_assigned', (data) => {
        console.log('Request assigned:', data);
        showAssignedService(data);
    });
    
    socket.on('pong', (data) => {
        console.log('Pong received:', data);
    });
}

connectWebSocket();

// Ping every 25 seconds
setInterval(() => {
    if (socket && socket.connected) {
        socket.emit('ping', { timestamp: new Date().toISOString() });
    }
}, 25000);

// Geolocation handling
let currentLocation = null;

document.getElementById('getLocationBtn').addEventListener('click', getUserLocation);

function getUserLocation() {
    if (!navigator.geolocation) {
        alert('Geolocation is not supported by your browser');
        return;
    }
    
    document.getElementById('getLocationBtn').textContent = '📍 Getting location...';
    document.getElementById('getLocationBtn').disabled = true;
    
    navigator.geolocation.getCurrentPosition(
        position => {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            
            currentLocation = { latitude: lat, longitude: lng };
            
            addUserMarker(lat, lng);
            updateLocationDisplay(lat, lng);
            
            document.getElementById('getLocationBtn').textContent = '✅ Location Found';
            document.getElementById('requestForm').style.display = 'block';
        },
        error => {
            console.error('Geolocation error:', error);
            alert('Could not get your location. Please enable location services.');
            document.getElementById('getLocationBtn').textContent = '📍 Get My Location';
            document.getElementById('getLocationBtn').disabled = false;
        }
    );
}

function updateLocationDisplay(lat, lng) {
    document.getElementById('locationInfo').style.display = 'block';
    document.getElementById('lat').textContent = lat.toFixed(6);
    document.getElementById('lng').textContent = lng.toFixed(6);
    
    // Reverse geocoding (optional - using Nominatim)
    fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json`)
        .then(res => res.json())
        .then(data => {
            document.getElementById('address').textContent = data.display_name || 'Address not found';
            currentLocation.address = data.display_name;
        })
        .catch(() => {
            document.getElementById('address').textContent = 'Address lookup failed';
        });
}

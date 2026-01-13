/**
 * Route Visualization and Car Animation Module
 * Displays route path between service provider and user with animated car movement
 */

// Global variables for route management
let activeRoute = null;
let activeRouteLine = null;
let carMarker = null;
let animationInterval = null;
let currentAnimationIndex = 0;
let routeCoordinates = [];

/**
 * Fetch route from OSRM API
 * @param {number} fromLat - Service provider latitude
 * @param {number} fromLng - Service provider longitude
 * @param {number} toLat - User latitude
 * @param {number} toLng - User longitude
 * @returns {Promise<Object>} Route data with coordinates and metadata
 */
async function fetchRoute(fromLat, fromLng, toLat, toLng) {
    try {
        // Using public OSRM demo server (replace with your own in production)
        const osrmUrl = `https://router.project-osrm.org/route/v1/driving/${fromLng},${fromLat};${toLng},${toLat}?overview=full&geometries=geojson&steps=true`;

        const response = await fetch(osrmUrl);

        if (!response.ok) {
            throw new Error(`OSRM API error: ${response.status}`);
        }

        const data = await response.json();

        if (!data.routes || data.routes.length === 0) {
            throw new Error('No route found');
        }

        const route = data.routes[0];

        // Convert coordinates from [lng, lat] to [lat, lng]
        let coordinates = route.geometry.coordinates.map(coord => [coord[1], coord[0]]);

        // IMPORTANT: Ensure route ends at EXACT destination coordinates
        // OSRM may snap to nearest road, so force last point to be exact destination
        const lastCoord = coordinates[coordinates.length - 1];
        const distanceToDestination = calculateStraightLineDistance(
            lastCoord[0], lastCoord[1], toLat, toLng
        );

        // If last coordinate is not exactly at destination (more than 10 meters away), add destination point
        if (distanceToDestination > 0.01) { // 0.01 km = 10 meters
            console.log(`📍 Route endpoint is ${(distanceToDestination * 1000).toFixed(0)}m from destination, adding exact destination point`);
            coordinates.push([toLat, toLng]);
        }

        return {
            coordinates: coordinates,
            distance: (route.distance / 1000).toFixed(2), // km
            duration: Math.round(route.duration / 60), // minutes
            steps: route.legs[0].steps,
            geometry: route.geometry
        };
    } catch (error) {
        console.error('Error fetching route from OSRM:', error);

        // Fallback: straight line if OSRM fails
        console.warn('Using straight line as fallback');
        return {
            coordinates: [[fromLat, fromLng], [toLat, toLng]],
            distance: calculateStraightLineDistance(fromLat, fromLng, toLat, toLng).toFixed(2),
            duration: null,
            steps: [],
            geometry: null,
            fallback: true
        };
    }
}

/**
 * Calculate straight-line distance using Haversine formula (fallback)
 * @param {number} lat1
 * @param {number} lng1
 * @param {number} lat2
 * @param {number} lng2
 * @returns {number} Distance in kilometers
 */
function calculateStraightLineDistance(lat1, lng1, lat2, lng2) {
    const R = 6371; // Earth's radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLng / 2) * Math.sin(dLng / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

/**
 * Display route on map with styled polyline
 * @param {Array} coordinates - Array of [lat, lng] coordinates
 * @param {string} color - Route line color (default: blue)
 * @returns {L.Polyline} Leaflet polyline object
 */
function displayRoute(coordinates, color = '#2196F3') {
    // Remove existing route if any
    clearRoute();

    // Create styled polyline
    activeRouteLine = L.polyline(coordinates, {
        color: color,
        weight: 5,
        opacity: 0.7,
        smoothFactor: 1,
        className: 'route-line'
    }).addTo(map);

    // Add decorative arrows to show direction
    const decorator = L.polylineDecorator(activeRouteLine, {
        patterns: [
            {
                offset: '10%',
                repeat: '15%',
                symbol: L.Symbol.arrowHead({
                    pixelSize: 10,
                    polygon: false,
                    pathOptions: {
                        stroke: true,
                        weight: 2,
                        color: color,
                        opacity: 0.7
                    }
                })
            }
        ]
    }).addTo(map);

    // Store decorator reference for cleanup
    activeRouteLine._decorator = decorator;

    // Fit map to show entire route
    const bounds = L.latLngBounds(coordinates);
    map.fitBounds(bounds, { padding: [50, 50] });

    return activeRouteLine;
}

/**
 * Create animated car marker
 * @param {Array} startPosition - Initial [lat, lng] position
 * @param {string} serviceType - Type of service (ambulance, fire, police)
 * @returns {L.Marker} Leaflet marker object
 */
function createCarMarker(startPosition, serviceType = 'ambulance') {
    // Choose emoji based on service type
    const serviceEmojis = {
        'ambulance': '🚑',
        'hospital': '🚑',
        'fire': '🚒',
        'police': '🚓'
    };

    const emoji = serviceEmojis[serviceType.toLowerCase()] || '🚗';

    // Create custom car icon
    const carIcon = L.divIcon({
        className: 'car-marker',
        html: `<div style="
            font-size: 30px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            transform: rotate(0deg);
            transition: transform 0.3s ease;
        ">${emoji}</div>`,
        iconSize: [30, 30],
        iconAnchor: [15, 15]
    });

    carMarker = L.marker(startPosition, {
        icon: carIcon,
        zIndexOffset: 1000 // Ensure car is above route
    }).addTo(map);

    return carMarker;
}

/**
 * Animate car movement along route
 * @param {Array} coordinates - Route coordinates
 * @param {number} duration - Total animation duration in milliseconds
 * @param {Function} onComplete - Callback when animation completes
 */
function animateCarMovement(coordinates, duration = 10000, onComplete = null) {
    if (!carMarker || coordinates.length < 2) {
        console.error('Cannot animate: invalid car marker or coordinates');
        return;
    }

    // Stop any existing animation
    stopAnimation();

    routeCoordinates = coordinates;
    currentAnimationIndex = 0;

    // Calculate delay between steps for smooth animation
    const totalSteps = coordinates.length;
    const stepDelay = duration / totalSteps;

    // Animation loop
    animationInterval = setInterval(() => {
        if (currentAnimationIndex >= totalSteps - 1) {
            // Animation complete
            stopAnimation();
            if (onComplete) onComplete();
            return;
        }

        // Move car to next position
        const currentPos = routeCoordinates[currentAnimationIndex];
        const nextPos = routeCoordinates[currentAnimationIndex + 1];

        // Calculate rotation angle for car icon
        const angle = calculateBearing(currentPos[0], currentPos[1], nextPos[0], nextPos[1]);

        // Update car position
        carMarker.setLatLng(nextPos);

        // Rotate car icon to face direction of travel
        const carElement = carMarker.getElement();
        if (carElement) {
            const iconDiv = carElement.querySelector('div');
            if (iconDiv) {
                iconDiv.style.transform = `rotate(${angle}deg)`;
            }
        }

        currentAnimationIndex++;

        // Pan map to follow car (optional, can be disabled)
        // map.panTo(nextPos, { animate: true, duration: stepDelay / 1000 });

    }, stepDelay);
}

/**
 * Calculate bearing/angle between two coordinates
 * @param {number} lat1
 * @param {number} lng1
 * @param {number} lat2
 * @param {number} lng2
 * @returns {number} Bearing in degrees
 */
function calculateBearing(lat1, lng1, lat2, lng2) {
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const lat1Rad = lat1 * Math.PI / 180;
    const lat2Rad = lat2 * Math.PI / 180;

    const y = Math.sin(dLng) * Math.cos(lat2Rad);
    const x = Math.cos(lat1Rad) * Math.sin(lat2Rad) -
              Math.sin(lat1Rad) * Math.cos(lat2Rad) * Math.cos(dLng);

    const bearing = Math.atan2(y, x) * 180 / Math.PI;
    return (bearing + 360) % 360; // Normalize to 0-360
}

/**
 * Stop car animation
 */
function stopAnimation() {
    if (animationInterval) {
        clearInterval(animationInterval);
        animationInterval = null;
    }
}

/**
 * Clear route from map
 */
function clearRoute() {
    if (activeRouteLine) {
        // Remove decorator if exists
        if (activeRouteLine._decorator) {
            activeRouteLine._decorator.remove();
        }
        activeRouteLine.remove();
        activeRouteLine = null;
    }
}

/**
 * Clear car marker from map
 */
function clearCarMarker() {
    stopAnimation();
    if (carMarker) {
        carMarker.remove();
        carMarker = null;
    }
}

/**
 * Clear all route visualizations
 */
function clearAllRouteVisualizations() {
    clearRoute();
    clearCarMarker();
    routeCoordinates = [];
    currentAnimationIndex = 0;
}

/**
 * Main function: Show route and animate car movement
 * @param {Object} params - Parameters object
 * @param {number} params.fromLat - Service provider latitude
 * @param {number} params.fromLng - Service provider longitude
 * @param {number} params.toLat - User latitude
 * @param {number} params.toLng - User longitude
 * @param {string} params.serviceType - Service type (ambulance, fire, police)
 * @param {string} params.routeColor - Route line color (optional)
 * @param {number} params.animationDuration - Animation duration in ms (optional, default: 10000)
 * @param {Function} params.onComplete - Callback when animation completes (optional)
 */
async function showRouteAndAnimate(params) {
    const {
        fromLat,
        fromLng,
        toLat,
        toLng,
        serviceType = 'ambulance',
        routeColor = '#2196F3',
        animationDuration = 10000,
        onComplete = null
    } = params;

    try {
        console.log(`📍 Fetching route from [${fromLat}, ${fromLng}] to [${toLat}, ${toLng}]`);

        // Show loading indicator (optional)
        if (typeof showNotification === 'function') {
            showNotification('🗺️ Calculating route...', 'info');
        }

        // Fetch route data
        const routeData = await fetchRoute(fromLat, fromLng, toLat, toLng);

        console.log(`✅ Route fetched: ${routeData.distance} km, ${routeData.duration || 'N/A'} min`);

        // Display route on map
        displayRoute(routeData.coordinates, routeColor);

        // Create car at starting position
        createCarMarker([fromLat, fromLng], serviceType);

        // Show route info notification
        if (typeof showNotification === 'function') {
            const routeInfo = routeData.fallback
                ? `📏 Distance: ${routeData.distance} km (straight line)`
                : `📏 Distance: ${routeData.distance} km • ⏱️ ETA: ${routeData.duration} min`;

            showNotification(routeInfo, 'success', 5000);
        }

        // Start animation after a brief delay
        setTimeout(() => {
            animateCarMovement(routeData.coordinates, animationDuration, () => {
                console.log('🏁 Car animation completed');
                if (typeof showNotification === 'function') {
                    showNotification('🏁 Service arrived at destination!', 'success');
                }
                if (onComplete) onComplete();
            });
        }, 500);

        // Store route data
        activeRoute = routeData;

        return routeData;

    } catch (error) {
        console.error('Error showing route and animation:', error);
        // Only show notification if function exists (service dashboard has it, user interface doesn't)
        if (typeof showNotification === 'function') {
            showNotification('❌ Failed to display route', 'error');
        }
        throw error;
    }
}

/**
 * Pause/Resume animation
 */
function toggleAnimation() {
    if (animationInterval) {
        stopAnimation();
        return false; // Paused
    } else if (routeCoordinates.length > 0 && currentAnimationIndex < routeCoordinates.length - 1) {
        // Resume from current position
        animateCarMovement(
            routeCoordinates.slice(currentAnimationIndex),
            5000 // Remaining duration
        );
        return true; // Playing
    }
    return false;
}

/**
 * Get current route info
 * @returns {Object|null} Active route data
 */
function getActiveRoute() {
    return activeRoute;
}

// Note: Make sure Leaflet.PolylineDecorator plugin is loaded for arrow decorations
// Add this to your HTML: <script src="https://cdn.jsdelivr.net/npm/leaflet-polylinedecorator@1.6.0/dist/leaflet.polylineDecorator.min.js"></script>
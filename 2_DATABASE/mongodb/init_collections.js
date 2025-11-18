// Emergency Response System - MongoDB Initialization
// Run this: mongosh < init_collections.js

// Switch to database
use emergency_response_logs;

// Create collections
db.createCollection("request_logs");
db.createCollection("service_logs");
db.createCollection("websocket_events");
db.createCollection("system_logs");

// Create indexes
db.request_logs.createIndex({ "request_id": 1 });
db.request_logs.createIndex({ "timestamp": -1 });
db.request_logs.createIndex({ "request_type": 1 });

db.service_logs.createIndex({ "service_id": 1 });
db.service_logs.createIndex({ "timestamp": -1 });
db.service_logs.createIndex({ "action": 1 });

db.websocket_events.createIndex({ "event_type": 1 });
db.websocket_events.createIndex({ "timestamp": -1 });

db.system_logs.createIndex({ "level": 1 });
db.system_logs.createIndex({ "timestamp": -1 });

// Insert sample log
db.system_logs.insertOne({
    level: "info",
    message: "MongoDB initialized successfully",
    timestamp: new Date(),
    component: "database"
});

print("✅ MongoDB collections and indexes created successfully!");
print("");
print("📊 Collections:");
print("  - request_logs");
print("  - service_logs");
print("  - websocket_events");
print("  - system_logs");
print("");

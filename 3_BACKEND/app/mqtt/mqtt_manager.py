"""
MQTT Manager for Emergency Response System
Handles MQTT pub/sub messaging for efficient service communication
"""

import json
import logging
import asyncio
from typing import Dict, Callable, Optional, Any
from datetime import datetime
import paho.mqtt.client as mqtt
from app.config import Config

logger = logging.getLogger(__name__)


class MQTTManager:
    """
    Manages MQTT connections and messaging for service providers
    Uses pub/sub pattern for scalable, efficient communication
    """

    # MQTT Topics
    TOPIC_NEW_REQUEST = "emergency/requests/new/{service_type}"  # ambulance, fire, police
    TOPIC_REQUEST_ASSIGNED = "emergency/requests/assigned/{request_id}"
    TOPIC_REQUEST_RESERVE = "emergency/requests/reserve/{request_id}"
    TOPIC_REQUEST_CANCELLED = "emergency/requests/cancelled/{request_id}"
    TOPIC_SERVICE_STATUS = "emergency/services/status/{service_id}"
    TOPIC_SYSTEM_BROADCAST = "emergency/system/broadcast"

    def __init__(self):
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self.message_callbacks: Dict[str, Callable] = {}
        self.service_subscriptions: Dict[str, list] = {}  # service_id -> list of topics

    async def connect(self):
        """Connect to Mosquitto MQTT broker"""
        try:
            # Create MQTT client with clean session
            self.client = mqtt.Client(
                client_id=f"emergency_backend_{datetime.now().timestamp()}",
                clean_session=True,
                protocol=mqtt.MQTTv311
            )

            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message

            # Connect to broker
            self.client.connect(
                Config.MQTT_BROKER_HOST,
                Config.MQTT_BROKER_PORT,
                keepalive=60
            )

            # Start network loop in background
            self.client.loop_start()

            logger.info(f"MQTT client connecting to {Config.MQTT_BROKER_HOST}:{Config.MQTT_BROKER_PORT}")

            # Wait for connection
            for _ in range(10):  # 5 seconds timeout
                if self.connected:
                    break
                await asyncio.sleep(0.5)

            if not self.connected:
                raise Exception("MQTT connection timeout")

            return True

        except Exception as e:
            logger.error(f"MQTT connection error: {e}")
            return False

    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to broker"""
        if rc == 0:
            self.connected = True
            logger.info("MQTT connected successfully")

            # Subscribe to system broadcast
            self.client.subscribe(self.TOPIC_SYSTEM_BROADCAST, qos=1)
        else:
            logger.error(f"MQTT connection failed with code {rc}")
            self.connected = False

    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from broker"""
        self.connected = False
        logger.warning(f"MQTT disconnected with code {rc}")

        if rc != 0:
            logger.info("Unexpected disconnect, will attempt reconnect")

    def _on_message(self, client, userdata, msg):
        """Callback when message received"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())

            logger.debug(f"MQTT message received on {topic}: {payload}")

            # Call registered callback if exists
            if topic in self.message_callbacks:
                asyncio.create_task(self.message_callbacks[topic](topic, payload))

            # Call wildcard callbacks
            for callback_topic, callback in self.message_callbacks.items():
                if self._topic_matches(callback_topic, topic):
                    asyncio.create_task(callback(topic, payload))

        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    def _topic_matches(self, pattern: str, topic: str) -> bool:
        """Check if topic matches pattern (supports + and # wildcards)"""
        pattern_parts = pattern.split('/')
        topic_parts = topic.split('/')

        if len(pattern_parts) > len(topic_parts):
            return False

        for i, pattern_part in enumerate(pattern_parts):
            if pattern_part == '#':
                return True
            if pattern_part == '+':
                continue
            if i >= len(topic_parts) or pattern_part != topic_parts[i]:
                return False

        return len(pattern_parts) == len(topic_parts)

    async def publish(
        self,
        topic: str,
        payload: Dict[str, Any],
        qos: int = 1,
        retain: bool = False
    ) -> bool:
        """
        Publish message to MQTT topic

        Args:
            topic: MQTT topic
            payload: Message payload (will be JSON serialized)
            qos: Quality of Service (0, 1, or 2)
            retain: Whether to retain message on broker
        """
        try:
            if not self.connected:
                logger.warning("MQTT not connected, cannot publish")
                return False

            message = json.dumps(payload, default=str)
            result = self.client.publish(topic, message, qos=qos, retain=retain)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published to {topic}: {payload}")
                return True
            else:
                logger.error(f"Failed to publish to {topic}: {result.rc}")
                return False

        except Exception as e:
            logger.error(f"Error publishing to MQTT: {e}")
            return False

    async def subscribe(self, topic: str, callback: Optional[Callable] = None, qos: int = 1):
        """
        Subscribe to MQTT topic

        Args:
            topic: MQTT topic (supports wildcards + and #)
            callback: Async function to call when message received
            qos: Quality of Service
        """
        try:
            if not self.connected:
                logger.warning("MQTT not connected, cannot subscribe")
                return False

            result = self.client.subscribe(topic, qos=qos)

            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Subscribed to {topic}")

                if callback:
                    self.message_callbacks[topic] = callback

                return True
            else:
                logger.error(f"Failed to subscribe to {topic}")
                return False

        except Exception as e:
            logger.error(f"Error subscribing to MQTT: {e}")
            return False

    async def unsubscribe(self, topic: str):
        """Unsubscribe from MQTT topic"""
        try:
            if self.connected:
                self.client.unsubscribe(topic)
                if topic in self.message_callbacks:
                    del self.message_callbacks[topic]
                logger.info(f"Unsubscribed from {topic}")

        except Exception as e:
            logger.error(f"Error unsubscribing from MQTT: {e}")

    async def publish_new_request(self, service_type: str, request_data: Dict[str, Any]):
        """Publish new emergency request to services"""
        topic = self.TOPIC_NEW_REQUEST.format(service_type=service_type)
        await self.publish(topic, request_data, qos=1)

    async def publish_request_assigned(self, request_id: str, assignment_data: Dict[str, Any]):
        """Publish request assignment notification"""
        topic = self.TOPIC_REQUEST_ASSIGNED.format(request_id=request_id)
        await self.publish(topic, assignment_data, qos=1)

    async def publish_reserve_notification(
        self,
        request_id: str,
        reserve_data: Dict[str, Any]
    ):
        """
        Publish reserve/standby notification to services that accepted but weren't selected

        Args:
            request_id: Request ID
            reserve_data: Contains service_ids, assigned_service info, distances, etc.
        """
        topic = self.TOPIC_REQUEST_RESERVE.format(request_id=request_id)
        await self.publish(topic, reserve_data, qos=1)

        # Also send individual notifications to each reserve service
        for service_id in reserve_data.get('reserve_service_ids', []):
            service_topic = self.TOPIC_SERVICE_STATUS.format(service_id=service_id)
            await self.publish(
                service_topic,
                {
                    "event": "request_reserve",
                    "request_id": request_id,
                    "assigned_to": reserve_data.get('assigned_service_name'),
                    "your_distance_km": reserve_data.get('distances', {}).get(service_id),
                    "message": f"Request handled by {reserve_data.get('assigned_service_name')} - You're on reserve"
                },
                qos=1
            )

    async def publish_request_cancelled(self, request_id: str, cancellation_data: Dict[str, Any]):
        """Publish request cancellation"""
        topic = self.TOPIC_REQUEST_CANCELLED.format(request_id=request_id)
        await self.publish(topic, cancellation_data, qos=1)

    async def subscribe_service(self, service_id: str, service_type: str, callback: Callable):
        """
        Subscribe service to relevant topics

        Args:
            service_id: Service ID
            service_type: hospital, fire_station, or police_station
            callback: Async callback for messages
        """
        # Map service type to request type
        type_mapping = {
            "hospital": "ambulance",
            "fire_station": "fire",
            "police_station": "police"
        }
        request_type = type_mapping.get(service_type, service_type)

        # Subscribe to new requests for this service type
        new_request_topic = self.TOPIC_NEW_REQUEST.format(service_type=request_type)
        await self.subscribe(new_request_topic, callback)

        # Subscribe to service-specific status
        service_topic = self.TOPIC_SERVICE_STATUS.format(service_id=service_id)
        await self.subscribe(service_topic, callback)

        # Track subscriptions
        self.service_subscriptions[service_id] = [new_request_topic, service_topic]

        logger.info(f"Service {service_id} subscribed to MQTT topics")

    async def unsubscribe_service(self, service_id: str):
        """Unsubscribe service from all topics"""
        if service_id in self.service_subscriptions:
            for topic in self.service_subscriptions[service_id]:
                await self.unsubscribe(topic)
            del self.service_subscriptions[service_id]
            logger.info(f"Service {service_id} unsubscribed from MQTT")

    async def disconnect(self):
        """Disconnect from MQTT broker"""
        try:
            if self.client:
                self.client.loop_stop()
                self.client.disconnect()
                self.connected = False
                logger.info("MQTT disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting MQTT: {e}")


# Global MQTT manager instance
mqtt_manager = MQTTManager()


async def get_mqtt_manager() -> MQTTManager:
    """Get MQTT manager instance (dependency injection)"""
    if not mqtt_manager.connected:
        await mqtt_manager.connect()
    return mqtt_manager
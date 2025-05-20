import json
import os
import pika
import logging
from typing import Dict, Any, Callable

logger = logging.getLogger(__name__)

class EventBus:
    """Event bus for publishing and consuming messages."""
    
    def __init__(self):
        self.host = os.environ.get("RABBITMQ_HOST", "rabbitmq")
        self.connection = None
        self.channel = None
        self.exchange_name = "dididentity"
        self.subscribers = {}
        
    async def connect(self):
        """Connect to RabbitMQ."""
        try:
            # Create connection parameters
            parameters = pika.ConnectionParameters(
                host=self.host,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            
            # Connect to RabbitMQ
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare the exchange
            self.channel.exchange_declare(
                exchange=self.exchange_name,
                exchange_type='topic',
                durable=True
            )
            
            logger.info(f"Connected to RabbitMQ at {self.host}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            return False
    
    async def publish(self, event_type: str, data: Dict[str, Any]):
        """Publish an event to the event bus."""
        if not self.connection or self.connection.is_closed:
            await self.connect()
            
        try:
            # Convert data to JSON
            message = json.dumps(data)
            
            # Publish message
            self.channel.basic_publish(
                exchange=self.exchange_name,
                routing_key=event_type,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )
            
            logger.info(f"Published event {event_type}: {message}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {str(e)}")
            return False
    
    async def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to an event type."""
        if not self.connection or self.connection.is_closed:
            await self.connect()
            
        try:
            # Declare a queue for this service
            service_name = os.environ.get("SERVICE_NAME", "did-service")
            queue_name = f"{service_name}.{event_type}"
            
            self.channel.queue_declare(queue=queue_name, durable=True)
            self.channel.queue_bind(
                exchange=self.exchange_name,
                queue=queue_name,
                routing_key=event_type
            )
            
            # Store callback
            self.subscribers[event_type] = callback
            
            # Set up consumer
            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=self._on_message,
                auto_ack=False
            )
            
            logger.info(f"Subscribed to event {event_type} on queue {queue_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to subscribe to event {event_type}: {str(e)}")
            return False
    
    def _on_message(self, channel, method, properties, body):
        """Handle incoming messages."""
        try:
            # Parse message
            message = json.loads(body)
            event_type = method.routing_key
            
            # Call callback if exists
            if event_type in self.subscribers:
                self.subscribers[event_type](message)
                
            # Acknowledge message
            channel.basic_ack(delivery_tag=method.delivery_tag)
            
            logger.info(f"Processed event {event_type}")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            # Reject message and requeue
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    async def start_consuming(self):
        """Start consuming messages."""
        if not self.connection or self.connection.is_closed:
            await self.connect()
            
        try:
            logger.info("Starting to consume messages")
            self.channel.start_consuming()
        except Exception as e:
            logger.error(f"Error consuming messages: {str(e)}")
    
    async def close(self):
        """Close connection to RabbitMQ."""
        try:
            if self.connection and not self.connection.is_closed:
                logger.info("Closing connection to RabbitMQ")
                self.connection.close()
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {str(e)}")

# Create a singleton instance
event_bus = EventBus() 
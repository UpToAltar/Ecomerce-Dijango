import json
import logging
import pika
import os

logger = logging.getLogger(__name__)


class RabbitMQClient:
    """RabbitMQ publisher for auth events."""

    def __init__(self):
        self.host = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
        self.port = int(os.environ.get('RABBITMQ_PORT', 5672))
        self.user = os.environ.get('RABBITMQ_USER', 'guest')
        self.password = os.environ.get('RABBITMQ_PASSWORD', 'guest')

    def _get_connection(self):
        credentials = pika.PlainCredentials(self.user, self.password)
        parameters = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            credentials=credentials,
        )
        return pika.BlockingConnection(parameters)

    def publish(self, exchange, routing_key, message):
        """Publish a message to RabbitMQ."""
        try:
            connection = self._get_connection()
            channel = connection.channel()
            channel.exchange_declare(exchange=exchange, exchange_type='topic', durable=True)
            channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json',
                ),
            )
            connection.close()
            logger.info(f'Published message to {exchange}/{routing_key}')
        except Exception as e:
            logger.error(f'Failed to publish message: {e}')

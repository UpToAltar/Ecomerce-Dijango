"""RabbitMQ helpers for shipping-service."""
import json
import pika
from django.conf import settings


def _get_connection():
    credentials = pika.PlainCredentials(
        settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD
    )
    params = pika.ConnectionParameters(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300,
    )
    return pika.BlockingConnection(params)


def publish_event(exchange: str, routing_key: str, payload: dict):
    """Generic event publisher to a topic exchange."""
    try:
        conn = _get_connection()
        channel = conn.channel()
        channel.exchange_declare(
            exchange=exchange,
            exchange_type='topic',
            durable=True,
        )
        channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=json.dumps(payload),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json',
            ),
        )
        conn.close()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f'[RabbitMQ] publish_event error: {e}')

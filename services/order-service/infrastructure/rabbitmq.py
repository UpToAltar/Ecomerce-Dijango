"""RabbitMQ publisher/consumer helpers for order-service."""
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


def setup_dlx_topology(channel):
    """Declare DLX exchange + queues for order expiry pattern."""
    # Dead-letter exchange — receives expired messages
    channel.exchange_declare(
        exchange='order.dlx',
        exchange_type='direct',
        durable=True,
    )
    # Main queue where expired messages land (DLX consumer reads this)
    channel.queue_declare(
        queue='order.expired',
        durable=True,
    )
    channel.queue_bind(
        queue='order.expired',
        exchange='order.dlx',
        routing_key='order.expired',
    )
    # Holding queue: messages sit here for TTL=15min, then go to DLX
    FIFTEEN_MIN_MS = 15 * 60 * 1000
    channel.queue_declare(
        queue='order.expiry_hold',
        durable=True,
        arguments={
            'x-message-ttl': FIFTEEN_MIN_MS,
            'x-dead-letter-exchange': 'order.dlx',
            'x-dead-letter-routing-key': 'order.expired',
        },
    )


def publish_order_expiry(order_id: str):
    """Publish order to holding queue — will be dead-lettered after 15 min."""
    try:
        conn = _get_connection()
        channel = conn.channel()
        setup_dlx_topology(channel)
        channel.basic_publish(
            exchange='',
            routing_key='order.expiry_hold',
            body=json.dumps({'order_id': str(order_id)}),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        conn.close()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f'[RabbitMQ] publish_order_expiry error: {e}')


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

"""Management command: consume_notifications
Listens for order events and sends emails.
Run: python manage.py consume_notifications
"""
import json
import logging
import pika
from django.core.management.base import BaseCommand
from django.conf import settings
from infrastructure.email_service import send_order_confirmation

logger = logging.getLogger(__name__)


def _get_connection():
    credentials = pika.PlainCredentials(
        getattr(settings, 'RABBITMQ_USER', 'guest'),
        getattr(settings, 'RABBITMQ_PASSWORD', 'guest'),
    )
    params = pika.ConnectionParameters(
        host=getattr(settings, 'RABBITMQ_HOST', 'rabbitmq'),
        port=int(getattr(settings, 'RABBITMQ_PORT', 5672)),
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300,
    )
    return pika.BlockingConnection(params)


class Command(BaseCommand):
    help = 'Consume order events and send email notifications.'

    def handle(self, *args, **options):
        import time
        retry = 0
        while True:
            try:
                self.stdout.write(f'[Notification] Connecting to RabbitMQ... (attempt {retry + 1})')
                conn = _get_connection()
                channel = conn.channel()
                channel.exchange_declare(
                    exchange='order.events',
                    exchange_type='topic',
                    durable=True,
                )
                channel.queue_declare(queue='notification.order', durable=True)
                channel.queue_bind(
                    exchange='order.events',
                    queue='notification.order',
                    routing_key='order.created',
                )
                channel.basic_qos(prefetch_count=1)
                channel.basic_consume(
                    queue='notification.order',
                    on_message_callback=self._on_message,
                )
                self.stdout.write('[Notification] Waiting for order.created events...')
                retry = 0
                channel.start_consuming()
            except Exception as e:
                retry += 1
                wait = min(30, 5 * retry)
                logger.error(f'[Notification] Error: {e}. Retrying in {wait}s...')
                time.sleep(wait)

    def _on_message(self, ch, method, properties, body):
        try:
            data = json.loads(body)
            logger.info(f'[Notification] Received event: {data}')

            to_email = data.get('user_email')
            if not to_email:
                logger.warning('[Notification] No user_email in event, skipping')
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            send_order_confirmation(to_email, data)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f'[Notification] Error: {e}')
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

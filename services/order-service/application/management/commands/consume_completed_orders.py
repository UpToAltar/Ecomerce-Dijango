"""Management command: consume_completed_orders
Listens on the order.events exchange (order.completed routing key)
to mark orders as confirmed and commit stock (permanently reducing DB and cleaning lock).
Run: python manage.py consume_completed_orders
"""
import json
import logging
import requests
import pika
from django.core.management.base import BaseCommand
from django.conf import settings
from domain.models import Order
from infrastructure.rabbitmq import _get_connection

logger = logging.getLogger(__name__)

PRODUCT_SERVICE_URL = getattr(settings, 'PRODUCT_SERVICE_URL', 'http://product-service:8000')


class Command(BaseCommand):
    help = 'Consume order.completed events to confirm orders and commit stock.'

    def handle(self, *args, **options):
        import time
        retry = 0
        while True:
            try:
                self.stdout.write(f'[Completed Consumer] Connecting to RabbitMQ... (attempt {retry + 1})')
                conn = _get_connection()
                channel = conn.channel()
                channel.exchange_declare(exchange='order.events', exchange_type='topic', durable=True)
                queue_name = 'order.service.completed.queue'
                channel.queue_declare(queue=queue_name, durable=True)
                channel.queue_bind(exchange='order.events', queue=queue_name, routing_key='order.completed')
                channel.basic_qos(prefetch_count=1)
                channel.basic_consume(
                    queue=queue_name,
                    on_message_callback=self._on_completed,
                )
                self.stdout.write('[Completed Consumer] Waiting for completed orders...')
                retry = 0
                channel.start_consuming()
            except Exception as e:
                retry += 1
                wait = min(30, 5 * retry)
                logger.error(f'[Completed Consumer] Error: {e}. Retrying in {wait}s...')
                time.sleep(wait)

    def _on_completed(self, ch, method, properties, body):
        try:
            data = json.loads(body)
            order_id = data.get('order_id')
            logger.info(f'[Completed] Processing completed order: {order_id}')

            try:
                order = Order.objects.get(id=order_id)
            except Order.DoesNotExist:
                logger.warning(f'[Completed] Order {order_id} not found — ack')
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            # If it's COD, we keep status Pending but still commit stock.
            # If it's VNPay (or others), we change status to Confirmed.
            should_commit_stock = False
            
            if order.status == Order.Status.PENDING:
                if order.payment_method != 'cod':
                    order.status = Order.Status.CONFIRMED
                    order.save()
                    logger.info(f'[Completed] Order {order_id} confirmed (VNPay/Online)')
                else:
                    logger.info(f'[Completed] Order {order_id} remains PENDING (COD), but stock will be committed')
                
                should_commit_stock = True
            
            if should_commit_stock:
                # Commit stock for each item (Deduct from DB & release Redis lock)
                for item in order.items.all():
                    try:
                        requests.post(
                            f'{PRODUCT_SERVICE_URL}/internal/products/{item.product_id}/commit-stock/',
                            json={'quantity': item.quantity},
                            timeout=5,
                        )
                    except Exception as e:
                        logger.error(f'[Completed] Stock commit failed for {item.product_id}: {e}')
            else:
                logger.info(f'[Completed] Order {order_id} already confirmed/completed')

            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f'[Completed] Error processing message: {e}')
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

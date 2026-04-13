"""Management command: consume_expired_orders
Listens on the DLX dead-letter queue and cancels expired orders.
Run: python manage.py consume_expired_orders
"""
import json
import logging
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from domain.models import Order
from infrastructure.rabbitmq import (
    _get_connection, setup_dlx_topology, publish_event
)

logger = logging.getLogger(__name__)

PRODUCT_SERVICE_URL = getattr(settings, 'PRODUCT_SERVICE_URL', 'http://product-service:8000')


class Command(BaseCommand):
    help = 'Consume expired order messages from DLX queue and cancel them.'

    def handle(self, *args, **options):
        self.stdout.write('[DLX Consumer] Connecting to RabbitMQ...')
        conn = _get_connection()
        channel = conn.channel()
        setup_dlx_topology(channel)

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue='order.expired',
            on_message_callback=self._on_expired,
        )
        self.stdout.write('[DLX Consumer] Waiting for expired orders...')
        channel.start_consuming()

    def _on_expired(self, ch, method, properties, body):
        try:
            data = json.loads(body)
            order_id = data.get('order_id')
            logger.info(f'[DLX] Processing expired order: {order_id}')

            try:
                order = Order.objects.get(id=order_id)
            except Order.DoesNotExist:
                logger.warning(f'[DLX] Order {order_id} not found — ack')
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            # 1. Condition: Payment method must be vnpay
            # 2. Condition: Order status must be PENDING
            if order.payment_method == 'vnpay' and order.status == Order.Status.PENDING:
                # 3. Condition: Check payment service to ensure it wasn't successfully paid
                PAYMENT_SERVICE_URL = getattr(settings, 'PAYMENT_SERVICE_URL', 'http://payment-service:8000')
                is_paid = False
                try:
                    resp = requests.get(f'{PAYMENT_SERVICE_URL}/api/payments/order/{order_id}/', timeout=5)
                    if resp.status_code == 200:
                        payments = resp.json()
                        if payments:
                            latest = sorted(payments, key=lambda x: x.get('created_at', ''), reverse=True)[0]
                            if latest.get('status') == 'completed':
                                is_paid = True
                except Exception as e:
                    logger.error(f'[DLX] Failed to check payment status: {e}')

                if not is_paid:
                    order.status = Order.Status.CANCELLED
                    order.save()
                    logger.info(f'[DLX] Order {order_id} cancelled due to expiry')

                    # Restore locked stock by releasing the Redis lock
                    for item in order.items.all():
                        try:
                            requests.post(
                                f'{PRODUCT_SERVICE_URL}/internal/products/{item.product_id}/release-stock/',
                                json={'quantity': item.quantity},
                                timeout=5,
                            )
                        except Exception as e:
                            logger.error(f'[DLX] Stock release failed for {item.product_id}: {e}')

                    # Publish order.cancelled event
                    publish_event(
                        exchange='order.events',
                        routing_key='order.cancelled',
                        payload={
                            'order_id': str(order.id),
                            'order_number': order.order_number,
                            'user_id': str(order.user_id),
                        },
                    )
                else:
                    logger.info(f'[DLX] Order {order_id} is already paid in payment-service — skip cancellation')
            else:
                logger.info(f'[DLX] Order {order_id} not vnpay or not pending — skip')

            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f'[DLX] Error processing message: {e}')
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

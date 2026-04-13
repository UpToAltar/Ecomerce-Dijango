"""VNPay payment views — create payment URL and handle return (IPN)."""
import hashlib
import hmac
import urllib.parse
import uuid
import logging
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from domain.models import Payment
from .serializers import PaymentSerializer, PaymentCreateSerializer
from infrastructure.rabbitmq import publish_event

logger = logging.getLogger(__name__)


def _vnpay_hmac_sha512(key: str, data: str) -> str:
    return hmac.new(
        key.encode('utf-8'),
        data.encode('utf-8'),
        hashlib.sha512,
    ).hexdigest()


def _build_vnpay_url(amount: int, order_id: str, order_info: str, ip_addr: str = '127.0.0.1') -> str:
    """Build VNPay redirect URL with HMAC signature."""
    tmn_code = settings.VNPAY_TMN_CODE
    secret_key = settings.VNPAY_HASH_SECRET
    vnpay_url = settings.VNPAY_URL
    return_url = settings.VNPAY_RETURN_URL

    now = datetime.now()
    create_date = now.strftime('%Y%m%d%H%M%S')
    expire_date = now.replace(minute=now.minute + 15).strftime('%Y%m%d%H%M%S')

    params = {
        'vnp_Version': '2.1.0',
        'vnp_Command': 'pay',
        'vnp_TmnCode': tmn_code,
        'vnp_Amount': str(amount * 100),       # VNPay expects amount * 100
        'vnp_CurrCode': 'VND',
        'vnp_TxnRef': str(order_id).replace('-', '')[:20],
        'vnp_OrderInfo': order_info,
        'vnp_OrderType': 'other',
        'vnp_Locale': 'vn',
        'vnp_ReturnUrl': return_url,
        'vnp_IpAddr': ip_addr,
        'vnp_CreateDate': create_date,
        'vnp_ExpireDate': expire_date,
    }

    # Sort params and build query string
    sorted_params = sorted(params.items())
    query_string = urllib.parse.urlencode(sorted_params)
    secure_hash = _vnpay_hmac_sha512(secret_key, query_string)

    return f'{vnpay_url}?{query_string}&vnp_SecureHash={secure_hash}'


class PaymentCreateView(APIView):
    """POST /api/payments/create/ — Create a payment (COD)."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        payment = Payment.objects.create(**d)
        if payment.method == Payment.Method.COD:
            payment.status = Payment.Status.COMPLETED
            payment.save()
            # Publish order.completed for notification
            publish_event(
                exchange='order.events',
                routing_key='order.completed',
                payload={
                    'order_id': str(payment.order_id),
                    'user_id': str(payment.user_id),
                    'total_amount': str(payment.amount),
                    'user_email': request.data.get('user_email', ''),
                    'order_number': request.data.get('order_number', ''),
                    'items': request.data.get('items', []),
                },
            )
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class PaymentDetailView(APIView):
    """GET /api/payments/<id>/ — Payment detail."""
    permission_classes = [AllowAny]

    def get(self, request, payment_id):
        try:
            payment = Payment.objects.get(id=payment_id)
            return Response(PaymentSerializer(payment).data)
        except Payment.DoesNotExist:
            return Response({'error': 'Payment not found'}, status=404)


class PaymentByOrderView(APIView):
    """GET /api/payments/order/<order_id>/ — Get payment by order."""
    permission_classes = [AllowAny]

    def get(self, request, order_id):
        payments = Payment.objects.filter(order_id=order_id)
        return Response(PaymentSerializer(payments, many=True).data)


class PaymentCallbackView(APIView):
    """POST /api/payments/<id>/callback/ — Payment gateway callback."""
    permission_classes = [AllowAny]

    def post(self, request, payment_id):
        try:
            payment = Payment.objects.get(id=payment_id)
        except Payment.DoesNotExist:
            return Response({'error': 'Payment not found'}, status=404)

        new_status = request.data.get('status', 'completed')
        transaction_id = request.data.get('transaction_id')
        payment.status = new_status
        if transaction_id:
            payment.transaction_id = transaction_id
        payment.metadata = request.data.get('metadata', {})
        payment.save()
        return Response(PaymentSerializer(payment).data)


class VNPayCreateView(APIView):
    """POST /api/payments/vnpay/create/ — Build VNPay redirect URL."""
    permission_classes = [AllowAny]

    def post(self, request):
        order_id = request.data.get('order_id')
        user_id = request.data.get('user_id')
        amount = request.data.get('amount')
        order_number = request.data.get('order_number', '')
        user_email = request.data.get('user_email', '')
        items = request.data.get('items', [])

        if not all([order_id, user_id, amount]):
            return Response({'error': 'order_id, user_id, amount are required'}, status=400)

        # Create pending payment record
        payment = Payment.objects.create(
            order_id=order_id,
            user_id=user_id,
            amount=int(amount),
            method=Payment.Method.VNPAY,
            status=Payment.Status.PENDING,
            metadata={
                'order_number': order_number,
                'user_email': user_email,
                'items': items,
            },
        )

        ip_addr = request.META.get('REMOTE_ADDR', '127.0.0.1')
        payment_url = _build_vnpay_url(
            amount=int(amount),
            order_id=str(payment.id),
            order_info=f'Thanh toan don hang {order_number}',
            ip_addr=ip_addr,
        )
        return Response({
            'payment_url': payment_url,
            'payment_id': str(payment.id),
        })


class VNPayReturnView(APIView):
    """GET /api/payments/vnpay/return/ — VNPay IPN / return URL handler."""
    permission_classes = [AllowAny]

    def get(self, request):
        params = dict(request.query_params)
        secure_hash = params.pop('vnp_SecureHash', [None])[0]
        if isinstance(secure_hash, list):
            secure_hash = secure_hash[0]

        # Remove hash type param if present
        params.pop('vnp_SecureHashType', None)

        # Flatten single-item lists
        flat_params = {k: v[0] if isinstance(v, list) else v for k, v in params.items()}

        # Verify HMAC
        sorted_params = sorted(flat_params.items())
        query_string = urllib.parse.urlencode(sorted_params)
        expected_hash = _vnpay_hmac_sha512(settings.VNPAY_HASH_SECRET, query_string)

        if secure_hash and secure_hash.lower() != expected_hash.lower():
            logger.warning('[VNPay] Invalid signature on return')
            return Response({'code': '97', 'message': 'Invalid signature'}, status=400)

        response_code = flat_params.get('vnp_ResponseCode', '')
        txn_ref = flat_params.get('vnp_TxnRef', '')
        transaction_no = flat_params.get('vnp_TransactionNo', '')

        # Find payment by txn_ref (order_id without dashes, truncated to 20 chars)
        payment = None
        try:
            # Try matching payment_id from metadata or by txn_ref
            for p in Payment.objects.filter(method=Payment.Method.VNPAY, status=Payment.Status.PENDING):
                ref = str(p.id).replace('-', '')[:20]
                if ref == txn_ref:
                    payment = p
                    break
        except Exception as e:
            logger.error(f'[VNPay] Error finding payment: {e}')

        if not payment:
            logger.warning(f'[VNPay] Payment not found for txnref {txn_ref}')
            return Response({'code': '01', 'message': 'Order not found'}, status=404)

        if response_code == '00':
            payment.status = Payment.Status.COMPLETED
            payment.transaction_id = transaction_no
            payment.metadata.update({'vnp_params': flat_params})
            payment.save()

            # Publish order.completed event for notification
            meta = payment.metadata
            publish_event(
                exchange='order.events',
                routing_key='order.completed',
                payload={
                    'order_id': str(payment.order_id),
                    'user_id': str(payment.user_id),
                    'total_amount': str(payment.amount),
                    'user_email': meta.get('user_email', ''),
                    'order_number': meta.get('order_number', ''),
                    'items': meta.get('items', []),
                },
            )
            logger.info(f'[VNPay] Payment {payment.id} completed')
            return Response({'code': '00', 'message': 'Success', 'payment_id': str(payment.id)})
        else:
            payment.status = Payment.Status.FAILED
            payment.metadata.update({'vnp_params': flat_params, 'response_code': response_code})
            payment.save()
            logger.warning(f'[VNPay] Payment {payment.id} failed with code {response_code}')
            return Response({'code': response_code, 'message': 'Payment failed'})

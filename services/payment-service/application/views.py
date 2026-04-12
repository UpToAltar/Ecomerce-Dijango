from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from domain.models import Payment
from .serializers import PaymentSerializer, PaymentCreateSerializer


class PaymentCreateView(APIView):
    """POST /api/payments/create/ — Create a payment."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        payment = Payment.objects.create(**d)
        # COD auto-completes
        if payment.method == Payment.Method.COD:
            payment.status = Payment.Status.COMPLETED
            payment.save()
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

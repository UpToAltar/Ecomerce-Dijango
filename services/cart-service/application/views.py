from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from domain.models import CartItem
from .serializers import CartItemSerializer, CartItemCreateSerializer, CartItemUpdateSerializer


class CartView(APIView):
    """GET /api/cart/?user_id=... — Get user's cart items."""
    permission_classes = [AllowAny]

    def get(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'user_id required'}, status=400)
        items = CartItem.objects.filter(user_id=user_id)
        return Response(CartItemSerializer(items, many=True).data)


class CartAddView(APIView):
    """POST /api/cart/add/ — Add item to cart."""
    permission_classes = [AllowAny]

    def post(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id required'}, status=400)

        serializer = CartItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        item, created = CartItem.objects.get_or_create(
            user_id=user_id,
            product_id=serializer.validated_data['product_id'],
            defaults={'quantity': serializer.validated_data['quantity']},
        )
        if not created:
            item.quantity += serializer.validated_data['quantity']
            item.save()

        return Response(CartItemSerializer(item).data, status=status.HTTP_201_CREATED)


class CartUpdateView(APIView):
    """PUT /api/cart/<id>/update/ — Update cart item quantity."""
    permission_classes = [AllowAny]

    def put(self, request, item_id):
        try:
            item = CartItem.objects.get(id=item_id)
        except CartItem.DoesNotExist:
            return Response({'error': 'Item not found'}, status=404)

        serializer = CartItemUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item.quantity = serializer.validated_data['quantity']
        item.save()
        return Response(CartItemSerializer(item).data)


class CartRemoveView(APIView):
    """DELETE /api/cart/<id>/remove/ — Remove item from cart."""
    permission_classes = [AllowAny]

    def delete(self, request, item_id):
        try:
            item = CartItem.objects.get(id=item_id)
            item.delete()
            return Response({'message': 'Removed'}, status=status.HTTP_204_NO_CONTENT)
        except CartItem.DoesNotExist:
            return Response({'error': 'Item not found'}, status=404)


class CartClearView(APIView):
    """DELETE /api/cart/clear/?user_id=... — Clear user's cart."""
    permission_classes = [AllowAny]

    def delete(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'user_id required'}, status=400)
        CartItem.objects.filter(user_id=user_id).delete()
        return Response({'message': 'Cart cleared'}, status=status.HTTP_204_NO_CONTENT)

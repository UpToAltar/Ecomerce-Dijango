from django.urls import path
from . import views
urlpatterns = [
    path('create/', views.PaymentCreateView.as_view(), name='payment_create'),
    path('<uuid:payment_id>/', views.PaymentDetailView.as_view(), name='payment_detail'),
    path('order/<uuid:order_id>/', views.PaymentByOrderView.as_view(), name='payment_by_order'),
    path('<uuid:payment_id>/callback/', views.PaymentCallbackView.as_view(), name='payment_callback'),
]

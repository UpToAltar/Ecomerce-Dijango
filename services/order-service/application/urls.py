from django.urls import path
from . import views

urlpatterns = [
    path('', views.OrderListView.as_view(), name='order_list'),
    path('create/', views.OrderCreateView.as_view(), name='order_create'),
    path('<uuid:order_id>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('<uuid:order_id>/status/', views.OrderStatusUpdateView.as_view(), name='order_status'),
    path('<uuid:order_id>/cancel/', views.OrderCancelView.as_view(), name='order_cancel'),
    path('<uuid:order_id>/tracking/', views.ShippingTrackingCreateView.as_view(), name='order_tracking'),
]

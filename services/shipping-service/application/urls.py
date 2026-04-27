from django.urls import path
from . import views

urlpatterns = [
    path('', views.ShipmentListView.as_view(), name='shipment_list'),
    path('admin/', views.ShipmentAdminListView.as_view(), name='shipment_admin_list'),
    path('create/', views.ShipmentCreateView.as_view(), name='shipment_create'),
    path('<uuid:shipment_id>/', views.ShipmentDetailView.as_view(), name='shipment_detail'),
    path('<uuid:shipment_id>/status/', views.ShipmentStatusUpdateView.as_view(), name='shipment_status'),
    path('<uuid:shipment_id>/tracking/', views.ShipmentTrackingCreateView.as_view(), name='shipment_tracking'),
    path('order/<uuid:order_id>/', views.ShipmentByOrderView.as_view(), name='shipment_by_order'),
    path('track/<str:tracking_number>/', views.TrackByTrackingNumberView.as_view(), name='track_by_number'),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('categories', views.CategoryViewSet, basename='category')
router.register('', views.ProductViewSet, basename='product')

urlpatterns = [
    path('', include(router.urls)),
    # Internal endpoints (called by other services)
    path('../internal/products/<uuid:product_id>/deduct-stock/', views.DeductStockView.as_view(), name='deduct_stock'),
    path('../internal/products/<uuid:product_id>/restore-stock/', views.RestoreStockView.as_view(), name='restore_stock'),
]

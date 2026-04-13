from django.urls import path, include
from django.http import JsonResponse
from application import views

def health_check(request):
    return JsonResponse({'status': 'ok', 'service': 'product-service'})

urlpatterns = [
    path('health/', health_check),
    path('api/products/', include('application.urls')),
    path('api/analytics/', include('analytics.urls')),
    
    # Internal endpoints (called by other services)
    path('internal/products/<uuid:product_id>/lock-stock/', views.LockStockView.as_view(), name='lock_stock'),
    path('internal/products/<uuid:product_id>/commit-stock/', views.CommitStockView.as_view(), name='commit_stock'),
    path('internal/products/<uuid:product_id>/release-stock/', views.ReleaseStockDelockView.as_view(), name='release_stock'),
]

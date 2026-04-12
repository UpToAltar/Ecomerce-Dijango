from django.urls import path, include
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({'status': 'ok', 'service': 'product-service'})

urlpatterns = [
    path('health/', health_check),
    path('api/products/', include('application.urls')),
    path('api/analytics/', include('analytics.urls')),
]

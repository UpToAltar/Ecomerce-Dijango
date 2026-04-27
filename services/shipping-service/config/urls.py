from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def health_check(request):
    return JsonResponse({'status': 'ok', 'service': 'shipping-service'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check),
    path('api/shipping/', include('application.urls')),
]

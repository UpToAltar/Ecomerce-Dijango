from django.urls import path, re_path
from django.http import JsonResponse
from api_gateway.views import ProxyView

def health_check(request):
    return JsonResponse({'status': 'ok', 'service': 'gateway'})

urlpatterns = [
    path('health/', health_check),
    re_path(r'^api/(?P<service>[^/]+)/(?P<path>.*)$', ProxyView.as_view()),
]

import requests
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

SERVICE_MAP = {
    'auth': 'http://auth-service:8000',
    'products': 'http://product-service:8000',
    'cart': 'http://cart-service:8000',
    'orders': 'http://order-service:8000',
    'payments': 'http://payment-service:8000',
    'notifications': 'http://notification-service:8000',
    'reviews': 'http://review-service:8000',
    'ai': 'http://ai-service:8000',
    'ai-new': 'http://ai-new-service:8000',
}

@method_decorator(csrf_exempt, name='dispatch')
class ProxyView(View):
    def dispatch(self, request, service, path, *args, **kwargs):
        if service not in SERVICE_MAP:
            return JsonResponse({'error': 'Service not found'}, status=404)
        
        target_url = f"{SERVICE_MAP[service]}/api/{service}/{path}"
        if request.META.get('QUERY_STRING'):
            target_url += f"?{request.META['QUERY_STRING']}"

        headers = {k: v for k, v in request.headers.items() if k.lower() not in ['host', 'content-length']}
        
        try:
            method = request.method
            data = request.body if method in ['POST', 'PUT', 'PATCH'] else None
            
            response = requests.request(
                method=method,
                url=target_url,
                headers=headers,
                data=data,
                stream=True,
                timeout=10
            )

            res = HttpResponse(
                response.iter_content(chunk_size=1024),
                status=response.status_code,
                content_type=response.headers.get('Content-Type')
            )
            return res
            
        except requests.exceptions.RequestException as e:
            return JsonResponse({'error': 'Upstream service unavailable', 'details': str(e)}, status=503)

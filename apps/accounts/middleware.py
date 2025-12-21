import time
from django.core.cache import cache
from django.http import JsonResponse
from django.conf import settings


class RateLimitMiddleware:
    """
    Rate limiting middleware for authentication endpoints
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limit_paths = [
            '/api/auth/register',
            '/api/auth/login',
        ]

    def __call__(self, request):
        if not settings.RATE_LIMIT_ENABLE:
            return self.get_response(request)

        if request.path in self.rate_limit_paths:
            ip_address = self.get_client_ip(request)
            cache_key = f'rate_limit:{ip_address}'
            
            rate_data = cache.get(cache_key)
            now = time.time()
            
            if rate_data is None:
                cache.set(
                    cache_key,
                    {'count': 1, 'reset_time': now + settings.RATE_LIMIT_WINDOW},
                    settings.RATE_LIMIT_WINDOW
                )
            else:
                if now > rate_data['reset_time']:
                    cache.set(
                        cache_key,
                        {'count': 1, 'reset_time': now + settings.RATE_LIMIT_WINDOW},
                        settings.RATE_LIMIT_WINDOW
                    )
                elif rate_data['count'] >= settings.RATE_LIMIT_MAX_REQUESTS:
                    retry_after = int(rate_data['reset_time'] - now)
                    return JsonResponse(
                        {
                            'message': 'Too many requests. Please try again later.',
                            'retryAfter': retry_after
                        },
                        status=429,
                        headers={'Retry-After': str(retry_after)}
                    )
                else:
                    rate_data['count'] += 1
                    cache.set(cache_key, rate_data, settings.RATE_LIMIT_WINDOW)

        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    

class MediaCORSMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Add CORS headers for media files (videos, thumbnails, etc.)
        if request.path.startswith('/media/'):
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, HEAD, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Range, Content-Type, Accept, Accept-Encoding'
            response['Access-Control-Expose-Headers'] = 'Content-Length, Content-Range, Accept-Ranges'
            response['Cross-Origin-Resource-Policy'] = 'cross-origin'
            response['Accept-Ranges'] = 'bytes'
            
        return response
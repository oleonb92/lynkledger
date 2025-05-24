from django.core.cache import cache
from django.http import HttpResponseTooManyRequests
from django.conf import settings
import time
import logging
from typing import Callable
from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)

class RateLimitMiddleware:
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self.rate_limits = {
            'default': (100, 60),  # 100 requests per minute
            'api': (1000, 60),     # 1000 requests per minute
            'auth': (5, 60),       # 5 requests per minute
            'webhook': (100, 60),  # 100 requests per minute
        }

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Skip rate limiting for certain paths
        if request.path.startswith('/admin/'):
            return self.get_response(request)

        # Determine rate limit type
        rate_limit_type = 'default'
        if request.path.startswith('/api/'):
            rate_limit_type = 'api'
        elif request.path.startswith('/auth/'):
            rate_limit_type = 'auth'
        elif request.path.startswith('/webhook/'):
            rate_limit_type = 'webhook'

        # Get rate limit settings
        max_requests, window = self.rate_limits[rate_limit_type]

        # Get client identifier
        client_id = self._get_client_id(request)

        # Check rate limit
        if not self._check_rate_limit(client_id, rate_limit_type, max_requests, window):
            logger.warning(
                f"Rate limit exceeded for {client_id}",
                extra={
                    'client_id': client_id,
                    'rate_limit_type': rate_limit_type,
                    'path': request.path
                }
            )
            return HttpResponseTooManyRequests('Rate limit exceeded')

        return self.get_response(request)

    def _get_client_id(self, request: HttpRequest) -> str:
        """Get a unique identifier for the client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        if request.user.is_authenticated:
            return f"{ip}:{request.user.id}"
        return ip

    def _check_rate_limit(self, client_id: str, rate_limit_type: str, max_requests: int, window: int) -> bool:
        """Check if the client has exceeded the rate limit."""
        cache_key = f"rate_limit:{rate_limit_type}:{client_id}"
        current = int(time.time())
        window_start = current - window

        # Get existing requests
        requests = cache.get(cache_key, [])
        
        # Remove old requests
        requests = [req for req in requests if req > window_start]
        
        # Check if limit is exceeded
        if len(requests) >= max_requests:
            return False
        
        # Add current request
        requests.append(current)
        cache.set(cache_key, requests, window)
        
        return True

class SecurityHeadersMiddleware:
    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response['Content-Security-Policy'] = "default-src 'self' https: http:; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; connect-src 'self' https: http:;"
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response

class RequestLoggingMiddleware:
    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Log request
        logger.info(
            f"Request received: {request.method} {request.path}",
            extra={
                'method': request.method,
                'path': request.path,
                'user_id': request.user.id if request.user.is_authenticated else None,
                'ip': self._get_client_ip(request)
            }
        )

        response = self.get_response(request)

        # Log response
        logger.info(
            f"Response sent: {response.status_code}",
            extra={
                'status_code': response.status_code,
                'method': request.method,
                'path': request.path,
                'user_id': request.user.id if request.user.is_authenticated else None
            }
        )

        return response

    def _get_client_ip(self, request: HttpRequest) -> str:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR') 
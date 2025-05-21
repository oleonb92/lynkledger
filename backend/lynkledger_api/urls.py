"""
URL configuration for lynkledger_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.views.generic import RedirectView

# API URLs
api_patterns = [
    path('users/', include('users.urls', namespace='users')),
    path('', include('organizations.urls', namespace='organizations')),
    path('accounting/', include('accounting.urls', namespace='accounting')),
]

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    A public endpoint to check if the API is running
    """
    return Response({
        'status': 'healthy',
        'message': 'Backend API is running'
    })

urlpatterns = [
    # Redirect root to admin
    path('', RedirectView.as_view(url='/admin/', permanent=False), name='home'),
    # Admin URLs
    path('admin/', admin.site.urls, name='admin'),
    # API URLs
    path('api/v1/', include((api_patterns, 'api'), namespace='api')),
    path('api/health-check/', health_check, name='health-check'),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # In production, serve static files through whitenoise
    urlpatterns += [
        path('static/<path:path>', RedirectView.as_view(url='/staticfiles/%(path)s'), name='static'),
        path('media/<path:path>', RedirectView.as_view(url='/media/%(path)s'), name='media'),
    ]

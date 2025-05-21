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
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView
from django.contrib.auth.views import LoginView
from django.utils.translation import gettext_lazy as _

# API URLs
api_patterns = [
    path('users/', include('users.urls')),
    path('', include('organizations.urls')),
    path('accounting/', include('accounting.urls')),
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

class AdminLoginView(LoginView):
    template_name = 'admin/login.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('Log in'),
            'subtitle': None,
            'site_title': _('LynkLedger Admin'),
            'site_header': _('LynkLedger Administration'),
            'has_permission': True,
            'app_path': self.request.path,
        })
        return context
    
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response.set_cookie('csrftoken', request.META.get('CSRF_COOKIE', ''))
        return response

urlpatterns = [
    # Redirect root to admin
    path('', RedirectView.as_view(url='/admin/', permanent=False)),
    # Admin URLs
    path('admin/login/', AdminLoginView.as_view(), name='admin_login'),
    path('admin/', admin.site.urls),
    # API URLs
    path('api/v1/', include(api_patterns)),
    path('api/health-check/', health_check, name='health-check'),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # In production, serve static files through whitenoise
    urlpatterns += [
        path('static/<path:path>', RedirectView.as_view(url='/staticfiles/%(path)s')),
        path('media/<path:path>', RedirectView.as_view(url='/media/%(path)s')),
    ]

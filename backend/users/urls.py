from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from .views import (
    RegisterView,
    ProfileView,
    ChangePasswordView,
    RoleViewSet,
    UserMeView
)

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'roles', RoleViewSet)

app_name = 'users'

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Authentication URLs
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # User management URLs
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('me/', UserMeView.as_view(), name='user-me'),
] 
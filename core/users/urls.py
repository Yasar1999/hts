from rest_framework.routers import DefaultRouter
from django.urls.conf import include, path
from .views import CustomUserViewSet, RoleViewSet, PermissionViewSet


user_router = DefaultRouter()
user_router.register(r'users', CustomUserViewSet)
user_router.register(r'role', RoleViewSet)

urlpatterns = [
    path(r'', include(user_router.urls)),
    path('permissions/', PermissionViewSet.as_view(), name='permission-list'),

]
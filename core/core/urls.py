"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from drf_yasg import openapi
from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from users.authentication import ObtainJSONWebTokenExtended, LogoutView
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from graphene_django.views import GraphQLView


class BothHttpAndHttpsSchemaGenerator(OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        schema.schemes = ["http", "https"]
        return schema


schema_view = get_schema_view(
   openapi.Info(
      title="Python API",
      default_version='v1',
      description="An api for Python",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="yasirsharief1999@gmail.com"),
      license=openapi.License(name="Test License"),
   ),
   public=True,
   generator_class=BothHttpAndHttpsSchemaGenerator,
   permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('api/admin/', admin.site.urls),
    path('api-auth', include('rest_framework.urls'), name="rest_framework"),
    path('api/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api-token-auth/', ObtainJSONWebTokenExtended.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('api-token-refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('api-token-verify/', TokenVerifyView.as_view(), name='token-verify'),
    path("graphql/", GraphQLView.as_view(graphiql=True)),
    # path('api-token-auth/', ObtainJSONWebTokenExtended.as_view()),
    # path('api-token-refresh/', refresh_jwt_token),
    # path('api-token-verify/', verify_jwt_token),
    path(r'api/', include('users.urls')),
    path(r'api/', include('product.urls')),
    path(r'api/', include('business.urls')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)\
+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

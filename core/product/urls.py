from rest_framework.routers import DefaultRouter
from django.urls.conf import include, path
from .views import CategoryViewSet, SizeChartViewSet, BrandViewSet, ProductViewSet


product_router = DefaultRouter()
product_router.register(r'category', CategoryViewSet)
product_router.register(r'brand', BrandViewSet)
product_router.register(r'size', SizeChartViewSet)
product_router.register(r'product', ProductViewSet)

urlpatterns = [
    path(r'', include(product_router.urls)),
]

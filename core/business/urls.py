from rest_framework.routers import DefaultRouter
from django.urls.conf import path, include
from .views import AddToCartViewSet, OrderViewSet

business_router = DefaultRouter()
business_router.register(r'order', OrderViewSet)

urlpatterns = [
    path(r'cart/', AddToCartViewSet.as_view(), name="add-to-cart"),
    path(r'', include(business_router.urls)),
]
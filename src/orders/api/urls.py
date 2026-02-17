"""
URLs do módulo de Pedidos.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from orders.api.views import OrderViewSet

router = DefaultRouter()
router.register(r"", OrderViewSet, basename="order")

urlpatterns = [
    path("", include(router.urls)),
]

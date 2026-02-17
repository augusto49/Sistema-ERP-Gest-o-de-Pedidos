"""
URLs do módulo de Clientes.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from customers.api.views import CustomerViewSet

router = DefaultRouter()
router.register(r"", CustomerViewSet, basename="customer")

urlpatterns = [
    path("", include(router.urls)),
]

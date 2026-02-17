"""
URL configuration for ERP project.
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from shared.views.scalar import ScalarView

urlpatterns = [
    path("admin/", admin.site.urls),
    # API v1
    path("api/v1/customers/", include("customers.api.urls")),
    path("api/v1/products/", include("products.api.urls")),
    path("api/v1/orders/", include("orders.api.urls")),
    # Documentação
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path(
        "api/scalar/",
        ScalarView.as_view(),
        name="scalar",
    ),
]


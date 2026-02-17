"""
Health check endpoint.
Verifica conectividade com banco de dados e Redis.
"""

import structlog
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.views import View

logger = structlog.get_logger(__name__)


class HealthCheckView(View):
    """
    GET /health
    Retorna status dos serviços: database e cache (Redis).
    """

    def get(self, request):
        health = {
            "status": "healthy",
            "services": {},
        }
        overall_healthy = True

        # Check database
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health["services"]["database"] = {"status": "up"}
        except Exception as e:
            logger.error("health_check_db_failed", error=str(e))
            health["services"]["database"] = {"status": "down", "error": str(e)}
            overall_healthy = False

        # Check Redis
        try:
            cache.set("health_check", "ok", timeout=5)
            value = cache.get("health_check")
            if value == "ok":
                health["services"]["redis"] = {"status": "up"}
            else:
                health["services"]["redis"] = {"status": "degraded"}
                overall_healthy = False
        except Exception as e:
            logger.error("health_check_redis_failed", error=str(e))
            health["services"]["redis"] = {"status": "down", "error": str(e)}
            overall_healthy = False

        if not overall_healthy:
            health["status"] = "unhealthy"

        status_code = 200 if overall_healthy else 503
        return JsonResponse(health, status=status_code)

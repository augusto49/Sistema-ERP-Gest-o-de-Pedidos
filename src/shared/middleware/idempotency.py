"""
Middleware de Idempotência.
Garante que requisições POST duplicadas não criem recursos duplicados.
Utiliza Redis para armazenar chaves de idempotência.
"""

import hashlib
import json

import structlog
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse

logger = structlog.get_logger(__name__)

# Tempo de expiração da chave de idempotência (24 horas)
IDEMPOTENCY_KEY_TTL = 60 * 60 * 24


class IdempotencyMiddleware:
    """
    Middleware que intercepta requisições POST com o cabeçalho
    'Idempotency-Key' e garante que a mesma operação não seja
    executada mais de uma vez.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Só aplica idempotência para métodos POST
        if request.method != "POST":
            return self.get_response(request)

        idempotency_key = request.headers.get("Idempotency-Key")

        if not idempotency_key:
            return self.get_response(request)

        cache_key = f"idempotency:{idempotency_key}"
        cached_response = cache.get(cache_key)

        if cached_response is not None:
            logger.info(
                "idempotency_hit",
                key=idempotency_key,
                path=request.path,
            )
            return JsonResponse(
                cached_response["data"],
                status=cached_response["status"],
                safe=False,
            )

        # Processar a requisição normalmente
        response = self.get_response(request)

        # Cachear a resposta para requisições bem-sucedidas (2xx)
        if 200 <= response.status_code < 300:
            try:
                response_data = json.loads(response.content)
                cache.set(
                    cache_key,
                    {"data": response_data, "status": response.status_code},
                    IDEMPOTENCY_KEY_TTL,
                )
                logger.info(
                    "idempotency_cached",
                    key=idempotency_key,
                    path=request.path,
                )
            except (json.JSONDecodeError, AttributeError):
                pass

        return response

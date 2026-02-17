"""
Configurações do Django para testes.
Herda tudo de core.settings mas utiliza SQLite in-memory.
"""

from core.settings import *  # noqa: F401,F403

# Usar SQLite em memória para testes (rápido, sem depender de MySQL/Docker)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Desabilitar cache Redis também para testes
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Desabilitar middleware de idempotência nos testes
MIDDLEWARE = [
    m for m in MIDDLEWARE if "IdempotencyMiddleware" not in m  # noqa: F405
]

# Desabilitar throttling para testes (evita 429 Too Many Requests)
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []  # noqa: F405
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {}  # noqa: F405

"""
Sistema de eventos de domínio.
Permite disparar e escutar eventos de forma desacoplada.
"""

from typing import Any, Callable


class DomainEvent:
    """Classe base para eventos de domínio."""

    def __init__(self, **kwargs):
        self.data = kwargs

    def __repr__(self):
        return f"{self.__class__.__name__}({self.data})"


class EventBus:
    """
    Barramento de eventos simples (in-memory).
    Pode ser substituído por Celery/RabbitMQ no futuro.
    """

    _handlers: dict[str, list[Callable]] = {}

    @classmethod
    def subscribe(cls, event_type: str, handler: Callable):
        """Registra um handler para um tipo de evento."""
        if event_type not in cls._handlers:
            cls._handlers[event_type] = []
        cls._handlers[event_type].append(handler)

    @classmethod
    def publish(cls, event_type: str, event: DomainEvent):
        """Publica um evento para todos os handlers registrados."""
        handlers = cls._handlers.get(event_type, [])
        for handler in handlers:
            handler(event)

    @classmethod
    def clear(cls):
        """Limpa todos os handlers (útil para testes)."""
        cls._handlers = {}

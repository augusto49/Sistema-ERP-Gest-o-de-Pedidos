"""
Exception handler customizado para o DRF.
Converte exceções de domínio em respostas HTTP padronizadas.
"""

import structlog
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from shared.exceptions.domain_exceptions import (
    BusinessRuleViolation,
    DomainException,
    DuplicateRequestException,
    EntityNotFoundException,
)

logger = structlog.get_logger(__name__)


def custom_exception_handler(exc, context):
    """
    Handler de exceções que converte exceções de domínio
    em respostas HTTP com formato padronizado.
    """
    # Primeiro, chama o handler padrão do DRF
    response = exception_handler(exc, context)

    if response is not None:
        return response

    # Mapear exceções de domínio para HTTP
    if isinstance(exc, EntityNotFoundException):
        logger.warning("entity_not_found", error=str(exc))
        return Response(
            {"error": {"code": exc.code, "message": exc.message}},
            status=status.HTTP_404_NOT_FOUND,
        )

    if isinstance(exc, DuplicateRequestException):
        logger.info("duplicate_request", error=str(exc))
        return Response(
            {"error": {"code": exc.code, "message": exc.message}},
            status=status.HTTP_409_CONFLICT,
        )

    if isinstance(exc, BusinessRuleViolation):
        logger.warning("business_rule_violation", error=str(exc))
        return Response(
            {"error": {"code": exc.code, "message": exc.message}},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    if isinstance(exc, DomainException):
        logger.error("domain_error", error=str(exc))
        return Response(
            {"error": {"code": exc.code, "message": exc.message}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Exceção inesperada
    logger.exception("unhandled_exception", error=str(exc))
    return Response(
        {"error": {"code": "internal_error", "message": "Erro interno do servidor."}},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )

"""
Exceções customizadas do domínio.
"""


class DomainException(Exception):
    """Exceção base para erros de domínio."""

    def __init__(self, message: str, code: str = "domain_error"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class EntityNotFoundException(DomainException):
    """Entidade não encontrada no banco de dados."""

    def __init__(self, entity: str, entity_id):
        super().__init__(
            message=f"{entity} com identificador '{entity_id}' não encontrado.",
            code="not_found",
        )


class BusinessRuleViolation(DomainException):
    """Violação de regra de negócio."""

    def __init__(self, message: str):
        super().__init__(message=message, code="business_rule_violation")


class InsufficientStockException(BusinessRuleViolation):
    """Estoque insuficiente para o produto."""

    def __init__(self, product_sku: str, requested: int, available: int):
        super().__init__(
            message=(
                f"Estoque insuficiente para o produto '{product_sku}'. "
                f"Solicitado: {requested}, Disponível: {available}."
            )
        )
        self.code = "insufficient_stock"


class InvalidStateTransitionException(BusinessRuleViolation):
    """Transição de status inválida."""

    def __init__(self, current_status: str, target_status: str):
        super().__init__(
            message=(
                f"Transição de status inválida: "
                f"'{current_status}' -> '{target_status}'."
            )
        )
        self.code = "invalid_state_transition"


class DuplicateRequestException(DomainException):
    """Requisição duplicada (idempotência)."""

    def __init__(self):
        super().__init__(
            message="Requisição duplicada detectada.",
            code="duplicate_request",
        )

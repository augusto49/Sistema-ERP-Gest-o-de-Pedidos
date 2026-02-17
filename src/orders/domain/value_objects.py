"""
Value Objects do domínio de Pedidos.
Objetos imutáveis que representam conceitos sem identidade própria.
"""

from enum import Enum


class OrderStatus(str, Enum):
    """
    Status possíveis de um Pedido.
    Fluxo principal:
        PENDING → CONFIRMED → SEPARATED → SHIPPED → DELIVERED
    Cancelamento (apenas nos dois primeiros status):
        PENDING   → CANCELLED
        CONFIRMED → CANCELLED
    """

    PENDING = "pending"
    CONFIRMED = "confirmed"
    SEPARATED = "separated"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

    @classmethod
    def valid_transitions(cls) -> dict:
        """Retorna o mapa de transições válidas entre status."""
        return {
            cls.PENDING: [cls.CONFIRMED, cls.CANCELLED],
            cls.CONFIRMED: [cls.SEPARATED, cls.CANCELLED],
            cls.SEPARATED: [cls.SHIPPED],
            cls.SHIPPED: [cls.DELIVERED],
            cls.DELIVERED: [],
            cls.CANCELLED: [],
        }

    def can_transition_to(self, new_status: "OrderStatus") -> bool:
        """Verifica se a transição para o novo status é válida."""
        return new_status in self.valid_transitions().get(self, [])

"""
Entidades de domínio - Order e OrderItem.
Classes Python puras, sem dependência do Django.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional

from orders.domain.value_objects import OrderStatus
from shared.exceptions.domain_exceptions import InvalidStateTransitionException


@dataclass
class OrderItemEntity:
    """Entidade representando um item dentro de um pedido."""

    id: Optional[int] = None
    order_id: Optional[int] = None
    product_id: int = 0
    product_sku: str = ""
    product_name: str = ""
    quantity: int = 0
    unit_price: Decimal = Decimal("0.00")

    @property
    def subtotal(self) -> Decimal:
        """Calcula o subtotal do item."""
        return self.unit_price * self.quantity


@dataclass
class OrderEntity:
    """
    Entidade de domínio representando um Pedido.
    Contém regras de negócio de transição de status.
    """

    id: Optional[int] = None
    customer_id: int = 0
    customer_name: str = ""
    status: OrderStatus = OrderStatus.PENDING
    items: list[OrderItemEntity] = field(default_factory=list)
    notes: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def total(self) -> Decimal:
        """Calcula o valor total do pedido somando os subtotais dos itens."""
        return sum(item.subtotal for item in self.items) if self.items else Decimal("0.00")

    @property
    def total_items(self) -> int:
        """Quantidade total de unidades no pedido."""
        return sum(item.quantity for item in self.items) if self.items else 0

    def transition_to(self, new_status: OrderStatus):
        """
        Transiciona o pedido para um novo status.
        Lança exceção se a transição for inválida.
        """
        if not self.status.can_transition_to(new_status):
            raise InvalidStateTransitionException(
                current_status=self.status.value,
                target_status=new_status.value,
            )
        self.status = new_status

    def confirm(self):
        """Confirma o pedido."""
        self.transition_to(OrderStatus.CONFIRMED)

    def separate(self):
        """Marca o pedido como separado (picking)."""
        self.transition_to(OrderStatus.SEPARATED)

    def ship(self):
        """Marca o pedido como enviado."""
        self.transition_to(OrderStatus.SHIPPED)

    def deliver(self):
        """Marca o pedido como entregue."""
        self.transition_to(OrderStatus.DELIVERED)

    def cancel(self):
        """Cancela o pedido."""
        self.transition_to(OrderStatus.CANCELLED)

    def soft_delete(self):
        self.deleted_at = datetime.now()

    def validate(self) -> list[str]:
        errors = []
        if not self.customer_id:
            errors.append("O cliente é obrigatório.")
        if not self.items:
            errors.append("O pedido deve ter pelo menos um item.")
        for item in self.items:
            if item.quantity <= 0:
                errors.append(f"Quantidade inválida para o produto '{item.product_sku}'.")
            if item.unit_price <= 0:
                errors.append(f"Preço inválido para o produto '{item.product_sku}'.")
        return errors

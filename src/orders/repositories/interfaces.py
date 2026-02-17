"""
Interfaces abstratas do repositório de Order.
"""

from abc import ABC, abstractmethod
from typing import Optional

from orders.domain.entities import OrderEntity


class IOrderRepository(ABC):
    """
    Interface do repositório de Pedidos.
    """

    @abstractmethod
    def get_by_id(self, order_id: int) -> Optional[OrderEntity]:
        """Busca um pedido pelo ID com seus itens."""
        ...

    @abstractmethod
    def list_all(
        self, filters: Optional[dict] = None, page: int = 1, page_size: int = 20
    ) -> tuple[list[OrderEntity], int]:
        """Lista pedidos com filtros e paginação."""
        ...

    @abstractmethod
    def list_by_customer(
        self, customer_id: int, page: int = 1, page_size: int = 20
    ) -> tuple[list[OrderEntity], int]:
        """Lista pedidos de um cliente específico."""
        ...

    @abstractmethod
    def create(self, entity: OrderEntity) -> OrderEntity:
        """Cria um novo pedido com seus itens."""
        ...

    @abstractmethod
    def update_status(self, order_id: int, new_status: str, notes: str = "", changed_by: str = "system") -> bool:
        """Atualiza o status de um pedido e registra no histórico."""
        ...

    @abstractmethod
    def soft_delete(self, order_id: int) -> bool:
        """Exclusão lógica de um pedido."""
        ...

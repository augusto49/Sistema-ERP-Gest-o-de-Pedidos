"""
Interfaces abstratas do repositório de Product.
"""

from abc import ABC, abstractmethod
from typing import Optional

from products.domain.entities import ProductEntity


class IProductRepository(ABC):
    """
    Interface do repositório de Produtos.
    Inclui métodos para controle de estoque com locking.
    """

    @abstractmethod
    def get_by_id(self, product_id: int) -> Optional[ProductEntity]:
        """Busca um produto pelo ID."""
        ...

    @abstractmethod
    def get_by_sku(self, sku: str) -> Optional[ProductEntity]:
        """Busca um produto pelo SKU."""
        ...

    @abstractmethod
    def get_by_ids_for_update(self, product_ids: list[int]) -> list[ProductEntity]:
        """
        Busca produtos pelo ID com SELECT FOR UPDATE (Pessimistic Lock).
        DEVE ser chamado dentro de uma transação (atomic).
        """
        ...

    @abstractmethod
    def list_all(
        self, filters: Optional[dict] = None, page: int = 1, page_size: int = 20
    ) -> tuple[list[ProductEntity], int]:
        """Lista produtos com filtros e paginação."""
        ...

    @abstractmethod
    def create(self, entity: ProductEntity) -> ProductEntity:
        """Cria um novo produto."""
        ...

    @abstractmethod
    def update(self, entity: ProductEntity) -> ProductEntity:
        """Atualiza um produto existente."""
        ...

    @abstractmethod
    def update_stock(self, product_id: int, new_quantity: int) -> bool:
        """Atualiza a quantidade em estoque de um produto."""
        ...

    @abstractmethod
    def soft_delete(self, product_id: int) -> bool:
        """Exclusão lógica de um produto."""
        ...

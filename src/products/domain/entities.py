"""
Entidades de domínio - Product.
Classes Python puras, sem dependência do Django.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class ProductEntity:
    """
    Entidade de domínio representando um Produto.
    Independente do framework e do banco de dados.
    """

    id: Optional[int] = None
    sku: str = ""
    name: str = ""
    description: str = ""
    price: Decimal = Decimal("0.00")
    stock_quantity: int = 0
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def has_stock(self) -> bool:
        """Verifica se o produto tem estoque disponível."""
        return self.stock_quantity > 0

    def has_sufficient_stock(self, quantity: int) -> bool:
        """Verifica se há estoque suficiente para a quantidade solicitada."""
        return self.stock_quantity >= quantity

    def deduct_stock(self, quantity: int):
        """
        Deduz a quantidade do estoque.
        Deve ser chamado dentro de uma transação com lock.
        """
        if not self.has_sufficient_stock(quantity):
            raise ValueError(
                f"Estoque insuficiente para '{self.sku}'. "
                f"Disponível: {self.stock_quantity}, Solicitado: {quantity}"
            )
        self.stock_quantity -= quantity

    def restore_stock(self, quantity: int):
        """Restaura quantidade ao estoque (ex: cancelamento de pedido)."""
        self.stock_quantity += quantity

    def soft_delete(self):
        self.deleted_at = datetime.now()
        self.is_active = False

    def validate(self) -> list[str]:
        errors = []
        if not self.sku or not self.sku.strip():
            errors.append("O SKU do produto é obrigatório.")
        if not self.name or not self.name.strip():
            errors.append("O nome do produto é obrigatório.")
        if self.price <= 0:
            errors.append("O preço deve ser maior que zero.")
        if self.stock_quantity < 0:
            errors.append("A quantidade em estoque não pode ser negativa.")
        return errors

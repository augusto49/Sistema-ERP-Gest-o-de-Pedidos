"""
Serviço de Produtos — Camada de aplicação (Use Cases).
Orquestra regras de negócio e operações do repositório.
"""

import structlog

from products.domain.entities import ProductEntity
from products.repositories.interfaces import IProductRepository
from shared.exceptions.domain_exceptions import (
    BusinessRuleViolation,
    EntityNotFoundException,
)

logger = structlog.get_logger(__name__)


class ProductService:
    """
    Use Cases do módulo de Produtos.
    Recebe o repositório via injeção de dependência (DIP).
    """

    def __init__(self, repository: IProductRepository):
        self.repository = repository

    def create_product(self, data: dict) -> ProductEntity:
        """
        Cria um novo produto.
        Regras:
        - SKU deve ser único.
        - Preço deve ser positivo.
        - Estoque não pode ser negativo.
        """
        entity = ProductEntity(
            sku=data["sku"],
            name=data["name"],
            description=data.get("description", ""),
            price=data["price"],
            stock_quantity=data.get("stock_quantity", 0),
        )

        errors = entity.validate()
        if errors:
            raise BusinessRuleViolation(message=" | ".join(errors))

        if self.repository.get_by_sku(entity.sku):
            raise BusinessRuleViolation(
                message=f"Já existe um produto com o SKU '{entity.sku}'."
            )

        product = self.repository.create(entity)
        logger.info("product_created", product_id=product.id, sku=product.sku)
        return product

    def get_product(self, product_id: int) -> ProductEntity:
        """Busca um produto pelo ID. Lança exceção se não encontrado."""
        product = self.repository.get_by_id(product_id)
        if not product:
            raise EntityNotFoundException(entity="Produto", entity_id=product_id)
        return product

    def list_products(
        self, filters: dict = None, page: int = 1, page_size: int = 20
    ) -> tuple[list[ProductEntity], int]:
        """Lista produtos com filtros e paginação."""
        return self.repository.list_all(filters=filters, page=page, page_size=page_size)

    def update_product(self, product_id: int, data: dict) -> ProductEntity:
        """
        Atualiza um produto existente.
        Regras:
        - Produto deve existir.
        - Se alterar SKU, verificar unicidade.
        """
        existing = self.get_product(product_id)

        # Verificar unicidade de SKU se alterado
        new_sku = data.get("sku", existing.sku)
        if new_sku != existing.sku:
            if self.repository.get_by_sku(new_sku):
                raise BusinessRuleViolation(
                    message=f"Já existe um produto com o SKU '{new_sku}'."
                )

        existing.sku = new_sku
        existing.name = data.get("name", existing.name)
        existing.description = data.get("description", existing.description)
        existing.price = data.get("price", existing.price)
        existing.stock_quantity = data.get("stock_quantity", existing.stock_quantity)
        existing.is_active = data.get("is_active", existing.is_active)

        errors = existing.validate()
        if errors:
            raise BusinessRuleViolation(message=" | ".join(errors))

        product = self.repository.update(existing)
        logger.info("product_updated", product_id=product.id)
        return product

    def delete_product(self, product_id: int) -> bool:
        """Exclusão lógica de um produto."""
        self.get_product(product_id)
        deleted = self.repository.soft_delete(product_id)
        if deleted:
            logger.info("product_deleted", product_id=product_id)
        return deleted

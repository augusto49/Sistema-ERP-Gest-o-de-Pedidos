"""
Implementação concreta do repositório de Product usando Django ORM.
Inclui suporte a SELECT FOR UPDATE para controle de concorrência.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from products.domain.entities import ProductEntity
from products.models import Product
from products.repositories.interfaces import IProductRepository


class ProductRepository(IProductRepository):
    """
    Implementação do repositório de Produtos usando Django ORM.
    """

    def _to_entity(self, model: Product) -> ProductEntity:
        return ProductEntity(
            id=model.id,
            sku=model.sku,
            name=model.name,
            description=model.description,
            price=model.price,
            stock_quantity=model.stock_quantity,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

    def _get_active_queryset(self):
        return Product.objects.filter(deleted_at__isnull=True)

    def get_by_id(self, product_id: int) -> Optional[ProductEntity]:
        try:
            model = self._get_active_queryset().get(id=product_id)
            return self._to_entity(model)
        except Product.DoesNotExist:
            return None

    def get_by_sku(self, sku: str) -> Optional[ProductEntity]:
        try:
            model = self._get_active_queryset().get(sku=sku)
            return self._to_entity(model)
        except Product.DoesNotExist:
            return None

    def get_by_ids_for_update(self, product_ids: list[int]) -> list[ProductEntity]:
        """
        Busca produtos com SELECT FOR UPDATE (Pessimistic Lock).
        Ordena pelo ID para evitar deadlocks.
        DEVE ser usado dentro de transaction.atomic().
        """
        models = (
            self._get_active_queryset()
            .filter(id__in=product_ids)
            .select_for_update()
            .order_by("id")
        )
        return [self._to_entity(m) for m in models]

    def list_all(
        self, filters: Optional[dict] = None, page: int = 1, page_size: int = 20
    ) -> tuple[list[ProductEntity], int]:
        queryset = self._get_active_queryset()

        if filters:
            if "name" in filters:
                queryset = queryset.filter(name__icontains=filters["name"])
            if "sku" in filters:
                queryset = queryset.filter(sku__icontains=filters["sku"])
            if "is_active" in filters:
                queryset = queryset.filter(is_active=filters["is_active"])

        total = queryset.count()
        offset = (page - 1) * page_size
        product_models = queryset[offset : offset + page_size]

        return [self._to_entity(m) for m in product_models], total

    def create(self, entity: ProductEntity) -> ProductEntity:
        model = Product.objects.create(
            sku=entity.sku,
            name=entity.name,
            description=entity.description,
            price=entity.price,
            stock_quantity=entity.stock_quantity,
            is_active=entity.is_active,
        )
        return self._to_entity(model)

    def update(self, entity: ProductEntity) -> ProductEntity:
        Product.objects.filter(id=entity.id).update(
            sku=entity.sku,
            name=entity.name,
            description=entity.description,
            price=entity.price,
            stock_quantity=entity.stock_quantity,
            is_active=entity.is_active,
        )
        model = Product.objects.get(id=entity.id)
        return self._to_entity(model)

    def update_stock(self, product_id: int, new_quantity: int) -> bool:
        """Atualiza estoque. Deve ser usado dentro de transaction.atomic()."""
        updated = Product.objects.filter(
            id=product_id, deleted_at__isnull=True
        ).update(stock_quantity=new_quantity)
        return updated > 0

    def soft_delete(self, product_id: int) -> bool:
        updated = Product.objects.filter(
            id=product_id, deleted_at__isnull=True
        ).update(deleted_at=datetime.now(), is_active=False)
        return updated > 0

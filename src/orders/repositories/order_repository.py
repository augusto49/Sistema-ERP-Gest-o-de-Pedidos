"""
Implementação concreta do repositório de Order usando Django ORM.
"""

from datetime import datetime
from typing import Optional

from orders.domain.entities import OrderEntity, OrderItemEntity
from orders.domain.value_objects import OrderStatus
from orders.models import Order, OrderHistory, OrderItem
from orders.repositories.interfaces import IOrderRepository


class OrderRepository(IOrderRepository):
    """
    Implementação do repositório de Pedidos usando Django ORM.
    """

    def _to_entity(self, model: Order) -> OrderEntity:
        items = [
            OrderItemEntity(
                id=item.id,
                order_id=item.order_id,
                product_id=item.product_id,
                product_sku=item.product_sku,
                product_name=item.product_name,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
            for item in model.items.all()
        ]

        return OrderEntity(
            id=model.id,
            order_number=model.order_number,
            customer_id=model.customer_id,
            customer_name=model.customer.name,
            status=OrderStatus(model.status),
            items=items,
            notes=model.notes,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

    def _get_active_queryset(self):
        return Order.objects.filter(deleted_at__isnull=True).select_related("customer")

    def get_by_id(self, order_id: int) -> Optional[OrderEntity]:
        try:
            model = (
                self._get_active_queryset()
                .prefetch_related("items")
                .get(id=order_id)
            )
            return self._to_entity(model)
        except Order.DoesNotExist:
            return None

    def list_all(
        self, filters: Optional[dict] = None, page: int = 1, page_size: int = 20
    ) -> tuple[list[OrderEntity], int]:
        queryset = self._get_active_queryset().prefetch_related("items")

        if filters:
            if "status" in filters:
                queryset = queryset.filter(status=filters["status"])
            if "customer_id" in filters:
                queryset = queryset.filter(customer_id=filters["customer_id"])
            if "date_from" in filters:
                queryset = queryset.filter(created_at__gte=filters["date_from"])
            if "date_to" in filters:
                queryset = queryset.filter(created_at__lte=filters["date_to"])

        total = queryset.count()
        offset = (page - 1) * page_size
        order_models = queryset[offset : offset + page_size]

        return [self._to_entity(m) for m in order_models], total

    def list_by_customer(
        self, customer_id: int, page: int = 1, page_size: int = 20
    ) -> tuple[list[OrderEntity], int]:
        return self.list_all(filters={"customer_id": customer_id}, page=page, page_size=page_size)

    def create(self, entity: OrderEntity) -> OrderEntity:
        order_model = Order.objects.create(
            customer_id=entity.customer_id,
            status=entity.status.value,
            notes=entity.notes,
        )

        for item in entity.items:
            OrderItem.objects.create(
                order=order_model,
                product_id=item.product_id,
                product_sku=item.product_sku,
                product_name=item.product_name,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )

        # Registrar no histórico
        OrderHistory.objects.create(
            order=order_model,
            from_status="",
            to_status=OrderStatus.PENDING.value,
            changed_by="system",
            notes="Pedido criado.",
        )

        return self.get_by_id(order_model.id)

    def update_status(self, order_id: int, new_status: str, notes: str = "", changed_by: str = "system") -> bool:
        try:
            order = Order.objects.get(id=order_id, deleted_at__isnull=True)
        except Order.DoesNotExist:
            return False

        old_status = order.status
        order.status = new_status
        order.save(update_fields=["status", "updated_at"])

        OrderHistory.objects.create(
            order=order,
            from_status=old_status,
            to_status=new_status,
            changed_by=changed_by,
            notes=notes,
        )

        return True

    def soft_delete(self, order_id: int) -> bool:
        updated = Order.objects.filter(
            id=order_id, deleted_at__isnull=True
        ).update(deleted_at=datetime.now())
        return updated > 0

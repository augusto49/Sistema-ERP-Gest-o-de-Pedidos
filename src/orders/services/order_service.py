"""
Serviço de Pedidos — Camada de aplicação (Use Cases).
Orquestra transações, regras de negócio, controle de estoque
e publicação de eventos de domínio.
"""

import structlog
from django.db import transaction

from customers.repositories.interfaces import ICustomerRepository
from orders.domain.entities import OrderEntity, OrderItemEntity
from orders.domain.value_objects import OrderStatus
from orders.repositories.interfaces import IOrderRepository
from products.repositories.interfaces import IProductRepository
from shared.events.event_bus import EventBus
from shared.exceptions.domain_exceptions import (
    BusinessRuleViolation,
    EntityNotFoundException,
    InsufficientStockException,
    InvalidStateTransitionException,
)

logger = structlog.get_logger(__name__)


class OrderService:
    """
    Use Cases do módulo de Pedidos.
    Orquestra múltiplos repositórios dentro de transações.
    """

    def __init__(
        self,
        order_repository: IOrderRepository,
        product_repository: IProductRepository,
        customer_repository: ICustomerRepository,
        event_bus: EventBus = None,
    ):
        self.order_repository = order_repository
        self.product_repository = product_repository
        self.customer_repository = customer_repository
        self.event_bus = event_bus or EventBus()

    def create_order(self, data: dict) -> OrderEntity:
        """
        Cria um novo pedido com controle de estoque atômico.

        Fluxo:
        1. Validar se o cliente existe.
        2. Dentro de transaction.atomic():
           a. Buscar produtos com SELECT FOR UPDATE (pessimistic lock).
           b. Verificar estoque de cada item.
           c. Deduzir estoque.
           d. Criar pedido com items.
        3. Publicar evento de domínio.
        """
        customer_id = data["customer_id"]
        items_data = data["items"]
        notes = data.get("notes", "")

        # 1. Validar cliente
        customer = self.customer_repository.get_by_id(customer_id)
        if not customer:
            raise EntityNotFoundException(entity="Cliente", entity_id=customer_id)

        if not customer.is_active:
            raise BusinessRuleViolation(
                message="Não é possível criar pedido para um cliente inativo."
            )

        if not items_data:
            raise BusinessRuleViolation(
                message="O pedido deve ter pelo menos um item."
            )

        # 2. Transação atômica com lock de estoque
        with transaction.atomic():
            product_ids = [item["product_id"] for item in items_data]

            # 2a. SELECT FOR UPDATE — ordena por ID para evitar deadlock
            locked_products = self.product_repository.get_by_ids_for_update(product_ids)

            # Mapear produtos por ID para acesso rápido
            product_map = {p.id: p for p in locked_products}

            # Verificar se todos os produtos existem
            for item_data in items_data:
                pid = item_data["product_id"]
                if pid not in product_map:
                    raise EntityNotFoundException(entity="Produto", entity_id=pid)

            # 2b/2c. Verificar e deduzir estoque
            order_items = []
            for item_data in items_data:
                product = product_map[item_data["product_id"]]
                quantity = item_data["quantity"]

                if not product.is_active:
                    raise BusinessRuleViolation(
                        message=f"O produto '{product.sku}' está inativo."
                    )

                if not product.has_sufficient_stock(quantity):
                    raise InsufficientStockException(
                        product_sku=product.sku,
                        requested=quantity,
                        available=product.stock_quantity,
                    )

                # Deduzir estoque
                product.deduct_stock(quantity)
                self.product_repository.update_stock(product.id, product.stock_quantity)

                order_items.append(
                    OrderItemEntity(
                        product_id=product.id,
                        product_sku=product.sku,
                        product_name=product.name,
                        quantity=quantity,
                        unit_price=product.price,
                    )
                )

            # 2d. Criar pedido
            order_entity = OrderEntity(
                customer_id=customer_id,
                customer_name=customer.name,
                status=OrderStatus.PENDING,
                items=order_items,
                notes=notes,
            )

            # Validar entidade
            errors = order_entity.validate()
            if errors:
                raise BusinessRuleViolation(message=" | ".join(errors))

            order = self.order_repository.create(order_entity)

        # 3. Publicar evento fora da transação
        logger.info(
            "order_created",
            order_id=order.id,
            customer_id=customer_id,
            total=str(order.total),
            items_count=len(order.items),
        )
        self.event_bus.publish("order_created", {
            "order_id": order.id,
            "customer_id": customer_id,
            "total": str(order.total),
        })

        return order

    def get_order(self, order_id: int) -> OrderEntity:
        """Busca um pedido pelo ID com seus itens."""
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise EntityNotFoundException(entity="Pedido", entity_id=order_id)
        return order

    def list_orders(
        self, filters: dict = None, page: int = 1, page_size: int = 20
    ) -> tuple[list[OrderEntity], int]:
        """Lista pedidos com filtros e paginação."""
        return self.order_repository.list_all(
            filters=filters, page=page, page_size=page_size
        )

    def list_orders_by_customer(
        self, customer_id: int, page: int = 1, page_size: int = 20
    ) -> tuple[list[OrderEntity], int]:
        """Lista pedidos de um cliente específico."""
        # Verificar se cliente existe
        customer = self.customer_repository.get_by_id(customer_id)
        if not customer:
            raise EntityNotFoundException(entity="Cliente", entity_id=customer_id)

        return self.order_repository.list_by_customer(
            customer_id=customer_id, page=page, page_size=page_size
        )

    def update_status(
        self, order_id: int, new_status: str, notes: str = ""
    ) -> OrderEntity:
        """
        Atualiza o status de um pedido com validação de transição.
        Fluxo: PENDENTE → CONFIRMADO → SEPARADO → ENVIADO → ENTREGUE
        Cancelamento: apenas PENDENTE ou CONFIRMADO → CANCELADO
        """
        order = self.get_order(order_id)

        try:
            new_status_enum = OrderStatus(new_status)
        except ValueError:
            raise BusinessRuleViolation(
                message=f"Status '{new_status}' inválido. "
                f"Valores aceitos: {[s.value for s in OrderStatus]}"
            )

        # Validar transição via máquina de estados da entidade
        order.transition_to(new_status_enum)

        self.order_repository.update_status(
            order_id=order_id,
            new_status=new_status_enum.value,
            notes=notes,
        )

        logger.info(
            "order_status_updated",
            order_id=order_id,
            from_status=order.status.value,
            to_status=new_status_enum.value,
        )

        self.event_bus.publish("order_status_updated", {
            "order_id": order_id,
            "new_status": new_status_enum.value,
        })

        return self.get_order(order_id)

    def cancel_order(self, order_id: int, reason: str = "") -> OrderEntity:
        """
        Cancela um pedido e restaura o estoque.
        Só é permitido para pedidos com status PENDENTE ou CONFIRMADO.
        """
        order = self.get_order(order_id)

        # Validar transição (a entidade verifica internamente)
        order.transition_to(OrderStatus.CANCELLED)

        with transaction.atomic():
            # Restaurar estoque dos produtos
            product_ids = [item.product_id for item in order.items]
            locked_products = self.product_repository.get_by_ids_for_update(product_ids)
            product_map = {p.id: p for p in locked_products}

            for item in order.items:
                product = product_map.get(item.product_id)
                if product:
                    product.restore_stock(item.quantity)
                    self.product_repository.update_stock(
                        product.id, product.stock_quantity
                    )

            # Atualizar status do pedido
            self.order_repository.update_status(
                order_id=order_id,
                new_status=OrderStatus.CANCELLED.value,
                notes=reason or "Pedido cancelado.",
            )

        logger.info("order_cancelled", order_id=order_id, reason=reason)
        self.event_bus.publish("order_cancelled", {
            "order_id": order_id,
            "reason": reason,
        })

        return self.get_order(order_id)

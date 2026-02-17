"""
Testes unitários para Order entities e value objects.
Inclui testes da máquina de estados de transição de status.
"""

from decimal import Decimal

import pytest

from orders.domain.entities import OrderEntity, OrderItemEntity
from orders.domain.value_objects import OrderStatus
from shared.exceptions.domain_exceptions import InvalidStateTransitionException


class TestOrderStatus:
    """Testes para o Value Object OrderStatus."""

    def test_transicao_pendente_para_confirmado(self):
        assert OrderStatus.PENDING.can_transition_to(OrderStatus.CONFIRMED) is True

    def test_transicao_confirmado_para_separado(self):
        assert OrderStatus.CONFIRMED.can_transition_to(OrderStatus.SEPARATED) is True

    def test_transicao_separado_para_enviado(self):
        assert OrderStatus.SEPARATED.can_transition_to(OrderStatus.SHIPPED) is True

    def test_transicao_enviado_para_entregue(self):
        assert OrderStatus.SHIPPED.can_transition_to(OrderStatus.DELIVERED) is True

    def test_cancelamento_de_pendente(self):
        assert OrderStatus.PENDING.can_transition_to(OrderStatus.CANCELLED) is True

    def test_cancelamento_de_confirmado(self):
        assert OrderStatus.CONFIRMED.can_transition_to(OrderStatus.CANCELLED) is True

    def test_cancelamento_invalido_de_separado(self):
        assert OrderStatus.SEPARATED.can_transition_to(OrderStatus.CANCELLED) is False

    def test_cancelamento_invalido_de_enviado(self):
        assert OrderStatus.SHIPPED.can_transition_to(OrderStatus.CANCELLED) is False

    def test_cancelamento_invalido_de_entregue(self):
        assert OrderStatus.DELIVERED.can_transition_to(OrderStatus.CANCELLED) is False

    def test_entregue_eh_estado_final(self):
        transitions = OrderStatus.valid_transitions()
        assert transitions[OrderStatus.DELIVERED] == []

    def test_cancelado_eh_estado_final(self):
        transitions = OrderStatus.valid_transitions()
        assert transitions[OrderStatus.CANCELLED] == []

    def test_transicao_invalida_pular_status(self):
        """Não pode pular de PENDENTE direto para ENVIADO."""
        assert OrderStatus.PENDING.can_transition_to(OrderStatus.SHIPPED) is False


class TestOrderItemEntity:
    """Testes para OrderItemEntity."""

    def test_calculo_subtotal(self):
        item = OrderItemEntity(
            product_id=1,
            product_sku="SKU-001",
            product_name="Produto A",
            quantity=3,
            unit_price=Decimal("25.50"),
        )
        assert item.subtotal == Decimal("76.50")


class TestOrderEntity:
    """Testes para OrderEntity."""

    def _create_order_with_items(self) -> OrderEntity:
        return OrderEntity(
            customer_id=1,
            customer_name="João",
            status=OrderStatus.PENDING,
            items=[
                OrderItemEntity(
                    product_id=1,
                    product_sku="SKU-001",
                    product_name="Produto A",
                    quantity=2,
                    unit_price=Decimal("50.00"),
                ),
                OrderItemEntity(
                    product_id=2,
                    product_sku="SKU-002",
                    product_name="Produto B",
                    quantity=1,
                    unit_price=Decimal("30.00"),
                ),
            ],
        )

    def test_calcular_total(self):
        order = self._create_order_with_items()
        # (2 * 50) + (1 * 30) = 130
        assert order.total == Decimal("130.00")

    def test_total_items(self):
        order = self._create_order_with_items()
        assert order.total_items == 3

    def test_validar_pedido_sem_items(self):
        order = OrderEntity(customer_id=1)
        errors = order.validate()
        assert any("pelo menos um item" in e.lower() for e in errors)

    def test_validar_pedido_sem_cliente(self):
        order = OrderEntity(
            items=[
                OrderItemEntity(
                    product_id=1, product_sku="X", product_name="Y",
                    quantity=1, unit_price=Decimal("10"),
                )
            ]
        )
        errors = order.validate()
        assert any("cliente" in e.lower() for e in errors)

    def test_fluxo_completo_de_status(self):
        """Testa o fluxo: PENDENTE → CONFIRMADO → SEPARADO → ENVIADO → ENTREGUE"""
        order = self._create_order_with_items()

        order.confirm()
        assert order.status == OrderStatus.CONFIRMED

        order.separate()
        assert order.status == OrderStatus.SEPARATED

        order.ship()
        assert order.status == OrderStatus.SHIPPED

        order.deliver()
        assert order.status == OrderStatus.DELIVERED

    def test_cancelamento_de_pedido_pendente(self):
        order = self._create_order_with_items()
        order.cancel()
        assert order.status == OrderStatus.CANCELLED

    def test_cancelamento_de_pedido_confirmado(self):
        order = self._create_order_with_items()
        order.confirm()
        order.cancel()
        assert order.status == OrderStatus.CANCELLED

    def test_cancelamento_invalido_de_pedido_enviado(self):
        order = self._create_order_with_items()
        order.confirm()
        order.separate()
        order.ship()

        with pytest.raises(InvalidStateTransitionException):
            order.cancel()

    def test_transicao_invalida_lanca_excecao(self):
        order = self._create_order_with_items()
        with pytest.raises(InvalidStateTransitionException):
            order.ship()  # Não pode ir de PENDENTE direto para SHIPPED

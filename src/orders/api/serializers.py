"""
Serializers (DTOs) do módulo de Pedidos.
Inclui serializers aninhados para itens do pedido.
"""

from rest_framework import serializers

from orders.domain.value_objects import OrderStatus


class OrderItemInputSerializer(serializers.Serializer):
    """DTO de entrada para um item do pedido."""

    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class OrderInputSerializer(serializers.Serializer):
    """DTO de entrada para criação de Pedido."""

    customer_id = serializers.IntegerField()
    items = OrderItemInputSerializer(many=True, min_length=1)
    notes = serializers.CharField(required=False, default="")


class OrderStatusUpdateSerializer(serializers.Serializer):
    """DTO para atualização de status do pedido."""

    status = serializers.ChoiceField(
        choices=[(s.value, s.name) for s in OrderStatus]
    )
    notes = serializers.CharField(required=False, default="")


class OrderCancelSerializer(serializers.Serializer):
    """DTO para cancelamento de pedido."""

    reason = serializers.CharField(required=False, default="")


# --- Serializers de Saída ---


class OrderItemOutputSerializer(serializers.Serializer):
    """DTO de saída para item do pedido."""

    id = serializers.IntegerField(read_only=True)
    product_id = serializers.IntegerField(read_only=True)
    product_sku = serializers.CharField(read_only=True)
    product_name = serializers.CharField(read_only=True)
    quantity = serializers.IntegerField(read_only=True)
    unit_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    subtotal = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )


class OrderOutputSerializer(serializers.Serializer):
    """DTO de saída para pedido completo."""

    id = serializers.IntegerField(read_only=True)
    customer_id = serializers.IntegerField(read_only=True)
    customer_name = serializers.CharField(read_only=True)
    status = serializers.SerializerMethodField()
    items = OrderItemOutputSerializer(many=True, read_only=True)
    total = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    total_items = serializers.IntegerField(read_only=True)
    notes = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def get_status(self, obj) -> str:
        """Retorna o valor string do enum OrderStatus."""
        if hasattr(obj.status, "value"):
            return obj.status.value
        return str(obj.status)

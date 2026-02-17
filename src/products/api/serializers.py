"""
Serializers (DTOs) do módulo de Produtos.
"""

from rest_framework import serializers


class ProductInputSerializer(serializers.Serializer):
    """DTO de entrada para criação/atualização de Produto."""

    sku = serializers.CharField(max_length=50)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, default="")
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = serializers.IntegerField(required=False, default=0, min_value=0)
    is_active = serializers.BooleanField(required=False, default=True)


class ProductOutputSerializer(serializers.Serializer):
    """DTO de saída para resposta da API."""

    id = serializers.IntegerField(read_only=True)
    sku = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    stock_quantity = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class StockUpdateSerializer(serializers.Serializer):
    """DTO para atualização de estoque de produto."""

    quantity = serializers.IntegerField(
        help_text="Quantidade a adicionar (positivo) ou subtrair (negativo)."
    )


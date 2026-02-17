"""
Serializers (DTOs) do módulo de Clientes.
Responsáveis pela validação e transformação de entrada/saída da API.
"""

from rest_framework import serializers


class CustomerInputSerializer(serializers.Serializer):
    """DTO de entrada para criação/atualização de Cliente."""

    name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    cpf_cnpj = serializers.CharField(max_length=18)
    phone = serializers.CharField(max_length=20, required=False, default="")
    address = serializers.CharField(required=False, default="")
    is_active = serializers.BooleanField(required=False, default=True)


class CustomerOutputSerializer(serializers.Serializer):
    """DTO de saída para resposta da API."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    cpf_cnpj = serializers.CharField(read_only=True)
    phone = serializers.CharField(read_only=True)
    address = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

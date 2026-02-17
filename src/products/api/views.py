"""
Views (Controllers) do módulo de Produtos.
"""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from products.api.serializers import (
    ProductInputSerializer,
    ProductOutputSerializer,
    StockUpdateSerializer,
)
from products.repositories.product_repository import ProductRepository
from products.services.product_service import ProductService


def _get_service() -> ProductService:
    return ProductService(repository=ProductRepository())


class ProductViewSet(ViewSet):
    """
    API REST para gerenciamento de Produtos.

    Endpoints:
        GET    /api/v1/products/               → list
        POST   /api/v1/products/               → create
        GET    /api/v1/products/{id}/           → retrieve
        PUT    /api/v1/products/{id}/           → update
        DELETE /api/v1/products/{id}/           → destroy (soft delete)
        PATCH  /api/v1/products/{id}/stock/     → update_stock
    """

    def list(self, request):
        service = _get_service()
        filters = {}

        if request.query_params.get("name"):
            filters["name"] = request.query_params["name"]
        if request.query_params.get("sku"):
            filters["sku"] = request.query_params["sku"]
        if request.query_params.get("is_active") is not None:
            filters["is_active"] = request.query_params["is_active"].lower() == "true"

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))

        products, total = service.list_products(
            filters=filters, page=page, page_size=page_size
        )

        serializer = ProductOutputSerializer(products, many=True)
        return Response({
            "count": total,
            "page": page,
            "page_size": page_size,
            "results": serializer.data,
        })

    def create(self, request):
        service = _get_service()
        input_serializer = ProductInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        product = service.create_product(input_serializer.validated_data)

        output_serializer = ProductOutputSerializer(product)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        service = _get_service()
        product = service.get_product(int(pk))

        serializer = ProductOutputSerializer(product)
        return Response(serializer.data)

    def update(self, request, pk=None):
        service = _get_service()
        input_serializer = ProductInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        product = service.update_product(int(pk), input_serializer.validated_data)

        output_serializer = ProductOutputSerializer(product)
        return Response(output_serializer.data)

    def destroy(self, request, pk=None):
        service = _get_service()
        service.delete_product(int(pk))
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["patch"], url_path="stock")
    def update_stock(self, request, pk=None):
        """
        Atualiza o estoque de um produto.
        Envie { "quantity": 10 } para adicionar ou { "quantity": -5 } para subtrair.
        """
        service = _get_service()
        input_serializer = StockUpdateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        product = service.update_stock(
            product_id=int(pk),
            quantity=input_serializer.validated_data["quantity"],
        )

        output_serializer = ProductOutputSerializer(product)
        return Response(output_serializer.data)


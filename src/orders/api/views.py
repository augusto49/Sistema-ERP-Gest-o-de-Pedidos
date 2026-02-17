"""
Views (Controllers) do módulo de Pedidos.
Inclui endpoints customizados para transição de status e cancelamento.
"""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from customers.repositories.customer_repository import CustomerRepository
from orders.api.serializers import (
    OrderCancelSerializer,
    OrderInputSerializer,
    OrderOutputSerializer,
    OrderStatusUpdateSerializer,
)
from orders.repositories.order_repository import OrderRepository
from orders.services.order_service import OrderService
from products.repositories.product_repository import ProductRepository


def _get_service() -> OrderService:
    return OrderService(
        order_repository=OrderRepository(),
        product_repository=ProductRepository(),
        customer_repository=CustomerRepository(),
    )


class OrderViewSet(ViewSet):
    """
    API REST para gerenciamento de Pedidos.

    Endpoints:
        GET    /api/v1/orders/                      → list
        POST   /api/v1/orders/                      → create
        GET    /api/v1/orders/{id}/                  → retrieve
        DELETE /api/v1/orders/{id}/                  → destroy (soft delete)
        PATCH  /api/v1/orders/{id}/status/           → update_status
        POST   /api/v1/orders/{id}/cancel/           → cancel
        GET    /api/v1/orders/customer/{customer_id}/ → by_customer
    """

    def list(self, request):
        """Lista pedidos com filtros e paginação."""
        service = _get_service()
        filters = {}

        if request.query_params.get("status"):
            filters["status"] = request.query_params["status"]
        if request.query_params.get("customer_id"):
            filters["customer_id"] = int(request.query_params["customer_id"])

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))

        orders, total = service.list_orders(
            filters=filters, page=page, page_size=page_size
        )

        serializer = OrderOutputSerializer(orders, many=True)
        return Response({
            "count": total,
            "page": page,
            "page_size": page_size,
            "results": serializer.data,
        })

    def create(self, request):
        """Cria um novo pedido (com verificação e dedução atômica de estoque)."""
        service = _get_service()
        input_serializer = OrderInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        order = service.create_order(input_serializer.validated_data)

        output_serializer = OrderOutputSerializer(order)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        """Busca um pedido pelo ID com seus itens."""
        service = _get_service()
        order = service.get_order(int(pk))

        serializer = OrderOutputSerializer(order)
        return Response(serializer.data)

    def destroy(self, request, pk=None):
        """Exclusão lógica de um pedido."""
        service = _get_service()
        service.delete_order(int(pk))
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["patch"], url_path="status")
    def update_status(self, request, pk=None):
        """
        Atualiza o status de um pedido.
        Respeita a máquina de estados:
        PENDENTE → CONFIRMADO → SEPARADO → ENVIADO → ENTREGUE
        """
        service = _get_service()
        input_serializer = OrderStatusUpdateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        order = service.update_status(
            order_id=int(pk),
            new_status=input_serializer.validated_data["status"],
            notes=input_serializer.validated_data.get("notes", ""),
            changed_by=getattr(request.user, "username", None) or "anonymous",
        )

        output_serializer = OrderOutputSerializer(order)
        return Response(output_serializer.data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        """
        Cancela um pedido e restaura o estoque.
        Só permitido para PENDENTE ou CONFIRMADO.
        """
        service = _get_service()
        input_serializer = OrderCancelSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        order = service.cancel_order(
            order_id=int(pk),
            reason=input_serializer.validated_data.get("reason", ""),
            changed_by=getattr(request.user, "username", None) or "anonymous",
        )

        output_serializer = OrderOutputSerializer(order)
        return Response(output_serializer.data)

    @action(detail=False, methods=["get"], url_path=r"customer/(?P<customer_id>\d+)")
    def by_customer(self, request, customer_id=None):
        """Lista pedidos de um cliente específico."""
        service = _get_service()
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))

        orders, total = service.list_orders_by_customer(
            customer_id=int(customer_id), page=page, page_size=page_size
        )

        serializer = OrderOutputSerializer(orders, many=True)
        return Response({
            "count": total,
            "page": page,
            "page_size": page_size,
            "results": serializer.data,
        })

"""
Views (Controllers) do módulo de Clientes.
Recebem requisições HTTP, delegam aos Services e retornam respostas.
"""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from customers.api.serializers import CustomerInputSerializer, CustomerOutputSerializer
from customers.repositories.customer_repository import CustomerRepository
from customers.services.customer_service import CustomerService


def _get_service() -> CustomerService:
    """Factory para instanciar o service com suas dependências."""
    return CustomerService(repository=CustomerRepository())


class CustomerViewSet(ViewSet):
    """
    API REST para gerenciamento de Clientes.

    Endpoints:
        GET    /api/v1/customers/           → list
        POST   /api/v1/customers/           → create
        GET    /api/v1/customers/{id}/       → retrieve
        PUT    /api/v1/customers/{id}/       → update
        DELETE /api/v1/customers/{id}/       → destroy (soft delete)
    """

    def list(self, request):
        """Lista clientes com filtros e paginação."""
        service = _get_service()
        filters = {}

        if request.query_params.get("name"):
            filters["name"] = request.query_params["name"]
        if request.query_params.get("email"):
            filters["email"] = request.query_params["email"]
        if request.query_params.get("is_active") is not None:
            filters["is_active"] = request.query_params["is_active"].lower() == "true"

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))

        customers, total = service.list_customers(
            filters=filters, page=page, page_size=page_size
        )

        serializer = CustomerOutputSerializer(customers, many=True)
        return Response({
            "count": total,
            "page": page,
            "page_size": page_size,
            "results": serializer.data,
        })

    def create(self, request):
        """Cria um novo cliente."""
        service = _get_service()
        input_serializer = CustomerInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        customer = service.create_customer(input_serializer.validated_data)

        output_serializer = CustomerOutputSerializer(customer)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        """Busca um cliente pelo ID."""
        service = _get_service()
        customer = service.get_customer(int(pk))

        serializer = CustomerOutputSerializer(customer)
        return Response(serializer.data)

    def update(self, request, pk=None):
        """Atualiza um cliente existente."""
        service = _get_service()
        input_serializer = CustomerInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        customer = service.update_customer(int(pk), input_serializer.validated_data)

        output_serializer = CustomerOutputSerializer(customer)
        return Response(output_serializer.data)

    def destroy(self, request, pk=None):
        """Exclusão lógica de um cliente."""
        service = _get_service()
        service.delete_customer(int(pk))
        return Response(status=status.HTTP_204_NO_CONTENT)

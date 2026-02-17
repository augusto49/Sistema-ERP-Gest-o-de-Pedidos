"""
Testes de integração da API — Orders.
Testa criação com estoque, transições de status e cancelamento.
"""

import pytest
from rest_framework import status


@pytest.mark.django_db
class TestOrderAPI:
    """Testes de integração para endpoints de Pedidos."""

    ENDPOINT = "/api/v1/orders/"
    CUSTOMERS_ENDPOINT = "/api/v1/customers/"
    PRODUCTS_ENDPOINT = "/api/v1/products/"

    def _setup_customer(self, api_client):
        response = api_client.post(
            self.CUSTOMERS_ENDPOINT,
            {"name": "Cliente Teste", "email": "cliente@test.com", "cpf_cnpj": "111"},
            format="json",
        )
        return response.data["id"]

    def _setup_product(self, api_client, sku="SKU-001", stock=50, price="100.00"):
        response = api_client.post(
            self.PRODUCTS_ENDPOINT,
            {"sku": sku, "name": f"Produto {sku}", "price": price, "stock_quantity": stock},
            format="json",
        )
        return response.data["id"]

    def _create_order(self, api_client, customer_id, items):
        return api_client.post(
            self.ENDPOINT,
            {"customer_id": customer_id, "items": items},
            format="json",
        )

    def test_criar_pedido(self, api_client):
        customer_id = self._setup_customer(api_client)
        product_id = self._setup_product(api_client)

        response = self._create_order(
            api_client, customer_id, [{"product_id": product_id, "quantity": 2}]
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "pending"
        assert response.data["customer_id"] == customer_id
        assert len(response.data["items"]) == 1
        assert response.data["total"] == "200.00"

    def test_criar_pedido_deduz_estoque(self, api_client):
        customer_id = self._setup_customer(api_client)
        product_id = self._setup_product(api_client, stock=10)

        self._create_order(
            api_client, customer_id, [{"product_id": product_id, "quantity": 3}]
        )

        # Verificar que estoque foi deduzido
        product_response = api_client.get(f"{self.PRODUCTS_ENDPOINT}{product_id}/")
        assert product_response.data["stock_quantity"] == 7

    def test_criar_pedido_estoque_insuficiente(self, api_client):
        customer_id = self._setup_customer(api_client)
        product_id = self._setup_product(api_client, stock=5)

        response = self._create_order(
            api_client, customer_id, [{"product_id": product_id, "quantity": 10}]
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_criar_pedido_cliente_inexistente(self, api_client):
        product_id = self._setup_product(api_client)

        response = self._create_order(
            api_client, 9999, [{"product_id": product_id, "quantity": 1}]
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_buscar_pedido_por_id(self, api_client):
        customer_id = self._setup_customer(api_client)
        product_id = self._setup_product(api_client)

        create_response = self._create_order(
            api_client, customer_id, [{"product_id": product_id, "quantity": 1}]
        )
        order_id = create_response.data["id"]

        response = api_client.get(f"{self.ENDPOINT}{order_id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == order_id

    def test_fluxo_completo_status(self, api_client):
        """Testa: PENDENTE → CONFIRMADO → SEPARADO → ENVIADO → ENTREGUE"""
        customer_id = self._setup_customer(api_client)
        product_id = self._setup_product(api_client)

        create_response = self._create_order(
            api_client, customer_id, [{"product_id": product_id, "quantity": 1}]
        )
        order_id = create_response.data["id"]

        # PENDENTE → CONFIRMADO
        resp = api_client.patch(
            f"{self.ENDPOINT}{order_id}/status/",
            {"status": "confirmed"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["status"] == "confirmed"

        # CONFIRMADO → SEPARADO
        resp = api_client.patch(
            f"{self.ENDPOINT}{order_id}/status/",
            {"status": "separated"},
            format="json",
        )
        assert resp.data["status"] == "separated"

        # SEPARADO → ENVIADO
        resp = api_client.patch(
            f"{self.ENDPOINT}{order_id}/status/",
            {"status": "shipped"},
            format="json",
        )
        assert resp.data["status"] == "shipped"

        # ENVIADO → ENTREGUE
        resp = api_client.patch(
            f"{self.ENDPOINT}{order_id}/status/",
            {"status": "delivered"},
            format="json",
        )
        assert resp.data["status"] == "delivered"

    def test_transicao_invalida_status(self, api_client):
        """Não pode ir de PENDENTE direto para SHIPPED."""
        customer_id = self._setup_customer(api_client)
        product_id = self._setup_product(api_client)

        create_response = self._create_order(
            api_client, customer_id, [{"product_id": product_id, "quantity": 1}]
        )
        order_id = create_response.data["id"]

        resp = api_client.patch(
            f"{self.ENDPOINT}{order_id}/status/",
            {"status": "shipped"},
            format="json",
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_cancelar_pedido_pendente(self, api_client):
        customer_id = self._setup_customer(api_client)
        product_id = self._setup_product(api_client, stock=10)

        create_response = self._create_order(
            api_client, customer_id, [{"product_id": product_id, "quantity": 3}]
        )
        order_id = create_response.data["id"]

        # Cancelar
        resp = api_client.post(
            f"{self.ENDPOINT}{order_id}/cancel/",
            {"reason": "Desistência"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["status"] == "cancelled"

        # Verificar que estoque foi restaurado
        product_response = api_client.get(f"{self.PRODUCTS_ENDPOINT}{product_id}/")
        assert product_response.data["stock_quantity"] == 10

    def test_cancelar_pedido_enviado_invalido(self, api_client):
        """Não pode cancelar pedido já enviado."""
        customer_id = self._setup_customer(api_client)
        product_id = self._setup_product(api_client)

        create_response = self._create_order(
            api_client, customer_id, [{"product_id": product_id, "quantity": 1}]
        )
        order_id = create_response.data["id"]

        # Avançar status até ENVIADO
        api_client.patch(f"{self.ENDPOINT}{order_id}/status/", {"status": "confirmed"}, format="json")
        api_client.patch(f"{self.ENDPOINT}{order_id}/status/", {"status": "separated"}, format="json")
        api_client.patch(f"{self.ENDPOINT}{order_id}/status/", {"status": "shipped"}, format="json")

        # Tentar cancelar
        resp = api_client.post(f"{self.ENDPOINT}{order_id}/cancel/", {}, format="json")
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

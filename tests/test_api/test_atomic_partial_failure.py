"""
Teste de Atomicidade em Falha Parcial.

Cenário: Pedido com 3 itens. Item 1 e 2 têm estoque, item 3 não tem.
Resultado esperado: O pedido deve falhar completamente. Nenhum estoque
deve ser reservado (all-or-nothing).
Teste: Validar que o estoque dos itens 1 e 2 não foi alterado após a falha.
"""

import uuid

import pytest
from rest_framework import status


@pytest.mark.django_db
class TestAtomicPartialFailure:
    """Testa que falha parcial de estoque causa rollback total."""

    ENDPOINT = "/api/v1/orders/"
    CUSTOMERS_ENDPOINT = "/api/v1/customers/"
    PRODUCTS_ENDPOINT = "/api/v1/products/"

    def _setup_customer(self, client):
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            self.CUSTOMERS_ENDPOINT,
            {"name": f"Cliente {uid}", "email": f"{uid}@test.com", "cpf_cnpj": uid},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        return resp.data["id"]

    def _setup_product(self, client, name, stock, price="100.00"):
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            self.PRODUCTS_ENDPOINT,
            {"sku": f"ATOM-{uid}", "name": name, "price": price, "stock_quantity": stock},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        return resp.data["id"]

    def test_partial_failure_rolls_back_all_stock(self, api_client):
        """
        Cenário principal: 3 itens, item 3 sem estoque.
        O pedido deve falhar e nenhum estoque deve ser reservado.
        """
        customer_id = self._setup_customer(api_client)

        # Item 1: 20 unidades em estoque (pedido quer 5)
        prod1_id = self._setup_product(api_client, "Produto A", stock=20)
        # Item 2: 30 unidades em estoque (pedido quer 10)
        prod2_id = self._setup_product(api_client, "Produto B", stock=30)
        # Item 3: 2 unidades em estoque (pedido quer 15 → insuficiente!)
        prod3_id = self._setup_product(api_client, "Produto C", stock=2)

        # Tentar criar pedido com os 3 itens
        response = api_client.post(
            self.ENDPOINT,
            {
                "customer_id": customer_id,
                "items": [
                    {"product_id": prod1_id, "quantity": 5},
                    {"product_id": prod2_id, "quantity": 10},
                    {"product_id": prod3_id, "quantity": 15},  # SEM ESTOQUE
                ],
            },
            format="json",
        )

        # Pedido deve ser rejeitado
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, (
            f"Esperado 422, recebeu {response.status_code}: {response.data}"
        )

        # Estoque do Produto A NÃO deve ter sido alterado (ainda 20)
        p1 = api_client.get(f"{self.PRODUCTS_ENDPOINT}{prod1_id}/")
        assert p1.data["stock_quantity"] == 20, (
            f"Estoque do Produto A deveria ser 20, mas é {p1.data['stock_quantity']}. "
            f"Rollback falhou!"
        )

        # Estoque do Produto B NÃO deve ter sido alterado (ainda 30)
        p2 = api_client.get(f"{self.PRODUCTS_ENDPOINT}{prod2_id}/")
        assert p2.data["stock_quantity"] == 30, (
            f"Estoque do Produto B deveria ser 30, mas é {p2.data['stock_quantity']}. "
            f"Rollback falhou!"
        )

        # Estoque do Produto C NÃO deve ter sido alterado (ainda 2)
        p3 = api_client.get(f"{self.PRODUCTS_ENDPOINT}{prod3_id}/")
        assert p3.data["stock_quantity"] == 2, (
            f"Estoque do Produto C deveria ser 2, mas é {p3.data['stock_quantity']}."
        )

    def test_partial_failure_no_order_created(self, api_client):
        """
        Nenhum pedido deve existir após falha parcial.
        """
        customer_id = self._setup_customer(api_client)
        prod1_id = self._setup_product(api_client, "Produto OK", stock=100)
        prod2_id = self._setup_product(api_client, "Produto SEM", stock=1)

        # Contar pedidos antes
        orders_before = api_client.get(self.ENDPOINT)
        count_before = len(orders_before.data.get("results", orders_before.data))

        # Tentar criar pedido que falha
        api_client.post(
            self.ENDPOINT,
            {
                "customer_id": customer_id,
                "items": [
                    {"product_id": prod1_id, "quantity": 5},
                    {"product_id": prod2_id, "quantity": 10},  # SEM ESTOQUE
                ],
            },
            format="json",
        )

        # Contar pedidos depois — não deve ter aumentado
        orders_after = api_client.get(self.ENDPOINT)
        count_after = len(orders_after.data.get("results", orders_after.data))

        assert count_after == count_before, (
            f"Nenhum pedido deveria ter sido criado. "
            f"Antes: {count_before}, Depois: {count_after}"
        )

    def test_all_items_with_stock_succeeds(self, api_client):
        """
        Contra-prova: se todos os itens têm estoque, o pedido deve funcionar.
        """
        customer_id = self._setup_customer(api_client)
        prod1_id = self._setup_product(api_client, "Prod X", stock=20)
        prod2_id = self._setup_product(api_client, "Prod Y", stock=30)
        prod3_id = self._setup_product(api_client, "Prod Z", stock=50)

        response = api_client.post(
            self.ENDPOINT,
            {
                "customer_id": customer_id,
                "items": [
                    {"product_id": prod1_id, "quantity": 5},
                    {"product_id": prod2_id, "quantity": 10},
                    {"product_id": prod3_id, "quantity": 15},
                ],
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        # Estoques deduzidos corretamente
        p1 = api_client.get(f"{self.PRODUCTS_ENDPOINT}{prod1_id}/")
        assert p1.data["stock_quantity"] == 15  # 20 - 5

        p2 = api_client.get(f"{self.PRODUCTS_ENDPOINT}{prod2_id}/")
        assert p2.data["stock_quantity"] == 20  # 30 - 10

        p3 = api_client.get(f"{self.PRODUCTS_ENDPOINT}{prod3_id}/")
        assert p3.data["stock_quantity"] == 35  # 50 - 15

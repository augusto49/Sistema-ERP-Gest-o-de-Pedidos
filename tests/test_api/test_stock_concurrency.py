"""
Teste de Concorrência de Estoque.

Cenário: Produto X tem 10 unidades em estoque.
Dois pedidos simultâneos tentam comprar 8 unidades cada.
Resultado esperado: Apenas um pedido deve ser aceito.
O outro deve falhar com erro de estoque insuficiente.

NOTA: Este teste usa threading para simular requisições paralelas.
Para funcionar com SELECT FOR UPDATE real, deve rodar contra MySQL:
    pytest tests/test_api/test_stock_concurrency.py -p no:django --override-ini="DJANGO_SETTINGS_MODULE=core.settings"

Quando executado com SQLite (settings_test), o teste valida a lógica
sequencial de verificação de estoque, mas não o lock real do banco.
"""

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
from django.db import connection
from django.test import TransactionTestCase
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db(transaction=True)
class TestStockConcurrency:
    """
    Testa que dois pedidos simultâneos para o mesmo produto
    não podem reservar estoque além do disponível.
    """

    ENDPOINT = "/api/v1/orders/"
    CUSTOMERS_ENDPOINT = "/api/v1/customers/"
    PRODUCTS_ENDPOINT = "/api/v1/products/"

    def _setup_customer(self, client):
        uid = uuid.uuid4().hex[:8]
        response = client.post(
            self.CUSTOMERS_ENDPOINT,
            {"name": f"Cliente {uid}", "email": f"{uid}@test.com", "cpf_cnpj": uid},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED, (
            f"Falha ao criar cliente: {response.data}"
        )
        return response.data["id"]

    def _setup_product(self, client, stock=10):
        uid = uuid.uuid4().hex[:8]
        response = client.post(
            self.PRODUCTS_ENDPOINT,
            {"sku": f"CONC-{uid}", "name": f"Produto {uid}", "price": "50.00", "stock_quantity": stock},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED, (
            f"Falha ao criar produto: {response.data}"
        )
        return response.data["id"]

    def _create_order_threadsafe(self, customer_id, product_id, quantity):
        """
        Cria um pedido usando um APIClient independente.
        Cada thread precisa de sua própria conexão ao banco.
        """
        client = APIClient()
        try:
            response = client.post(
                self.ENDPOINT,
                {"customer_id": customer_id, "items": [{"product_id": product_id, "quantity": quantity}]},
                format="json",
            )
            return {
                "status_code": response.status_code,
                "data": response.data,
                "success": 200 <= response.status_code < 300,
            }
        except Exception as e:
            return {
                "status_code": 500,
                "data": str(e),
                "success": False,
            }
        finally:
            connection.close()

    def test_concurrent_stock_reservation(self, api_client):
        """
        Cenário: Produto com 10 unidades. Dois pedidos de 8 cada.
        Apenas 1 deve ser aceito; o outro deve falhar.
        Estoque final deve ser 2 (10 - 8).
        """
        customer_id = self._setup_customer(api_client)
        product_id = self._setup_product(api_client, stock=10)

        barrier = threading.Barrier(2, timeout=5)
        results = [None, None]

        def place_order(index):
            barrier.wait()
            results[index] = self._create_order_threadsafe(
                customer_id, product_id, quantity=8
            )

        threads = [
            threading.Thread(target=place_order, args=(0,)),
            threading.Thread(target=place_order, args=(1,)),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        # Contar resultados
        successes = [r for r in results if r and r["success"]]
        failures = [r for r in results if r and not r["success"]]

        # Exatamente 1 deve ter sucesso
        assert len(successes) == 1, (
            f"Esperado exatamente 1 pedido aceito, mas {len(successes)} foram aceitos. "
            f"Resultados: {results}"
        )

        # Exatamente 1 deve falhar
        assert len(failures) == 1, (
            f"Esperado exatamente 1 pedido rejeitado, mas {len(failures)} falharam. "
            f"Resultados: {results}"
        )

        # O pedido que falhou deve ter código de estoque insuficiente (422)
        # ou database locked no SQLite (500) — ambos são comportamentos válidos
        # que impedem a venda duplicada.
        failed = failures[0]
        assert failed["status_code"] in (
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_409_CONFLICT,
            status.HTTP_500_INTERNAL_SERVER_ERROR,  # SQLite: database locked
        ), f"Status inesperado para falha: {failed['status_code']}"

        # Verificar estoque final (deve ser 10 - 8 = 2)
        product_response = api_client.get(f"{self.PRODUCTS_ENDPOINT}{product_id}/")
        assert product_response.data["stock_quantity"] == 2, (
            f"Estoque final deveria ser 2, mas é {product_response.data['stock_quantity']}"
        )

    def test_concurrent_stock_three_orders(self, api_client):
        """
        Cenário: Produto com 15 unidades. Três pedidos de 8 cada.
        Apenas 1 deve ser aceito; os outros 2 devem falhar.
        """
        customer_id = self._setup_customer(api_client)
        product_id = self._setup_product(api_client, stock=15)

        barrier = threading.Barrier(3, timeout=5)
        results = [None, None, None]

        def place_order(index):
            barrier.wait()
            results[index] = self._create_order_threadsafe(
                customer_id, product_id, quantity=8
            )

        threads = [
            threading.Thread(target=place_order, args=(i,))
            for i in range(3)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        successes = [r for r in results if r and r["success"]]
        failures = [r for r in results if r and not r["success"]]

        # Apenas 1 deve ter sucesso (15 - 8 = 7, segundo pedido de 8 não cabe)
        assert len(successes) == 1, (
            f"Esperado 1 pedido aceito, mas {len(successes)} foram aceitos. "
            f"Resultados: {results}"
        )
        assert len(failures) == 2, (
            f"Esperado 2 pedidos rejeitados, mas {len(failures)} falharam."
        )

        # Estoque final = 15 - 8 = 7
        product_response = api_client.get(f"{self.PRODUCTS_ENDPOINT}{product_id}/")
        assert product_response.data["stock_quantity"] == 7


@pytest.mark.django_db
class TestStockSequentialDepletion:
    """Testa esgotamento sequencial de estoque."""

    ENDPOINT = "/api/v1/orders/"
    CUSTOMERS_ENDPOINT = "/api/v1/customers/"
    PRODUCTS_ENDPOINT = "/api/v1/products/"

    def test_sequential_stock_until_depleted(self, api_client):
        """
        Cenário sequencial: Produto com 10 unidades.
        3 pedidos de 4 cada. Os 2 primeiros devem ser aceitos, o 3º rejeitado.
        """
        uid = uuid.uuid4().hex[:8]
        # Setup
        cust = api_client.post(
            self.CUSTOMERS_ENDPOINT,
            {"name": f"Cliente {uid}", "email": f"{uid}@test.com", "cpf_cnpj": uid},
            format="json",
        )
        assert cust.status_code == status.HTTP_201_CREATED
        customer_id = cust.data["id"]

        prod = api_client.post(
            self.PRODUCTS_ENDPOINT,
            {"sku": f"SEQ-{uid}", "name": f"Produto {uid}", "price": "50.00", "stock_quantity": 10},
            format="json",
        )
        assert prod.status_code == status.HTTP_201_CREATED
        product_id = prod.data["id"]

        # Pedido 1: 4 unidades (estoque: 10 → 6) ✓
        r1 = api_client.post(
            self.ENDPOINT,
            {"customer_id": customer_id, "items": [{"product_id": product_id, "quantity": 4}]},
            format="json",
        )
        assert r1.status_code == status.HTTP_201_CREATED

        # Pedido 2: 4 unidades (estoque: 6 → 2) ✓
        r2 = api_client.post(
            self.ENDPOINT,
            {"customer_id": customer_id, "items": [{"product_id": product_id, "quantity": 4}]},
            format="json",
        )
        assert r2.status_code == status.HTTP_201_CREATED

        # Pedido 3: 4 unidades (estoque: 2, insuficiente) ✗
        r3 = api_client.post(
            self.ENDPOINT,
            {"customer_id": customer_id, "items": [{"product_id": product_id, "quantity": 4}]},
            format="json",
        )
        assert r3.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Estoque final = 2
        product_response = api_client.get(f"{self.PRODUCTS_ENDPOINT}{product_id}/")
        assert product_response.data["stock_quantity"] == 2


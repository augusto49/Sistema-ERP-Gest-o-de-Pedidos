"""
Teste de Idempotência na Criação de Pedidos.

Cenário: Cliente envia a mesma requisição de criação de pedido 3 vezes
(simula retry após timeout) com a mesma Idempotency-Key.
Resultado esperado: Apenas um pedido deve ser criado.
As outras requisições devem retornar o mesmo pedido (200 ou 201, não 409).
"""

import json
import uuid

import pytest
from django.test import override_settings
from rest_framework import status

# Middleware completo com IdempotencyMiddleware ativo
MIDDLEWARE_WITH_IDEMPOTENCY = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "shared.middleware.idempotency.IdempotencyMiddleware",
]


def _get_data(response):
    """
    Extrai dados de uma resposta HTTP, seja DRF Response (.data)
    ou Django JsonResponse (sem .data, usar json.loads).
    O middleware de idempotência retorna JsonResponse, enquanto
    a primeira chamada retorna DRF Response.
    """
    if hasattr(response, "data"):
        return response.data
    return json.loads(response.content)


@pytest.mark.django_db
class TestIdempotency:
    """Testa idempotência na criação de pedidos via Idempotency-Key header."""

    ENDPOINT = "/api/v1/orders/"
    CUSTOMERS_ENDPOINT = "/api/v1/customers/"
    PRODUCTS_ENDPOINT = "/api/v1/products/"

    def _setup_customer(self, client):
        response = client.post(
            self.CUSTOMERS_ENDPOINT,
            {"name": "Cliente Idemp", "email": "idemp@test.com", "cpf_cnpj": "55566677700"},
            format="json",
        )
        return response.data["id"]

    def _setup_product(self, client, stock=50):
        response = client.post(
            self.PRODUCTS_ENDPOINT,
            {"sku": "IDEMP-001", "name": "Produto Idemp", "price": "75.00", "stock_quantity": stock},
            format="json",
        )
        return response.data["id"]

    @override_settings(MIDDLEWARE=MIDDLEWARE_WITH_IDEMPOTENCY)
    def test_idempotency_three_retries_same_key(self, api_client):
        """
        3 POST requests idênticos com mesma Idempotency-Key.
        Apenas 1 pedido deve ser criado. As 3 respostas devem
        retornar o mesmo pedido com status 200 ou 201.
        """
        customer_id = self._setup_customer(api_client)
        product_id = self._setup_product(api_client, stock=50)
        idempotency_key = str(uuid.uuid4())

        order_data = {
            "customer_id": customer_id,
            "items": [{"product_id": product_id, "quantity": 2}],
            "notes": "Pedido idempotente",
        }

        responses = []
        for i in range(3):
            resp = api_client.post(
                self.ENDPOINT,
                order_data,
                format="json",
                HTTP_IDEMPOTENCY_KEY=idempotency_key,
            )
            responses.append(resp)

        # Todas as respostas devem ter status 2xx (sucesso)
        for i, resp in enumerate(responses):
            assert 200 <= resp.status_code < 300, (
                f"Requisição {i+1} retornou status {resp.status_code} "
                f"(esperado 200 ou 201)."
            )

        # Primeira requisição: 201 Created
        assert responses[0].status_code == status.HTTP_201_CREATED

        # Todas devem retornar o mesmo ID de pedido
        data_list = [_get_data(r) for r in responses]
        order_ids = [d["id"] for d in data_list]
        assert len(set(order_ids)) == 1, (
            f"Esperado que todas retornassem o mesmo pedido, "
            f"mas IDs diferentes: {order_ids}"
        )

        # Todas devem retornar o mesmo order_number
        order_numbers = [d["order_number"] for d in data_list]
        assert len(set(order_numbers)) == 1, (
            f"Order numbers diferentes: {order_numbers}"
        )

        # Estoque deve ter sido deduzido apenas 1 vez (50 - 2 = 48)
        product_response = api_client.get(f"{self.PRODUCTS_ENDPOINT}{product_id}/")
        assert product_response.data["stock_quantity"] == 48, (
            f"Estoque deveria ser 48, mas é {product_response.data['stock_quantity']}. "
            f"O estoque foi deduzido mais de uma vez!"
        )

    @override_settings(MIDDLEWARE=MIDDLEWARE_WITH_IDEMPOTENCY)
    def test_different_keys_create_different_orders(self, api_client):
        """
        2 POST requests com Idempotency-Keys diferentes devem
        criar 2 pedidos distintos.
        """
        customer_id = self._setup_customer(api_client)
        product_id = self._setup_product(api_client, stock=50)

        order_data = {
            "customer_id": customer_id,
            "items": [{"product_id": product_id, "quantity": 1}],
        }

        resp1 = api_client.post(
            self.ENDPOINT,
            order_data,
            format="json",
            HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
        )
        resp2 = api_client.post(
            self.ENDPOINT,
            order_data,
            format="json",
            HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
        )

        assert resp1.status_code == status.HTTP_201_CREATED
        assert resp2.status_code == status.HTTP_201_CREATED
        assert resp1.data["id"] != resp2.data["id"], (
            "Keys diferentes deveriam criar pedidos diferentes"
        )

        # Estoque deduzido 2 vezes (50 - 1 - 1 = 48)
        product_response = api_client.get(f"{self.PRODUCTS_ENDPOINT}{product_id}/")
        assert product_response.data["stock_quantity"] == 48

    @override_settings(MIDDLEWARE=MIDDLEWARE_WITH_IDEMPOTENCY)
    def test_no_key_creates_new_order_each_time(self, api_client):
        """
        POST sem Idempotency-Key deve criar um pedido novo a cada vez.
        """
        customer_id = self._setup_customer(api_client)
        product_id = self._setup_product(api_client, stock=50)

        order_data = {
            "customer_id": customer_id,
            "items": [{"product_id": product_id, "quantity": 1}],
        }

        resp1 = api_client.post(self.ENDPOINT, order_data, format="json")
        resp2 = api_client.post(self.ENDPOINT, order_data, format="json")

        assert resp1.status_code == status.HTTP_201_CREATED
        assert resp2.status_code == status.HTTP_201_CREATED
        assert resp1.data["id"] != resp2.data["id"]

    @override_settings(MIDDLEWARE=MIDDLEWARE_WITH_IDEMPOTENCY)
    def test_idempotency_preserves_response_data(self, api_client):
        """
        A resposta cacheada deve conter exatamente os mesmos dados
        que a resposta original.
        """
        customer_id = self._setup_customer(api_client)
        product_id = self._setup_product(api_client, stock=50)
        idempotency_key = str(uuid.uuid4())

        order_data = {
            "customer_id": customer_id,
            "items": [{"product_id": product_id, "quantity": 3}],
            "notes": "Teste dados preservados",
        }

        resp1 = api_client.post(
            self.ENDPOINT, order_data, format="json",
            HTTP_IDEMPOTENCY_KEY=idempotency_key,
        )
        resp2 = api_client.post(
            self.ENDPOINT, order_data, format="json",
            HTTP_IDEMPOTENCY_KEY=idempotency_key,
        )

        d1 = _get_data(resp1)
        d2 = _get_data(resp2)

        # Mesmos campos essenciais
        assert d1["id"] == d2["id"]
        assert d1["order_number"] == d2["order_number"]
        assert d1["total"] == d2["total"]
        assert d1["status"] == d2["status"]
        assert d1["notes"] == d2["notes"]
        assert len(d1["items"]) == len(d2["items"])

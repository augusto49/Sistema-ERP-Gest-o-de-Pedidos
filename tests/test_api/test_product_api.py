"""
Testes de integração da API — Products.
"""

import pytest
from rest_framework import status


@pytest.mark.django_db
class TestProductAPI:
    """Testes de integração para endpoints de Produtos."""

    ENDPOINT = "/api/v1/products/"

    def _create_product(self, api_client, **kwargs):
        data = {
            "sku": "SKU-001",
            "name": "Produto Teste",
            "description": "Um produto para teste",
            "price": "99.90",
            "stock_quantity": 50,
        }
        data.update(kwargs)
        return api_client.post(self.ENDPOINT, data, format="json")

    def test_criar_produto(self, api_client):
        response = self._create_product(api_client)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["sku"] == "SKU-001"
        assert response.data["stock_quantity"] == 50

    def test_criar_produto_sku_duplicado(self, api_client):
        self._create_product(api_client)
        response = self._create_product(api_client)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_listar_produtos(self, api_client):
        self._create_product(api_client)
        self._create_product(api_client, sku="SKU-002", name="Produto 2")

        response = api_client.get(self.ENDPOINT)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_buscar_produto_por_id(self, api_client):
        create_response = self._create_product(api_client)
        product_id = create_response.data["id"]

        response = api_client.get(f"{self.ENDPOINT}{product_id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["sku"] == "SKU-001"

    def test_atualizar_produto(self, api_client):
        create_response = self._create_product(api_client)
        product_id = create_response.data["id"]

        update_data = {
            "sku": "SKU-001",
            "name": "Produto Atualizado",
            "price": "149.90",
            "stock_quantity": 100,
        }
        response = api_client.put(
            f"{self.ENDPOINT}{product_id}/", update_data, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Produto Atualizado"

    def test_deletar_produto_soft(self, api_client):
        create_response = self._create_product(api_client)
        product_id = create_response.data["id"]

        response = api_client.delete(f"{self.ENDPOINT}{product_id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        response = api_client.get(f"{self.ENDPOINT}{product_id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

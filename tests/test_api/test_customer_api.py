"""
Testes de integração da API — Customers.
Usa SQLite in-memory via conftest.py.
"""

import pytest
from django.test import override_settings
from rest_framework import status


@pytest.mark.django_db
class TestCustomerAPI:
    """Testes de integração para endpoints de Clientes."""

    ENDPOINT = "/api/v1/customers/"

    def _create_customer(self, api_client, **kwargs):
        data = {
            "name": "João Silva",
            "email": "joao@email.com",
            "cpf_cnpj": "12345678901",
            "phone": "11999999999",
        }
        data.update(kwargs)
        return api_client.post(self.ENDPOINT, data, format="json")

    def test_criar_cliente(self, api_client):
        response = self._create_customer(api_client)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "João Silva"
        assert response.data["email"] == "joao@email.com"
        assert response.data["id"] is not None

    def test_criar_cliente_email_duplicado(self, api_client):
        self._create_customer(api_client)
        response = self._create_customer(api_client, cpf_cnpj="99999999999")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_criar_cliente_cpf_duplicado(self, api_client):
        self._create_customer(api_client)
        response = self._create_customer(api_client, email="outro@email.com")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_listar_clientes(self, api_client):
        self._create_customer(api_client)
        self._create_customer(
            api_client, name="Maria", email="maria@email.com", cpf_cnpj="111"
        )

        response = api_client.get(self.ENDPOINT)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        assert len(response.data["results"]) == 2

    def test_buscar_cliente_por_id(self, api_client):
        create_response = self._create_customer(api_client)
        customer_id = create_response.data["id"]

        response = api_client.get(f"{self.ENDPOINT}{customer_id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == customer_id

    def test_buscar_cliente_inexistente(self, api_client):
        response = api_client.get(f"{self.ENDPOINT}9999/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_atualizar_cliente(self, api_client):
        create_response = self._create_customer(api_client)
        customer_id = create_response.data["id"]

        update_data = {
            "name": "João Atualizado",
            "email": "joao@email.com",
            "cpf_cnpj": "12345678901",
        }
        response = api_client.put(
            f"{self.ENDPOINT}{customer_id}/", update_data, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "João Atualizado"

    def test_deletar_cliente_soft(self, api_client):
        create_response = self._create_customer(api_client)
        customer_id = create_response.data["id"]

        response = api_client.delete(f"{self.ENDPOINT}{customer_id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Após soft delete, não deve ser encontrado
        response = api_client.get(f"{self.ENDPOINT}{customer_id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

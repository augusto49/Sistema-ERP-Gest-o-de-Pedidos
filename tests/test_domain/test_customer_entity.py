"""
Testes unitários para entidades de domínio - Customer.
Testes puros sem dependência do Django.
"""

from customers.domain.entities import CustomerEntity


class TestCustomerEntity:
    """Testes para CustomerEntity."""

    def test_criar_entidade_valida(self):
        customer = CustomerEntity(
            name="João Silva",
            email="joao@email.com",
            cpf_cnpj="12345678901",
            phone="11999999999",
        )
        assert customer.name == "João Silva"
        assert customer.email == "joao@email.com"
        assert customer.is_active is True
        assert customer.is_deleted is False

    def test_validar_campos_obrigatorios(self):
        customer = CustomerEntity()
        errors = customer.validate()
        assert len(errors) == 3
        assert "nome" in errors[0].lower()
        assert "email" in errors[1].lower()
        assert "cpf" in errors[2].lower()

    def test_validar_entidade_valida_sem_erros(self):
        customer = CustomerEntity(
            name="Maria", email="maria@email.com", cpf_cnpj="98765432100"
        )
        errors = customer.validate()
        assert len(errors) == 0

    def test_soft_delete(self):
        customer = CustomerEntity(name="Test", email="t@t.com", cpf_cnpj="111")
        assert customer.is_deleted is False
        assert customer.is_active is True

        customer.soft_delete()

        assert customer.is_deleted is True
        assert customer.is_active is False
        assert customer.deleted_at is not None

    def test_desativar_e_ativar(self):
        customer = CustomerEntity(name="Test", email="t@t.com", cpf_cnpj="111")

        customer.deactivate()
        assert customer.is_active is False

        customer.activate()
        assert customer.is_active is True

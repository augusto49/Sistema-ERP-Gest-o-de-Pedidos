"""
Serviço de Clientes — Camada de aplicação (Use Cases).
Orquestra regras de negócio e operações do repositório.
"""

import structlog

from customers.domain.entities import CustomerEntity
from customers.repositories.interfaces import ICustomerRepository
from shared.exceptions.domain_exceptions import (
    BusinessRuleViolation,
    EntityNotFoundException,
)

logger = structlog.get_logger(__name__)


class CustomerService:
    """
    Use Cases do módulo de Clientes.
    Recebe o repositório via injeção de dependência (DIP).
    """

    def __init__(self, repository: ICustomerRepository):
        self.repository = repository

    def create_customer(self, data: dict) -> CustomerEntity:
        """
        Cria um novo cliente.
        Regras:
        - Email deve ser único.
        - CPF/CNPJ deve ser único.
        - Campos obrigatórios validados pela entidade.
        """
        entity = CustomerEntity(
            name=data["name"],
            email=data["email"],
            cpf_cnpj=data["cpf_cnpj"],
            phone=data.get("phone", ""),
            address=data.get("address", ""),
        )

        # Validação da entidade
        errors = entity.validate()
        if errors:
            raise BusinessRuleViolation(
                message=" | ".join(errors),
            )

        # Verificar duplicatas
        if self.repository.get_by_email(entity.email):
            raise BusinessRuleViolation(
                message=f"Já existe um cliente com o email '{entity.email}'."
            )

        if self.repository.get_by_cpf_cnpj(entity.cpf_cnpj):
            raise BusinessRuleViolation(
                message=f"Já existe um cliente com o CPF/CNPJ '{entity.cpf_cnpj}'."
            )

        customer = self.repository.create(entity)
        logger.info("customer_created", customer_id=customer.id, email=customer.email)
        return customer

    def get_customer(self, customer_id: int) -> CustomerEntity:
        """Busca um cliente pelo ID. Lança exceção se não encontrado."""
        customer = self.repository.get_by_id(customer_id)
        if not customer:
            raise EntityNotFoundException(
                entity="Cliente", entity_id=customer_id
            )
        return customer

    def list_customers(
        self, filters: dict = None, page: int = 1, page_size: int = 20
    ) -> tuple[list[CustomerEntity], int]:
        """Lista clientes com filtros e paginação."""
        return self.repository.list_all(filters=filters, page=page, page_size=page_size)

    def update_customer(self, customer_id: int, data: dict) -> CustomerEntity:
        """
        Atualiza um cliente existente.
        Regras:
        - Cliente deve existir.
        - Se alterar email/cpf_cnpj, verificar unicidade.
        """
        existing = self.get_customer(customer_id)

        # Verificar unicidade de email se alterado
        new_email = data.get("email", existing.email)
        if new_email != existing.email:
            if self.repository.get_by_email(new_email):
                raise BusinessRuleViolation(
                    message=f"Já existe um cliente com o email '{new_email}'."
                )

        # Verificar unicidade de CPF/CNPJ se alterado
        new_cpf_cnpj = data.get("cpf_cnpj", existing.cpf_cnpj)
        if new_cpf_cnpj != existing.cpf_cnpj:
            if self.repository.get_by_cpf_cnpj(new_cpf_cnpj):
                raise BusinessRuleViolation(
                    message=f"Já existe um cliente com o CPF/CNPJ '{new_cpf_cnpj}'."
                )

        # Atualizar entidade
        existing.name = data.get("name", existing.name)
        existing.email = new_email
        existing.cpf_cnpj = new_cpf_cnpj
        existing.phone = data.get("phone", existing.phone)
        existing.address = data.get("address", existing.address)
        existing.is_active = data.get("is_active", existing.is_active)

        # Revalidar
        errors = existing.validate()
        if errors:
            raise BusinessRuleViolation(message=" | ".join(errors))

        customer = self.repository.update(existing)
        logger.info("customer_updated", customer_id=customer.id)
        return customer

    def delete_customer(self, customer_id: int) -> bool:
        """Exclusão lógica de um cliente."""
        self.get_customer(customer_id)  # Verifica se existe
        deleted = self.repository.soft_delete(customer_id)
        if deleted:
            logger.info("customer_deleted", customer_id=customer_id)
        return deleted

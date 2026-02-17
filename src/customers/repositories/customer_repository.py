"""
Implementação concreta do repositório de Customer usando Django ORM.
"""

from datetime import datetime
from typing import Optional

from customers.domain.entities import CustomerEntity
from customers.models import Customer
from customers.repositories.interfaces import ICustomerRepository


class CustomerRepository(ICustomerRepository):
    """
    Implementação do repositório de Clientes usando Django ORM.
    Converte entre Django Models e Domain Entities.
    """

    def _to_entity(self, model: Customer) -> CustomerEntity:
        """Converte um Django Model para uma Domain Entity."""
        return CustomerEntity(
            id=model.id,
            name=model.name,
            email=model.email,
            cpf_cnpj=model.cpf_cnpj,
            phone=model.phone,
            address=model.address,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

    def _get_active_queryset(self):
        """Retorna queryset filtrando apenas registros não excluídos."""
        return Customer.objects.filter(deleted_at__isnull=True)

    def get_by_id(self, customer_id: int) -> Optional[CustomerEntity]:
        try:
            model = self._get_active_queryset().get(id=customer_id)
            return self._to_entity(model)
        except Customer.DoesNotExist:
            return None

    def get_by_email(self, email: str) -> Optional[CustomerEntity]:
        try:
            model = self._get_active_queryset().get(email=email)
            return self._to_entity(model)
        except Customer.DoesNotExist:
            return None

    def get_by_cpf_cnpj(self, cpf_cnpj: str) -> Optional[CustomerEntity]:
        try:
            model = self._get_active_queryset().get(cpf_cnpj=cpf_cnpj)
            return self._to_entity(model)
        except Customer.DoesNotExist:
            return None

    def list_all(
        self, filters: Optional[dict] = None, page: int = 1, page_size: int = 20
    ) -> tuple[list[CustomerEntity], int]:
        queryset = self._get_active_queryset()

        if filters:
            if "name" in filters:
                queryset = queryset.filter(name__icontains=filters["name"])
            if "email" in filters:
                queryset = queryset.filter(email__icontains=filters["email"])
            if "is_active" in filters:
                queryset = queryset.filter(is_active=filters["is_active"])

        total = queryset.count()
        offset = (page - 1) * page_size
        models = queryset[offset : offset + page_size]

        return [self._to_entity(m) for m in models], total

    def create(self, entity: CustomerEntity) -> CustomerEntity:
        model = Customer.objects.create(
            name=entity.name,
            email=entity.email,
            cpf_cnpj=entity.cpf_cnpj,
            phone=entity.phone,
            address=entity.address,
            is_active=entity.is_active,
        )
        return self._to_entity(model)

    def update(self, entity: CustomerEntity) -> CustomerEntity:
        Customer.objects.filter(id=entity.id).update(
            name=entity.name,
            email=entity.email,
            cpf_cnpj=entity.cpf_cnpj,
            phone=entity.phone,
            address=entity.address,
            is_active=entity.is_active,
        )
        model = Customer.objects.get(id=entity.id)
        return self._to_entity(model)

    def soft_delete(self, customer_id: int) -> bool:
        updated = Customer.objects.filter(
            id=customer_id, deleted_at__isnull=True
        ).update(deleted_at=datetime.now(), is_active=False)
        return updated > 0

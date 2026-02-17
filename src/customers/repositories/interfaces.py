"""
Interfaces abstratas do repositório de Customer.
Define os contratos que qualquer implementação deve seguir (DIP - SOLID).
"""

from abc import ABC, abstractmethod
from typing import Optional

from customers.domain.entities import CustomerEntity


class ICustomerRepository(ABC):
    """
    Interface do repositório de Clientes.
    Dependa desta abstração, não da implementação concreta.
    """

    @abstractmethod
    def get_by_id(self, customer_id: int) -> Optional[CustomerEntity]:
        """Busca um cliente pelo ID."""
        ...

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[CustomerEntity]:
        """Busca um cliente pelo email."""
        ...

    @abstractmethod
    def get_by_cpf_cnpj(self, cpf_cnpj: str) -> Optional[CustomerEntity]:
        """Busca um cliente pelo CPF/CNPJ."""
        ...

    @abstractmethod
    def list_all(
        self, filters: Optional[dict] = None, page: int = 1, page_size: int = 20
    ) -> tuple[list[CustomerEntity], int]:
        """Lista clientes com filtros e paginação. Retorna (lista, total)."""
        ...

    @abstractmethod
    def create(self, entity: CustomerEntity) -> CustomerEntity:
        """Cria um novo cliente."""
        ...

    @abstractmethod
    def update(self, entity: CustomerEntity) -> CustomerEntity:
        """Atualiza um cliente existente."""
        ...

    @abstractmethod
    def soft_delete(self, customer_id: int) -> bool:
        """Exclusão lógica de um cliente."""
        ...

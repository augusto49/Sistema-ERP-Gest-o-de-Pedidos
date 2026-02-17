"""
Entidades de domínio - Customer.
Classes Python puras, sem dependência do Django.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class CustomerEntity:
    """
    Entidade de domínio representando um Cliente.
    Independente do framework e do banco de dados.
    """

    id: Optional[int] = None
    name: str = ""
    email: str = ""
    cpf_cnpj: str = ""
    phone: str = ""
    address: str = ""
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    @property
    def is_deleted(self) -> bool:
        """Verifica se o cliente foi excluído logicamente."""
        return self.deleted_at is not None

    def deactivate(self):
        """Desativa o cliente."""
        self.is_active = False

    def activate(self):
        """Ativa o cliente."""
        self.is_active = True

    def soft_delete(self):
        """Exclusão lógica do cliente."""
        self.deleted_at = datetime.now()
        self.is_active = False

    def validate(self) -> list[str]:
        """Valida os dados da entidade. Retorna lista de erros."""
        errors = []
        if not self.name or not self.name.strip():
            errors.append("O nome do cliente é obrigatório.")
        if not self.email or not self.email.strip():
            errors.append("O email do cliente é obrigatório.")
        if not self.cpf_cnpj or not self.cpf_cnpj.strip():
            errors.append("O CPF/CNPJ do cliente é obrigatório.")
        return errors

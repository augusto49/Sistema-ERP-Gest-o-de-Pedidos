"""
Django Models - Customer.
Camada de persistência mapeada para o banco de dados MySQL.
"""

from django.db import models


class Customer(models.Model):
    """
    Model Django representando a tabela de Clientes no banco.
    Responsável apenas pela persistência (não contém regras de negócio).
    """

    name = models.CharField(
        max_length=255,
        verbose_name="Nome",
    )
    email = models.EmailField(
        unique=True,
        verbose_name="Email",
    )
    cpf_cnpj = models.CharField(
        max_length=18,
        unique=True,
        verbose_name="CPF/CNPJ",
        db_index=True,
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name="Telefone",
    )
    address = models.TextField(
        blank=True,
        default="",
        verbose_name="Endereço",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativo",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em",
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Excluído em",
    )

    class Meta:
        db_table = "customers"
        ordering = ["-created_at"]
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        indexes = [
            models.Index(fields=["email"], name="idx_customer_email"),
            models.Index(fields=["is_active"], name="idx_customer_active"),
        ]

    def __str__(self):
        return f"{self.name} ({self.cpf_cnpj})"

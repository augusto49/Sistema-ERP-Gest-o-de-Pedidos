"""
Django Models - Product.
Camada de persistência mapeada para o banco de dados MySQL.
"""

from django.db import models


class Product(models.Model):
    """
    Model Django representando a tabela de Produtos no banco.
    Suporta select_for_update para controle de concorrência.
    """

    sku = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="SKU",
        db_index=True,
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Nome",
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="Descrição",
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Preço",
    )
    stock_quantity = models.PositiveIntegerField(
        default=0,
        verbose_name="Quantidade em Estoque",
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
        db_table = "products"
        ordering = ["name"]
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        indexes = [
            models.Index(fields=["sku"], name="idx_product_sku"),
            models.Index(fields=["is_active"], name="idx_product_active"),
        ]

    def __str__(self):
        return f"{self.sku} - {self.name}"

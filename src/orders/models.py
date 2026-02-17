"""
Django Models - Order, OrderItem, OrderHistory.
Camada de persistência mapeada para o banco de dados MySQL.
"""

import uuid

from django.db import models

from orders.domain.value_objects import OrderStatus


class Order(models.Model):
    """
    Model representando a tabela de Pedidos.
    """

    STATUS_CHOICES = [(s.value, s.name.title()) for s in OrderStatus]

    order_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name="Número do Pedido",
    )
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="Cliente",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=OrderStatus.PENDING.value,
        db_index=True,
        verbose_name="Status",
    )
    notes = models.TextField(
        blank=True,
        default="",
        verbose_name="Observações",
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
        db_table = "orders"
        ordering = ["-created_at"]
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        indexes = [
            models.Index(fields=["status"], name="idx_order_status"),
            models.Index(fields=["customer", "status"], name="idx_order_cust_status"),
            models.Index(fields=["created_at"], name="idx_order_created"),
        ]

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self._generate_order_number()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_order_number() -> str:
        """Gera número único do pedido: PED-XXXXXXXX."""
        return f"PED-{uuid.uuid4().hex[:8].upper()}"

    def __str__(self):
        return f"Pedido {self.order_number} - {self.status}"


class OrderItem(models.Model):
    """
    Model representando os itens de um pedido.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Pedido",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="order_items",
        verbose_name="Produto",
    )
    product_sku = models.CharField(
        max_length=50,
        verbose_name="SKU do Produto",
    )
    product_name = models.CharField(
        max_length=255,
        verbose_name="Nome do Produto",
    )
    quantity = models.PositiveIntegerField(
        verbose_name="Quantidade",
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Preço Unitário",
    )

    class Meta:
        db_table = "order_items"
        verbose_name = "Item do Pedido"
        verbose_name_plural = "Itens do Pedido"

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.product_sku} x{self.quantity}"


class OrderHistory(models.Model):
    """
    Model para rastrear o histórico de mudanças de status dos pedidos.
    Audit trail imutável.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="history",
        verbose_name="Pedido",
    )
    from_status = models.CharField(
        max_length=20,
        verbose_name="Status Anterior",
    )
    to_status = models.CharField(
        max_length=20,
        verbose_name="Novo Status",
    )
    changed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data da Alteração",
    )
    changed_by = models.CharField(
        max_length=100,
        blank=True,
        default="system",
        verbose_name="Usuário Responsável",
    )
    notes = models.TextField(
        blank=True,
        default="",
        verbose_name="Observações",
    )

    class Meta:
        db_table = "order_history"
        ordering = ["-changed_at"]
        verbose_name = "Histórico do Pedido"
        verbose_name_plural = "Históricos dos Pedidos"

    def __str__(self):
        return f"Pedido #{self.order_id}: {self.from_status} → {self.to_status}"

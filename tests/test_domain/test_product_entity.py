"""
Testes unitários para entidades de domínio - Product.
"""

from decimal import Decimal

import pytest

from products.domain.entities import ProductEntity


class TestProductEntity:
    """Testes para ProductEntity."""

    def test_criar_produto_valido(self):
        product = ProductEntity(
            sku="SKU-001",
            name="Produto Teste",
            price=Decimal("99.90"),
            stock_quantity=50,
        )
        assert product.sku == "SKU-001"
        assert product.price == Decimal("99.90")
        assert product.has_stock is True

    def test_validar_campos_obrigatorios(self):
        product = ProductEntity(price=Decimal("0"))
        errors = product.validate()
        assert len(errors) >= 2
        assert any("sku" in e.lower() for e in errors)
        assert any("nome" in e.lower() for e in errors)

    def test_validar_preco_positivo(self):
        product = ProductEntity(
            sku="SKU-001", name="Test", price=Decimal("-10.00")
        )
        errors = product.validate()
        assert any("preço" in e.lower() for e in errors)

    def test_verificar_estoque_suficiente(self):
        product = ProductEntity(
            sku="SKU-001", name="Test", price=Decimal("10"), stock_quantity=10
        )
        assert product.has_sufficient_stock(5) is True
        assert product.has_sufficient_stock(10) is True
        assert product.has_sufficient_stock(11) is False

    def test_deduzir_estoque(self):
        product = ProductEntity(
            sku="SKU-001", name="Test", price=Decimal("10"), stock_quantity=10
        )
        product.deduct_stock(3)
        assert product.stock_quantity == 7

    def test_deduzir_estoque_insuficiente_lanca_erro(self):
        product = ProductEntity(
            sku="SKU-001", name="Test", price=Decimal("10"), stock_quantity=5
        )
        with pytest.raises(ValueError, match="Estoque insuficiente"):
            product.deduct_stock(10)

    def test_restaurar_estoque(self):
        product = ProductEntity(
            sku="SKU-001", name="Test", price=Decimal("10"), stock_quantity=5
        )
        product.restore_stock(3)
        assert product.stock_quantity == 8

    def test_soft_delete(self):
        product = ProductEntity(
            sku="SKU-001", name="Test", price=Decimal("10"), stock_quantity=5
        )
        product.soft_delete()
        assert product.is_deleted is True
        assert product.is_active is False

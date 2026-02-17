"""
Management command para popular o banco com dados iniciais.
Uso: python manage.py seed
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from customers.models import Customer
from products.models import Product


class Command(BaseCommand):
    help = "Popula o banco de dados com dados iniciais para desenvolvimento."

    CUSTOMERS = [
        {
            "name": "Maria Silva",
            "email": "maria.silva@email.com",
            "cpf_cnpj": "123.456.789-00",
            "phone": "(11) 99999-0001",
            "address": "Rua das Flores, 100 - São Paulo/SP",
        },
        {
            "name": "João Santos",
            "email": "joao.santos@email.com",
            "cpf_cnpj": "987.654.321-00",
            "phone": "(11) 99999-0002",
            "address": "Av. Paulista, 1000 - São Paulo/SP",
        },
        {
            "name": "Tech Solutions LTDA",
            "email": "contato@techsolutions.com",
            "cpf_cnpj": "12.345.678/0001-00",
            "phone": "(21) 3333-0001",
            "address": "Rua do Comércio, 50 - Rio de Janeiro/RJ",
        },
    ]

    PRODUCTS = [
        {
            "sku": "NOTE-001",
            "name": "Notebook Pro 15",
            "description": "Notebook profissional 15 polegadas, 16GB RAM, 512GB SSD",
            "price": "4599.90",
            "stock_quantity": 50,
        },
        {
            "sku": "MOUSE-001",
            "name": "Mouse Ergonômico Wireless",
            "description": "Mouse sem fio ergonômico com sensor óptico de alta precisão",
            "price": "149.90",
            "stock_quantity": 200,
        },
        {
            "sku": "TECL-001",
            "name": "Teclado Mecânico RGB",
            "description": "Teclado mecânico com iluminação RGB e switches blue",
            "price": "349.90",
            "stock_quantity": 150,
        },
        {
            "sku": "MON-001",
            "name": "Monitor 27\" 4K",
            "description": "Monitor IPS 27 polegadas, resolução 4K UHD",
            "price": "2299.90",
            "stock_quantity": 30,
        },
        {
            "sku": "HEAD-001",
            "name": "Headset Profissional",
            "description": "Headset com cancelamento de ruído e microfone",
            "price": "299.90",
            "stock_quantity": 100,
        },
    ]

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("🌱 Iniciando seed de dados...")

        # Customers
        created_customers = 0
        for data in self.CUSTOMERS:
            _, created = Customer.objects.get_or_create(
                email=data["email"],
                defaults=data,
            )
            if created:
                created_customers += 1

        self.stdout.write(
            self.style.SUCCESS(f"  ✅ Clientes: {created_customers} criados")
        )

        # Products
        created_products = 0
        for data in self.PRODUCTS:
            _, created = Product.objects.get_or_create(
                sku=data["sku"],
                defaults=data,
            )
            if created:
                created_products += 1

        self.stdout.write(
            self.style.SUCCESS(f"  ✅ Produtos: {created_products} criados")
        )

        self.stdout.write(self.style.SUCCESS("\n🎉 Seed concluído com sucesso!"))

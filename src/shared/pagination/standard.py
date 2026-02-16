"""
Paginação padrão para a API.
"""

from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """Paginação padrão com tamanho configurável."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

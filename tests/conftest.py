"""
Configuração global do pytest.
Fixtures compartilhadas para testes de domínio e integração.
"""

import pytest


@pytest.fixture
def api_client():
    """Client do DRF para testes de integração."""
    from rest_framework.test import APIClient

    return APIClient()

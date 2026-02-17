"""
View customizada para renderizar o Scalar API Reference.
Scalar é uma alternativa moderna e elegante ao Swagger/ReDoc.
"""

from django.http import HttpResponse
from django.views import View


class ScalarView(View):
    """Renderiza a documentação da API usando Scalar."""

    def get(self, request):
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>ERP API - Scalar</title>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
        </head>
        <body>
            <script
                id="api-reference"
                data-url="/api/schema/"
                data-configuration='{"theme": "kepler"}'
            ></script>
            <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
        </body>
        </html>
        """
        return HttpResponse(html, content_type="text/html")

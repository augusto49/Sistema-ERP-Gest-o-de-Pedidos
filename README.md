# Sistema ERP - Módulo de Gestão de Pedidos

API RESTful para gerenciamento de pedidos, clientes e produtos, construída com Django/DRF seguindo Clean Architecture e princípios SOLID.

## ✨ Funcionalidades

- **Clientes** – CRUD completo com validação de CPF/CNPJ e soft delete
- **Produtos** – CRUD com controle de estoque atômico (pessimistic locking)
- **Pedidos** – Criação com reserva de estoque, máquina de estados para status, histórico de transições
- **Idempotência** – Middleware com Redis para evitar duplicatas via `Idempotency-Key`
- **Domain Events** – EventBus para publicação de eventos de domínio
- **Paginação, Filtros e Ordenação** – Em todos os endpoints de listagem
- **Rate Limiting** – Controle de requisições via Redis
- **Documentação** – OpenAPI/Swagger, Redoc e Scalar

## 🛠 Tecnologias

| Componente            | Tecnologia                       |
| --------------------- | -------------------------------- |
| Framework             | Django 5 + Django REST Framework |
| Banco de Dados        | MySQL 8.0                        |
| Cache / Rate Limiting | Redis 7                          |
| Documentação API      | drf-spectacular (OpenAPI 3)      |
| Servidor WSGI         | Gunicorn                         |
| Contêiner             | Docker + Docker Compose          |
| CI/CD                 | GitHub Actions                   |
| Logs                  | structlog (JSON)                 |
| Testes                | pytest + pytest-cov              |

## 🚀 Setup Rápido

### Pré-requisitos

- [Docker](https://www.docker.com/) e Docker Compose instalados

### 1. Clonar repositório

```bash
git clone https://github.com/seu-usuario/erp-orders.git
cd erp-orders
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
```

### 3. Subir os serviços

```bash
docker-compose up --build
```

Isso inicia automaticamente:

- **API** em `http://localhost:8000`
- **MySQL** na porta `3307`
- **Redis** na porta `6379`
- Migrations aplicadas automaticamente no startup

### 4. Popular dados iniciais (opcional)

```bash
docker-compose exec web python manage.py seed
```

### 5. Verificar saúde

```bash
curl http://localhost:8000/health/
```

### 6. Acessar documentação

| Ferramenta  | URL                               |
| ----------- | --------------------------------- |
| Swagger UI  | http://localhost:8000/api/docs/   |
| Redoc       | http://localhost:8000/api/redoc/  |
| Scalar      | http://localhost:8000/api/scalar/ |
| Schema JSON | http://localhost:8000/api/schema/ |

## 🧪 Testes

### Rodar todos os testes

```bash
# Com Docker
docker-compose exec web pytest -v

# Local (com venv)
pip install -r requirements.txt
DJANGO_SETTINGS_MODULE=core.settings_test pytest -v
```

### Cobertura de código

```bash
pytest --cov=customers --cov=products --cov=orders --cov=shared --cov-report=term-missing
```

**Cobertura atual: 89%** (mínimo: 60%, recomendado: 80%+)

### Estrutura de testes

```
tests/
├── test_domain/          # Testes unitários (regras de negócio)
│   ├── test_customer_entity.py
│   ├── test_order_entity.py
│   └── test_product_entity.py
└── test_api/             # Testes de integração (E2E)
    ├── test_customer_api.py
    ├── test_product_api.py
    ├── test_order_api.py
    ├── test_idempotency.py
    ├── test_stock_concurrency.py
    └── test_atomic_partial_failure.py
```

## 📁 Arquitetura

```
src/
├── core/                  # Configurações Django
│   ├── settings.py        # Produção (MySQL + Redis)
│   └── settings_test.py   # Testes (SQLite in-memory)
├── customers/             # Módulo de Clientes
│   ├── api/               # Views + Serializers (Controller)
│   ├── domain/            # Entidades puras
│   ├── services/          # Regras de negócio
│   └── repositories/      # Acesso a dados (Interface + Impl)
├── products/              # Módulo de Produtos
│   └── (mesma estrutura)
├── orders/                # Módulo de Pedidos
│   └── (mesma estrutura)
└── shared/                # Infraestrutura compartilhada
    ├── events/            # EventBus (domain events)
    ├── exceptions/        # Exceções + Handler
    ├── middleware/         # Idempotência
    ├── pagination/        # Paginação padrão
    └── views/             # Health check, Scalar
```

## 📌 Endpoints Principais

| Método           | Rota                           | Descrição                      |
| ---------------- | ------------------------------ | ------------------------------ |
| `GET`            | `/health/`                     | Health check (DB + Redis)      |
| `GET/POST`       | `/api/v1/customers/`           | Listar / Criar clientes        |
| `GET/PUT/DELETE` | `/api/v1/customers/{id}/`      | Detalhar / Atualizar / Remover |
| `GET/POST`       | `/api/v1/products/`            | Listar / Criar produtos        |
| `GET/PUT/DELETE` | `/api/v1/products/{id}/`       | Detalhar / Atualizar / Remover |
| `PATCH`          | `/api/v1/products/{id}/stock/` | Atualizar estoque              |
| `GET/POST`       | `/api/v1/orders/`              | Listar / Criar pedidos         |
| `GET/DELETE`     | `/api/v1/orders/{id}/`         | Detalhar / Remover             |
| `PATCH`          | `/api/v1/orders/{id}/status/`  | Atualizar status               |
| `GET`            | `/api/v1/orders/{id}/history/` | Histórico de transições        |

## ⚙️ Variáveis de Ambiente

| Variável        | Descrição               | Default                |
| --------------- | ----------------------- | ---------------------- |
| `SECRET_KEY`    | Chave secreta do Django | —                      |
| `DEBUG`         | Modo debug              | `False`                |
| `ALLOWED_HOSTS` | Hosts permitidos        | —                      |
| `DB_NAME`       | Nome do banco MySQL     | `erp_orders`           |
| `DB_USER`       | Usuário MySQL           | `erp_user`             |
| `DB_PASSWORD`   | Senha MySQL             | `erp_password`         |
| `DB_HOST`       | Host MySQL              | `db`                   |
| `DB_PORT`       | Porta MySQL             | `3306`                 |
| `REDIS_URL`     | URL do Redis            | `redis://redis:6379/0` |

## 📄 Licença

MIT

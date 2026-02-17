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

- [Python 3.11+](https://www.python.org/downloads/)
- [Docker](https://www.docker.com/) e Docker Compose instalados

### 1. Clonar repositório

```bash
git clone https://github.com/augusto49/Sistema-ERP-Gest-o-de-Pedidos.git
cd Sistema-ERP-Gest-o-de-Pedidos
```

### 2. Configurar variáveis de ambiente

```bash
# Linux/macOS
cp .env.example .env

# Windows (PowerShell)
Copy-Item .env.example .env
```

### 3. Opção A — Docker (recomendado)

```bash
docker-compose up --build
```

Isso inicia automaticamente:

- **API** em `http://localhost:8000`
- **MySQL** na porta `3307`
- **Redis** na porta `6379`
- Migrations aplicadas automaticamente no startup

#### Seed de dados (opcional)

```bash
docker-compose exec web python manage.py seed
```

### 3. Opção B — Local (sem Docker)

> Requer MySQL e Redis rodando localmente. Ajuste as variáveis no `.env`.

```bash
# Criar e ativar ambiente virtual
python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows (PowerShell)
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Aplicar migrations
python src/manage.py migrate

# Popular dados iniciais (opcional)
python src/manage.py seed

# Iniciar servidor de desenvolvimento
python src/manage.py runserver
```

### 4. Verificar saúde

```bash
curl http://localhost:8000/health/
```

### 5. Acessar documentação

| Ferramenta  | URL                               |
| ----------- | --------------------------------- |
| Swagger UI  | http://localhost:8000/api/docs/   |
| Redoc       | http://localhost:8000/api/redoc/  |
| Scalar      | http://localhost:8000/api/scalar/ |
| Schema JSON | http://localhost:8000/api/schema/ |

## 🧪 Testes

### Rodar via Docker

```bash
docker-compose exec web pytest -v
```

### Rodar localmente

```bash
# Criar venv (se ainda não existir)
python -m venv venv

# Ativar venv
# Linux/macOS:   source venv/bin/activate
# Windows:       venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Rodar testes
pytest -v
```

> Os testes usam SQLite em memória (`settings_test.py`) — não precisa de MySQL/Redis.

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

## 🏗 Decisões Arquiteturais

| Decisão                                                | Motivação                                                         |
| ------------------------------------------------------ | ----------------------------------------------------------------- |
| **Clean Architecture** (Controller→Service→Repository) | Testabilidade e separação de responsabilidades                    |
| **Repository Pattern com Interfaces ABC**              | Inversão de dependência — services não dependem do Django ORM     |
| **Pessimistic Locking** (`SELECT FOR UPDATE`)          | Previne race conditions no estoque sem lógica de retry no cliente |
| **Domain Events via EventBus**                         | Desacopla efeitos colaterais das operações principais             |
| **Soft Delete** (`deleted_at`)                         | Preserva integridade referencial e permite auditoria              |
| **Idempotência via Redis**                             | Garante que retries com `Idempotency-Key` não criam duplicatas    |
| **Snapshots em OrderItem**                             | Grava `product_name`, `sku`, `unit_price` no momento da compra    |
| **structlog com JSON**                                 | Logs estruturados, parseáveis por ferramentas como ELK/Datadog    |

> Para detalhes sobre trade-offs e fluxo de dados, veja [ARCHITECTURE.md](ARCHITECTURE.md).

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

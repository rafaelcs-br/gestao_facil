# Estágio 1: Builder
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Cache e instalação de dependências
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

COPY . .

# Instalação do projeto e coleta de estáticos
# Nota: O collectstatic precisa rodar aqui para que a pasta exista
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Coleta os arquivos estáticos (usando dummy env vars se necessário)
RUN DJANGO_SECRET_KEY=dummy uv run python manage.py collectstatic --noinput


# Estágio 2: Runtime
FROM python:3.14-slim-bookworm

WORKDIR /app

# Copia o ambiente virtual
COPY --from=builder /app/.venv /app/.venv
# COPIA A PASTA DE ESTÁTICOS GERADA NO BUILDER (Crucial!)
COPY --from=builder /app/staticfiles /app/staticfiles

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=setup.settings

COPY . .

EXPOSE 8000

# Script de inicialização para rodar migrações antes do Gunicorn
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn --bind 0.0.0.0:8000 setup.wsgi:application"]
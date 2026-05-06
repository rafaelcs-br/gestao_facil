# Estágio 1: Builder
# Utilizamos a imagem do uv compatível com Python 3.14
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

# Cache das dependências
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

COPY . .

# Instalação final do projeto
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Execute migrações e colete arquivos estáticos
RUN uv run python manage.py collectstatic --noinput
RUN uv run python manage.py migrate

# Estágio 2: Runtime
# Alterado para python:3.14-slim-bookworm
FROM python:3.14-slim-bookworm

WORKDIR /app

# Copia apenas o venv gerado no estágio anterior
COPY --from=builder /app/.venv /app/.venv

# Garante que o Python 3.14 do venv seja o padrão
ENV PATH="/app/.venv/bin:$PATH"

# Copia o código fonte
COPY . .

# Configurações Django
ENV DJANGO_SETTINGS_MODULE=setup.settings
EXPOSE 8000

# Execução com Gunicorn
# Nota: Verifique se o gunicorn está listado no seu pyproject.toml
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "setup.wsgi:application"]

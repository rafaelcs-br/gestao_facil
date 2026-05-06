# Use a slim Python base image compatible com Python 3.14
FROM python:3.14-slim

# Defina o diretório de trabalho da aplicação
WORKDIR /app

# Copie apenas arquivos de dependências primeiro para acelerar o cache de build
COPY pyproject.toml uv.lock README.md ./

# Instale dependências de sistema necessárias e uv via pip
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && python -m pip install --upgrade pip setuptools wheel uv \
    && uv --version \
    && rm -rf /var/lib/apt/lists/*

# Crie o ambiente virtual e sincronize dependências
RUN uv venv
RUN uv sync --frozen-lockfile

# Copie todo o código da aplicação
COPY . .

# Execute migrações e colete arquivos estáticos
RUN uv run python manage.py collectstatic --noinput
RUN uv run python manage.py migrate

# Defina variáveis de ambiente padrão
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=setup.settings
ENV DEBUG=False
ENV SECRET_KEY=django-insecure-production-key-change-me
ENV ALLOWED_HOSTS=*

# Exponha a porta usada pelo Gunicorn
EXPOSE 80

# Comando padrão para iniciar a aplicação em produção
CMD ["uv", "run", "gunicorn", "setup.wsgi:application", "--bind", "0.0.0.0:80", "--workers", "1", "--threads", "3"]

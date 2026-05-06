# Use a slim Python base image compatible com Python 3.14
FROM python:3.14-slim

# Defina o diretório de trabalho da aplicação
WORKDIR /app

# Copie apenas arquivos de dependências primeiro para acelerar o cache de build
COPY pyproject.toml pyproject.toml
COPY README.md README.md

# Instale dependências de sistema necessárias
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install "setuptools>=61.0" \
    && python -m pip install . \
    && apt-get purge -y --auto-remove gcc \
    && rm -rf /var/lib/apt/lists/*

# Copie todo o código da aplicação
COPY . .

# Defina variáveis de ambiente padrão
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=setup.settings

# Exponha a porta usada pelo Gunicorn
EXPOSE 8000

# Comando padrão para iniciar a aplicação em produção
CMD ["gunicorn", "setup.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]

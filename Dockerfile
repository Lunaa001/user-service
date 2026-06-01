FROM python:3.12-slim

WORKDIR /app

# Crear usuario sin privilegios antes de realizar operaciones
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Instalar dependencias de build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar herramienta de gestión de dependencias
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copiar archivos de definición de dependencias
COPY pyproject.toml uv.lock* ./

# Instalar dependencias
RUN uv sync

# Copiar código fuente
COPY . .

# Asegurar permisos correctos para el usuario no-root
RUN chown -R appuser:appuser /app

# Cambiar al usuario sin privilegios
USER appuser

# Puerto estándar interno
EXPOSE 5000

# Comando de inicio (puerto estandarizado a 5000)
CMD ["uv", "run", "granian", "--interface", "wsgi", "main:app", "--host", "0.0.0.0", "--port", "5000", "--workers", "2"]

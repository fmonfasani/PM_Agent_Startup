# Dockerfile para PM Bot Enterprise
FROM python:3.11-slim

# Metadatos
LABEL maintainer="PM Bot Enterprise Team"
LABEL version="1.0.0"
LABEL description="Sistema de Gestión de Proyectos con Agentes IA"

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Crear usuario no-root para seguridad
RUN groupadd -r pmbot && useradd --no-log-init -r -g pmbot pmbot

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar Ollama (opcional, para modelos locales)
RUN curl -fsSL https://ollama.ai/install.sh | sh || echo "Ollama installation skipped"

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements primero para mejor caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Crear directorios necesarios
RUN mkdir -p data logs agents templates prompts models projects \
    && chown -R pmbot:pmbot /app

# Cambiar a usuario no-root
USER pmbot

# Exponer puertos
EXPOSE 5000 8000 11434

# Configurar variables de entorno por defecto
ENV OLLAMA_HOST=http://localhost:11434
ENV LOG_LEVEL=INFO
ENV MAX_CONCURRENT_PROJECTS=5

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/api/system/health')" || exit 1

# Comando por defecto
CMD ["python", "run_pm.py", "--dashboard", "--host", "0.0.0.0"]

# Dockerfile multi-stage para producción
FROM python:3.11-slim as production

# Copiar solo lo necesario desde la etapa anterior
COPY --from=0 /app /app
COPY --from=0 /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

WORKDIR /app

# Usuario no-root
USER pmbot

# Comando optimizado para producción
CMD ["python", "run_pm.py", "--dashboard", "--host", "0.0.0.0", "--port", "5000"]   
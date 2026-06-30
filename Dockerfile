FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar codigo fuente
COPY . .

# Crear directorios necesarios
RUN mkdir -p logs data

# Puerto del dashboard
EXPOSE 8501

# Script de inicio
COPY start.sh .
RUN chmod +x start.sh

# Iniciar bot y dashboard juntos
CMD ["./start.sh"]

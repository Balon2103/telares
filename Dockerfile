# Imagen base
FROM python:3.10-slim

# Instala dependencias del sistema (incluye pg_dump)
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Crea el directorio de trabajo
WORKDIR /app

# Copia los requerimientos e instala dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instala psycopg2-binary (para conexión PostgreSQL)
RUN pip install --no-cache-dir psycopg2-binary

# Copia el resto del código
COPY . .

# Expone el puerto (si usas FastAPI o Flask)
EXPOSE 8080

# Comando de inicio
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]

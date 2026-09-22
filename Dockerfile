# Imagen base con Python
FROM python:3.12-slim

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar las dependencias primero para aprovechar la caché de Docker
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del proyecto
COPY app ./app

# Exponer el puerto de FastAPI
EXPOSE 8000

# Iniciar FastAPI con Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
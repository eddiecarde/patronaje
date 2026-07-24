# Imagen de la app web de patronaje (FastAPI + motor de patrones)
FROM python:3.12-slim

# dependencias del sistema para shapely (GEOS) y reportlab
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgeos-c1v5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml README.md ./
COPY patronaje ./patronaje

EXPOSE 8000

# uvicorn sirve la app (host 0.0.0.0 para exponer el contenedor)
CMD ["uvicorn", "patronaje.app:app", "--host", "0.0.0.0", "--port", "8000"]

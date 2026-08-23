FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

EXPOSE 8000

# In produzione sul NUC: eseguire prima "alembic upgrade head" (una tantum o
# come init-container), poi avviare il server. Per semplicità qui il comando
# di default avvia solo il server.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

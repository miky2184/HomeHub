FROM python:3.12-slim

# Il container di base è in UTC. Tutta l'app (aggregator, cutoff orari,
# confronto con gli orari locali restituiti da Open-Meteo con timezone=auto,
# ecc.) usa datetime.now() assumendo l'ora locale italiana: impostiamo quindi
# esplicitamente il fuso del container, altrimenti datetime.now() resta in
# UTC e ogni confronto con "adesso" risulta sfasato di 1-2 ore.
ENV TZ=Europe/Rome
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

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

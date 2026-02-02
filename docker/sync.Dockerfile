FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    httpx \
    psycopg2-binary \
    pandas \
    python-dotenv

COPY db.py .
COPY sync/ sync/

EXPOSE 8000

CMD ["uvicorn", "sync.api:app", "--host", "0.0.0.0", "--port", "8000"]

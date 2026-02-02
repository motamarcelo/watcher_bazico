FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    streamlit \
    psycopg2-binary \
    pandas \
    plotly \
    python-dotenv

COPY db.py .
COPY app.py .
COPY pages/ pages/

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]

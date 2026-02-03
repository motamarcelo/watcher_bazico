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

# Heroku usa a variável PORT
CMD streamlit run app.py --server.port=$PORT --server.address=0.0.0.0

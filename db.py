import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return psycopg2.connect(
        host=os.getenv("SUPA_HOST"),
        port=os.getenv("SUPA_PORT"),
        dbname=os.getenv("SUPA_DB"),
        user=os.getenv("SUPA_USER"),
        password=os.getenv("SUPA_PASS"),
    )


def query_view(view_name: str) -> pd.DataFrame:
    """Lê uma view/tabela do Supabase e retorna um DataFrame."""
    conn = get_connection()
    try:
        df = pd.read_sql(f"SELECT * FROM {view_name}", conn)
    finally:
        conn.close()
    return df

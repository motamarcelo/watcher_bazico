import os
from urllib.parse import quote_plus

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
import streamlit as st

load_dotenv()

password = quote_plus(os.getenv("password", ""))
conn_str = (
    f"postgresql+psycopg://{os.getenv('user')}:{password}"
    f"@{os.getenv('host')}:{os.getenv('port')}/{os.getenv('dbname')}"
)
engine = create_engine(conn_str)

st.set_page_config(page_title="Watcher - Histórico de Preço", layout="wide")
st.title("Histórico de Preço")

@st.cache_data(ttl=120)
def load_data():
    sql = "SELECT total_vendido, ticket_medio, total_clientes, quantidade_vendas, mes FROM v_vendas_total_mes ORDER BY mes"
    df = pd.read_sql(sql, engine)
    df["mes"] = pd.to_datetime(df["mes"]).dt.to_period("M").dt.to_timestamp()
    month_labels = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    df["mes_legenda"] = (
        df["mes"].dt.month.map(lambda m: month_labels[m - 1])
        + "/"
        + df["mes"].dt.year.astype(str)
    )
    return df

df_vendas = load_data()
st.line_chart(df_vendas, x="mes_legenda", y="total_vendido", use_container_width=True)

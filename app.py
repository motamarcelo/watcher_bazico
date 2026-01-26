import streamlit as st
import pandas as pd
from db import get_connection

st.title("Watcher - Vendas")

@st.cache_resource
def get_conn():
    return get_connection()

conn = get_conn()

@st.cache_data(ttl=60)
def get_vendas():
    query = "SELECT * FROM vendas LIMIT 50"
    return pd.read_sql(query, conn)

df = get_vendas()
st.dataframe(df)

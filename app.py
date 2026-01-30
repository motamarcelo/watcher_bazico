import streamlit as st
import pandas as pd
import plotly.express as px
from db import query_view

st.set_page_config(page_title="Watcher", layout="wide")
st.title("Watcher Dashboard")

VIEW_NAME = "public.vw_vendas_sku_diarias"


@st.cache_data
def load_data():
    df = query_view(VIEW_NAME)
    df["data_venda"] = pd.to_datetime(df["data_venda"])
    return df


df = load_data()

# --- Filtros ---
col_filtro1, col_filtro2 = st.columns([3, 1])

skus = df[["sku", "produto_nome"]].drop_duplicates().sort_values("sku")
sku_options = {row.sku: f"{row.sku} - {row.produto_nome}" for _, row in skus.iterrows()}

with col_filtro1:
    selected = st.multiselect(
        "Filtrar por SKU (vazio = todos)",
        options=list(sku_options.keys()),
        format_func=lambda x: sku_options[x],
    )

with col_filtro2:
    agrupamento = st.selectbox(
        "Agrupar por",
        options=["Diário", "Semanal", "Mensal"],
    )

# --- Filtro de data ---
data_min = df["data_venda"].min().date()
data_max = df["data_venda"].max().date()

col_data1, col_data2 = st.columns(2)
with col_data1:
    data_inicio = st.date_input("Data inicial", value=None, min_value=data_min, max_value=data_max)
with col_data2:
    data_fim = st.date_input("Data final", value=None, min_value=data_min, max_value=data_max)

if selected:
    df = df[df["sku"].isin(selected)]
if data_inicio:
    df = df[df["data_venda"] >= pd.Timestamp(data_inicio)]
if data_fim:
    df = df[df["data_venda"] <= pd.Timestamp(data_fim)]

# --- Agrupamento temporal ---
freq_map = {"Diário": "D", "Semanal": "W-MON", "Mensal": "MS"}
freq = freq_map[agrupamento]

chart_df = (
    df.groupby([pd.Grouper(key="data_venda", freq=freq), "sku"], as_index=False)
    .agg(valor_total_vendas=("valor_total_vendas", "sum"), qtd_vendida=("qtd_vendida", "sum"))
)

# --- Gráfico ---
fig = px.line(
    chart_df,
    x="data_venda",
    y="valor_total_vendas",
    color="sku",
    custom_data=["qtd_vendida"],
    labels={"data_venda": "Data", "valor_total_vendas": "Vendas (R$)", "sku": "SKU"},
)
fig.update_traces(
    hovertemplate="<b>%{x}</b><br>Vendas: R$ %{y:,.2f}<br>Qtd: %{customdata[0]:,.0f}<extra>%{fullData.name}</extra>"
)
fig.update_layout(hovermode="x unified")

st.plotly_chart(fig, width='stretch')

# --- Ranking Top 10 ---
st.subheader("Top 10 Produtos Mais Vendidos")

ranking = (
    df.groupby(["sku", "produto_nome"], as_index=False)
    .agg(total_vendas=("valor_total_vendas", "sum"), total_qtd=("qtd_vendida", "sum"))
    .sort_values("total_vendas", ascending=False)
    .head(10)
    .reset_index(drop=True)
)
ranking.index = ranking.index + 1
ranking.columns = ["SKU", "Produto", "Total Vendas (R$)", "Qtd Vendida"]

st.dataframe(ranking, width='stretch')

# --- Dados ---
st.subheader("Dados")
st.dataframe(df, width='stretch')

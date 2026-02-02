import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from db import query_view

st.set_page_config(page_title="Estoque x Vendas", layout="wide")
st.title("Estoque x Vendas Mensal")

VIEW_NAME = "public.vw_estoque_vendas_mensal"


@st.cache_data
def load_data():
    df = query_view(VIEW_NAME)
    df["mes"] = pd.to_datetime(df["mes"])
    return df


df = load_data()

# --- Filtros ---
col_filtro1, _ = st.columns([3, 1])

skus_disponiveis = sorted(df["sku"].unique())

with col_filtro1:
    selected = st.multiselect(
        "Filtrar por SKU (vazio = todos)",
        options=skus_disponiveis,
    )

# --- Filtro de data ---
data_min = df["mes"].min().date()
data_max = df["mes"].max().date()

col_data1, col_data2 = st.columns(2)
with col_data1:
    data_inicio = st.date_input("Data inicial", value=None, min_value=data_min, max_value=data_max)
with col_data2:
    data_fim = st.date_input("Data final", value=None, min_value=data_min, max_value=data_max)

if selected:
    df = df[df["sku"].isin(selected)]
if data_inicio:
    df = df[df["mes"] >= pd.Timestamp(data_inicio)]
if data_fim:
    df = df[df["mes"] <= pd.Timestamp(data_fim)]

# --- Gráfico: Estoque acumulado vs Vendas ---
agg_df = (
    df.groupby("mes", as_index=False)
    .agg(estoque_acumulado=("estoque_acumulado", "sum"), qtd_vendida=("qtd_vendida", "sum"))
)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=agg_df["mes"], y=agg_df["estoque_acumulado"],
    name="Estoque Acumulado", mode="lines+markers",
    line=dict(color="#636EFA", width=2),
))
fig.add_trace(go.Bar(
    x=agg_df["mes"], y=agg_df["qtd_vendida"],
    name="Qtd Vendida", marker_color="#EF553B", opacity=0.6,
))
fig.update_layout(
    hovermode="x unified",
    xaxis_title="Mês",
    yaxis_title="Quantidade",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)

st.plotly_chart(fig, width='stretch')

# --- Alertas: meses com estoque baixo e queda de vendas ---
st.subheader("Meses com Estoque Baixo")

if selected and len(selected) <= 5:
    for sku in selected:
        sku_df = df[df["sku"] == sku].sort_values("mes")
        baixo = sku_df[sku_df["estoque_acumulado"] <= 0]
        if not baixo.empty:
            meses = ", ".join(baixo["mes"].dt.strftime("%Y-%m"))
            st.warning(f"**{sku}** — estoque zerado/negativo em: {meses}")
        else:
            st.success(f"**{sku}** — estoque sempre positivo no período")
else:
    zerados = df[df["estoque_acumulado"] <= 0].groupby("sku").size().reset_index(name="meses_sem_estoque")
    zerados = zerados.sort_values("meses_sem_estoque", ascending=False).head(20)
    if not zerados.empty:
        st.dataframe(zerados.rename(columns={"sku": "SKU", "meses_sem_estoque": "Meses sem Estoque"}), width='stretch')
    else:
        st.success("Nenhum SKU com estoque zerado/negativo no período.")

# --- Tabela detalhada ---
st.subheader("Dados por SKU/Mês")

display_df = df.copy()
display_df["mes"] = display_df["mes"].dt.strftime("%Y-%m")
display_df = display_df.sort_values(["sku", "mes"])
display_df.columns = ["SKU", "Mês", "Qtd Comprada", "Qtd Vendida", "Estoque Acumulado"]

st.dataframe(display_df, width='stretch')

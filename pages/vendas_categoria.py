import streamlit as st
import pandas as pd
import plotly.express as px
from db import query_sql

st.set_page_config(page_title="Vendas por Categoria", layout="wide")
st.title("Vendas por Categoria")

QUERY = """
SELECT
    v.data_venda,
    vi.produto_id,
    vi.produto_codigo,
    vi.produto_nome,
    vi.quantidade,
    vi.valor_unitario,
    vi.valor_total,
    vw.categoria,
    vw.modelo,
    vw.cor,
    vw.tecido,
    vw.tamanho
FROM vendas_itens vi
JOIN vendas v ON v.id = vi.venda_id
LEFT JOIN vw_estoque_por_produto_v6 vw ON vw.produto_id = vi.produto_id
"""

HIERARQUIA = ["categoria", "modelo", "cor", "tecido", "tamanho"]
LABELS = {
    "categoria": "Categoria",
    "modelo": "Modelo",
    "cor": "Cor",
    "tecido": "Tecido",
    "tamanho": "Tamanho",
    "produto_codigo": "SKU",
}


@st.cache_data
def load_data():
    df = query_sql(QUERY)
    df["data_venda"] = pd.to_datetime(df["data_venda"])
    for col in HIERARQUIA:
        df[col] = df[col].fillna(f"Sem {col}")
    return df


df = load_data()

# ============================================================
# Filtros hierárquicos (cascata)
# ============================================================
st.subheader("Filtros")

filtered = df.copy()

# --- Data + Agrupamento ---
col_data1, col_data2, col_agrup = st.columns([2, 2, 1])
data_min = df["data_venda"].min().date()
data_max = df["data_venda"].max().date()

with col_data1:
    data_inicio = st.date_input("Data inicial", value=None, min_value=data_min, max_value=data_max)
with col_data2:
    data_fim = st.date_input("Data final", value=None, min_value=data_min, max_value=data_max)
with col_agrup:
    agrupamento = st.selectbox("Agrupar por", options=["Diário", "Semanal", "Mensal"])

if data_inicio:
    filtered = filtered[filtered["data_venda"] >= pd.Timestamp(data_inicio)]
if data_fim:
    filtered = filtered[filtered["data_venda"] <= pd.Timestamp(data_fim)]

# --- Cascata: cada filtro restringe os próximos ---
cols = st.columns(len(HIERARQUIA))
selecoes = {}

for i, dim in enumerate(HIERARQUIA):
    opcoes = sorted(filtered[dim].unique())
    with cols[i]:
        sel = st.multiselect(LABELS[dim], options=opcoes, key=f"filtro_{dim}")
    selecoes[dim] = sel
    if sel:
        filtered = filtered[filtered[dim].isin(sel)]

# ============================================================
# Detalhar por (independente dos filtros)
# ============================================================
dims_livres = [d for d in HIERARQUIA if not selecoes[d]]
opcoes_detalhe = dims_livres if dims_livres else ["produto_codigo"]

col_det, _ = st.columns([2, 3])
with col_det:
    dim_detalhe = st.selectbox(
        "Detalhar por",
        options=opcoes_detalhe,
        format_func=lambda x: LABELS[x],
    )

label_detalhe = LABELS[dim_detalhe]

# ============================================================
# KPIs
# ============================================================
st.divider()

total_vendas = filtered["valor_total"].sum()
total_qtd = filtered["quantidade"].sum()
ticket_medio = total_vendas / total_qtd if total_qtd > 0 else 0
n_produtos = filtered["produto_id"].nunique()

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Faturamento", f"R$ {total_vendas:,.2f}")
kpi2.metric("Qtd Vendida", f"{total_qtd:,.0f}")
kpi3.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}")
kpi4.metric("Produtos Únicos", f"{n_produtos}")

# ============================================================
# Gráfico de vendas no tempo
# ============================================================
st.divider()
st.subheader(f"Vendas no Tempo por {label_detalhe}")

freq_map = {"Diário": "D", "Semanal": "W-MON", "Mensal": "MS"}
freq = freq_map[agrupamento]

chart_df = (
    filtered.groupby([pd.Grouper(key="data_venda", freq=freq), dim_detalhe], as_index=False)
    .agg(valor_total=("valor_total", "sum"), quantidade=("quantidade", "sum"))
)

# Top 10 pra não poluir o gráfico
top_valores = (
    filtered.groupby(dim_detalhe, as_index=False)["valor_total"]
    .sum()
    .nlargest(10, "valor_total")[dim_detalhe]
)
chart_df_top = chart_df[chart_df[dim_detalhe].isin(top_valores)]

fig_line = px.line(
    chart_df_top,
    x="data_venda",
    y="valor_total",
    color=dim_detalhe,
    custom_data=["quantidade"],
    labels={"data_venda": "Data", "valor_total": "Vendas (R$)", dim_detalhe: label_detalhe},
)
fig_line.update_traces(
    hovertemplate="<b>%{x}</b><br>R$ %{y:,.2f}<br>Qtd: %{customdata[0]:,.0f}<extra>%{fullData.name}</extra>"
)
fig_line.update_layout(hovermode="x unified")

st.plotly_chart(fig_line, use_container_width=True)

# ============================================================
# Ranking + Distribuição
# ============================================================
st.subheader(f"Ranking e Distribuição por {label_detalhe}")

col_rank, col_pie = st.columns([3, 2])

ranking = (
    filtered.groupby(dim_detalhe, as_index=False)
    .agg(total_vendas=("valor_total", "sum"), total_qtd=("quantidade", "sum"))
    .sort_values("total_vendas", ascending=False)
    .reset_index(drop=True)
)

with col_rank:
    top_n = ranking.head(15).copy()
    fig_bar = px.bar(
        top_n,
        x="total_vendas",
        y=dim_detalhe,
        orientation="h",
        text="total_vendas",
        custom_data=["total_qtd"],
        labels={"total_vendas": "Vendas (R$)", dim_detalhe: label_detalhe},
    )
    fig_bar.update_traces(
        texttemplate="R$ %{text:,.0f}",
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>R$ %{x:,.2f}<br>Qtd: %{customdata[0]:,.0f}<extra></extra>",
    )
    fig_bar.update_layout(yaxis=dict(autorange="reversed"), showlegend=False)
    st.plotly_chart(fig_bar, use_container_width=True)

with col_pie:
    top_pie = ranking.head(10).copy()
    outros = ranking.iloc[10:]
    if not outros.empty:
        outros_row = pd.DataFrame({
            dim_detalhe: ["Outros"],
            "total_vendas": [outros["total_vendas"].sum()],
            "total_qtd": [outros["total_qtd"].sum()],
        })
        top_pie = pd.concat([top_pie, outros_row], ignore_index=True)

    fig_pie = px.pie(
        top_pie,
        names=dim_detalhe,
        values="total_vendas",
        hole=0.4,
    )
    fig_pie.update_traces(textinfo="percent+label", hovertemplate="<b>%{label}</b><br>R$ %{value:,.2f}<extra></extra>")
    st.plotly_chart(fig_pie, use_container_width=True)

# ============================================================
# Ranking completo
# ============================================================
st.subheader("Ranking Completo")

ranking_display = ranking.copy()
ranking_display.index = range(1, len(ranking_display) + 1)
ranking_display.columns = [label_detalhe, "Total Vendas (R$)", "Qtd Vendida"]

st.dataframe(ranking_display, use_container_width=True)

# ============================================================
# Dados detalhados
# ============================================================
with st.expander("Dados detalhados"):
    st.dataframe(filtered, use_container_width=True)

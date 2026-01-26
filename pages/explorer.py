# import streamlit as st
# import pandas as pd
# import pygwalker as pyg
# from pygwalker.api.streamlit import StreamlitRenderer
# from db import get_connection

# st.set_page_config(layout="wide")

# CUSTOM_STYLE = """
# <style>
# [data-testid="stSidebar"],
# [data-testid="stSidebarNav"] {
#     min-width: 180px;
#     max-width: 180px;
# }
# iframe[title="pygwalker-renderer"] {
#     min-height: 900px !important;
# }
# </style>
# """

# st.markdown(CUSTOM_STYLE, unsafe_allow_html=True)
# st.title("Explorer - PyGWalker")

# @st.cache_resource
# def get_conn():
#     return get_connection()

# conn = get_conn()

# @st.cache_data(ttl=60)
# def get_vendas():
#     query = "SELECT * FROM vendas"
#     return pd.read_sql(query, conn)

# df = get_vendas()

# renderer = StreamlitRenderer(df, spec="./gwalker_config.json", spec_io_mode="rw")
# renderer.explorer()

import streamlit as st

st.set_page_config(
    page_title="Dashboard de Projetos",
    layout="wide",
    initial_sidebar_state="expanded",
)

pg = st.navigation([
    st.Page("pages/entregues.py",  title="Projetos Entregues",    icon="✅"),
    st.Page("pages/andamento.py",  title="Projetos em Andamento", icon="🔄"),
])
pg.run()

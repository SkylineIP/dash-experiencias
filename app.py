import streamlit as st
from config import SENHA

st.set_page_config(
    page_title="Dashboard de Projetos",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _check_auth() -> bool:
    if st.session_state.get("autenticado"):
        return True

    st.title("Dashboard de Projetos")
    st.markdown("---")

    col = st.columns([1, 2, 1])[1]
    with col:
        st.markdown("### Acesso restrito")
        senha = st.text_input("Senha", type="password", placeholder="Digite a senha de acesso")
        if st.button("Entrar", use_container_width=True):
            if senha == SENHA:
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("Senha incorreta.")

    return False


if not _check_auth():
    st.stop()

# Botão de sair na sidebar
with st.sidebar:
    if st.button("Sair", use_container_width=True):
        st.session_state["autenticado"] = False
        st.rerun()

pg = st.navigation([
    st.Page("pages/entregues.py",  title="Projetos Entregues",    icon="✅"),
    st.Page("pages/andamento.py",  title="Projetos em Andamento", icon="🔄"),
])
pg.run()

import streamlit as st
import pandas as pd
import plotly.express as px
import requests

from config import ANO_ATUAL, EQUIPES, CORES_EQUIPE, URL_ENTREGUES
from data.loader import load_data, prepare_data
from data.processing import detect_col, explode_tipos, mes_label
from components.equipe import render_equipe
from components.servicos import render_servicos
from components.pessoa import render_pessoa
from components.produtos import render_produtos

st.title("Projetos Entregues")

# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------
with st.sidebar:
    if st.button("Atualizar dados"):
        st.cache_data.clear()

try:
    with st.spinner("Carregando dados..."):
        df_raw = load_data(URL_ENTREGUES)
except requests.HTTPError as e:
    st.error(f"Não foi possível acessar a planilha ({e.response.status_code}).")
    st.stop()
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

df = prepare_data(df_raw)

col_nome   = detect_col(df, ["nome"])
col_tipo   = detect_col(df, ["tipo de serviço", "tipo de servico", "tipo"])
col_emp    = detect_col(df, ["emprendimento", "empreendimento", "incorporadora"])
col_prazo  = detect_col(df, ["prazo"])
col_outros = detect_col(df, ["outros"])
col_envio  = detect_col(df, ["data de envio", "envio"])

if not col_nome:
    st.error("Coluna 'Nome' não encontrada.")
    st.stop()
if not col_tipo:
    st.error("Coluna 'Tipo de serviço' não encontrada.")
    st.stop()

cols_completas = [c for c in [col_nome, col_emp, col_prazo, col_outros, col_tipo, col_envio] if c]

# ------------------------------------------------------------------
# Sidebar — filtros
# ------------------------------------------------------------------
with st.sidebar:
    st.divider()
    st.header("Filtros")

    meses_sel: list[str] = []
    if "_mes_order" in df.columns:
        meses_sorted = (
            df.dropna(subset=["_mes_order"])
            .sort_values("_mes_order")["_mes_ano"]
            .unique()
            .tolist()
        )
        meses_sel = st.multiselect(
            "Mês",
            options=meses_sorted,
            default=meses_sorted,
            format_func=mes_label,
        )

    equipe_sel = st.multiselect(
        "Equipe",
        options=list(EQUIPES.keys()),
        default=list(EQUIPES.keys()),
    )

    tipos_raw = (
        df[col_tipo].astype(str)
        .str.split(r"[,;\n]+")
        .explode()
        .str.strip()
        .unique()
        .tolist()
    )
    tipos_disponiveis = sorted([str(t) for t in tipos_raw if t and str(t) not in ("nan", "")])
    tipos_sel = st.multiselect("Tipo de serviço", tipos_disponiveis, default=tipos_disponiveis)

# ------------------------------------------------------------------
# Aplicar filtros
# ------------------------------------------------------------------
df_f = df.copy()
if meses_sel and "_mes_ano" in df_f.columns:
    df_f = df_f[df_f["_mes_ano"].isin(meses_sel)]
if equipe_sel:
    df_f = df_f[df_f["_equipe"].isin(equipe_sel)]

df_exp = explode_tipos(df_f, col_tipo)
if tipos_sel:
    df_exp = df_exp[df_exp["_tipo"].isin(tipos_sel)]

# ------------------------------------------------------------------
# Indicador principal: produtos entregues
# ------------------------------------------------------------------
df_ano = df.copy()
if equipe_sel:
    df_ano = df_ano[df_ano["_equipe"].isin(equipe_sel)]
df_ano_exp = explode_tipos(df_ano, col_tipo)

render_produtos(df_ano, df_ano_exp, df_f, df_exp, col_nome, col_tipo, col_emp)

# ------------------------------------------------------------------
# KPIs gerais
# ------------------------------------------------------------------
st.subheader(f"Resumo Geral — {ANO_ATUAL}")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Atividades realizadas", f"{len(df_f):,}")
k2.metric("Pessoas ativas", df_f[col_nome].nunique())
tipo_top = df_exp["_tipo"].value_counts().idxmax() if not df_exp.empty else "—"
k3.metric("Tipo mais frequente", tipo_top)
mes_top = (
    df_f["_mes_ano"].value_counts().idxmax()
    if "_mes_ano" in df_f.columns and not df_f.empty else "—"
)
k4.metric("Mês mais movimentado", mes_label(mes_top) if mes_top != "—" else "—")

st.divider()

# ------------------------------------------------------------------
# Comparativo entre equipes
# ------------------------------------------------------------------
st.subheader("Comparativo entre equipes")
comp_col1, comp_col2 = st.columns(2)

with comp_col1:
    por_equipe = df_f["_equipe"].value_counts().reset_index()
    por_equipe.columns = ["Equipe", "Entregas"]
    fig_eq = px.bar(
        por_equipe, x="Equipe", y="Entregas",
        text="Entregas", color="Equipe",
        color_discrete_map=CORES_EQUIPE,
    )
    fig_eq.update_traces(textposition="outside")
    fig_eq.update_layout(showlegend=False, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig_eq, use_container_width=True)

with comp_col2:
    if "_mes_order" in df_f.columns and df_f["_mes_order"].notna().any():
        mensal_eq = (
            df_f.dropna(subset=["_mes_order"])
            .groupby(["_mes_order", "_equipe"])
            .size()
            .reset_index(name="Entregas")
            .sort_values("_mes_order")
        )
        mensal_eq["Mês"] = mensal_eq["_mes_order"].apply(lambda p: p.strftime("%b/%Y"))
        fig_eqm = px.line(
            mensal_eq, x="Mês", y="Entregas",
            color="_equipe", markers=True,
            color_discrete_map=CORES_EQUIPE,
            labels={"_equipe": "Equipe"},
            title="Entregas mensais por equipe",
        )
        fig_eqm.update_layout(margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig_eqm, use_container_width=True)

st.divider()

# ------------------------------------------------------------------
# Abas
# ------------------------------------------------------------------
abas = st.tabs(["Designers", "Programadores", "Serviços", "Detalhe por pessoa", "Tabela"])

for i, (equipe, cor) in enumerate(CORES_EQUIPE.items()):
    with abas[i]:
        membros   = EQUIPES[equipe]
        df_eq     = df_f[df_f[col_nome].isin(membros)]
        df_eq_exp = df_exp[df_exp[col_nome].isin(membros)]
        render_equipe(df_eq, df_eq_exp, col_nome, equipe, cor)

with abas[2]:
    render_servicos(df_f, df_exp, col_nome, cols_completas, col_envio)

with abas[3]:
    render_pessoa(df_f, df_exp, col_nome, cols_completas, col_envio)

with abas[4]:
    st.subheader("Tabela de entregas")
    busca = st.text_input("Buscar", "")
    display_df = df_f[cols_completas].copy()
    if col_envio and col_envio in display_df.columns:
        display_df[col_envio] = pd.to_datetime(
            display_df[col_envio], dayfirst=True, errors="coerce"
        ).dt.strftime("%d/%m/%Y %H:%M")
    if busca:
        mask = display_df.astype(str).apply(
            lambda c: c.str.contains(busca, case=False, na=False)
        ).any(axis=1)
        display_df = display_df[mask]
    st.dataframe(display_df.reset_index(drop=True), use_container_width=True, hide_index=True, height=500)
    st.caption(f"Exibindo {len(display_df):,} de {len(df_f):,} linhas")

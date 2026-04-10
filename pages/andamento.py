import streamlit as st
import pandas as pd
import plotly.express as px
import requests

from config import URL_ANDAMENTO, EQUIPES, CORES_EQUIPE, PRIORIDADES_PRAZO
from data.loader_andamento import load_andamento

st.title("Projetos em Andamento")

# ------------------------------------------------------------------
# Helpers de prioridade
# ------------------------------------------------------------------

def cor_prazo(dias: float) -> str:
    for dias_max, _, cor in PRIORIDADES_PRAZO:
        if dias <= dias_max:
            return cor
    return PRIORIDADES_PRAZO[-1][2]


def label_prazo(dias: float) -> str:
    for dias_max, label, _ in PRIORIDADES_PRAZO:
        if dias <= dias_max:
            return label
    return PRIORIDADES_PRAZO[-1][1]


STATUS_CORES = {
    "Em andamento":       "#3b82f6",
    "Aguardando retorno": "#eab308",
    "Pausado":            "#9ca3af",
}

# ------------------------------------------------------------------
# Carregar dados
# ------------------------------------------------------------------
if st.sidebar.button("Atualizar dados"):
    st.cache_data.clear()

try:
    with st.spinner("Carregando projetos em andamento..."):
        df = load_andamento(URL_ANDAMENTO)
except requests.HTTPError as e:
    st.error(f"Não foi possível acessar a planilha ({e.response.status_code}).")
    st.stop()
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

if df.empty:
    st.warning("Nenhum projeto encontrado na planilha.")
    st.stop()

col_nome   = "Nome"            if "Nome"            in df.columns else None
col_tarefa = "Tarefa"          if "Tarefa"          in df.columns else None
col_data   = "Data"            if "Data"            in df.columns else None
col_obs    = "Obs"             if "Obs"             in df.columns else None
col_tipo   = "Tipo de serviço" if "Tipo de serviço" in df.columns else None

# Adiciona coluna de prioridade se tiver data
if "_dias_restantes" in df.columns:
    df["_prioridade_label"] = df["_dias_restantes"].apply(
        lambda d: label_prazo(d) if pd.notna(d) else "Sem prazo"
    )
    df["_prioridade_cor"] = df["_dias_restantes"].apply(
        lambda d: cor_prazo(d) if pd.notna(d) else "#d1d5db"
    )

# ------------------------------------------------------------------
# Sidebar — filtros
# ------------------------------------------------------------------
with st.sidebar:
    st.divider()
    st.header("Filtros")

    equipe_sel = st.multiselect(
        "Equipe", options=list(EQUIPES.keys()), default=list(EQUIPES.keys()),
    )
    if col_nome:
        todas_pessoas = sorted(df[col_nome].unique().tolist())
        pessoa_sel = st.multiselect("Pessoa", todas_pessoas, default=todas_pessoas)

    status_opts = sorted(df["_status"].dropna().unique().tolist()) if "_status" in df.columns else []
    status_sel = st.multiselect("Status", status_opts, default=status_opts)

    st.divider()
    # Legenda de prioridades
    st.markdown("**Legenda de prazos**")
    for _, label, cor in PRIORIDADES_PRAZO:
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:8px;margin:2px 0'>"
            f"<div style='width:14px;height:14px;border-radius:50%;background:{cor}'></div>"
            f"<span style='font-size:0.85rem'>{label}</span></div>",
            unsafe_allow_html=True,
        )

# ------------------------------------------------------------------
# Aplicar filtros
# ------------------------------------------------------------------
df_f = df.copy()
if col_nome:
    if equipe_sel:
        df_f = df_f[df_f["_equipe"].isin(equipe_sel)]
    if pessoa_sel:
        df_f = df_f[df_f[col_nome].isin(pessoa_sel)]
if "_status" in df_f.columns and status_sel:
    df_f = df_f[df_f["_status"].isin(status_sel)]

# ------------------------------------------------------------------
# KPIs gerais
# ------------------------------------------------------------------
total      = len(df_f)
em_prod    = int((df_f["_status"] == "Em andamento").sum())      if "_status" in df_f.columns else 0
aguardando = int((df_f["_status"] == "Aguardando retorno").sum()) if "_status" in df_f.columns else 0
pausados   = int((df_f["_status"] == "Pausado").sum())           if "_status" in df_f.columns else 0
com_prazo  = df_f["_dias_restantes"].notna().sum()               if "_dias_restantes" in df_f.columns else 0
atrasados  = int((df_f["_dias_restantes"] <= 0).sum())           if "_dias_restantes" in df_f.columns else 0

st.subheader("Visão geral da esteira")
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total na esteira", total)
k2.metric("Em produção",      em_prod)
k3.metric("Aguardando retorno", aguardando)
k4.metric("Pausados",         pausados)
k5.metric("No prazo ou atrasados", atrasados)

st.divider()

# ------------------------------------------------------------------
# Destaques: Aguardando retorno e Pausados
# ------------------------------------------------------------------
col_dest1, col_dest2 = st.columns(2)
cols_dest = [c for c in [col_nome, col_tarefa, col_tipo, col_data, col_obs] if c]

def _tabela_destaque(df_sub: pd.DataFrame, cor: str, label: str, key: str) -> None:
    st.markdown(
        f"<div style='border-left:4px solid {cor}; padding-left:10px; margin-bottom:6px'>"
        f"<strong style='color:{cor}'>{label}</strong> — {len(df_sub)} projeto(s)"
        f"</div>",
        unsafe_allow_html=True,
    )
    if df_sub.empty:
        st.success("Nenhum projeto nesta situação.")
        return
    disp = df_sub[cols_dest].copy()
    if col_data and col_data in disp.columns:
        disp[col_data] = pd.to_datetime(
            disp[col_data], dayfirst=True, errors="coerce"
        ).dt.strftime("%d/%m/%Y").fillna("—")
    st.dataframe(disp.reset_index(drop=True), use_container_width=True, hide_index=True,
                 height=min(38 * (len(disp) + 1) + 10, 380))

with col_dest1:
    df_ag = df_f[df_f["_status"] == "Aguardando retorno"] if "_status" in df_f.columns else pd.DataFrame()
    _tabela_destaque(df_ag, "#eab308", "⏳ Aguardando retorno", "ag")

with col_dest2:
    df_pau = df_f[df_f["_status"] == "Pausado"] if "_status" in df_f.columns else pd.DataFrame()
    _tabela_destaque(df_pau, "#9ca3af", "⏸ Pausados", "pau")

st.divider()

# ------------------------------------------------------------------
# Por equipe
# ------------------------------------------------------------------
st.subheader("Por equipe")
tab_des, tab_prog = st.tabs(["Designers", "Programadores"])

def _render_equipe_andamento(df_eq: pd.DataFrame, equipe: str, cor: str) -> None:
    if df_eq.empty:
        st.info("Nenhum projeto ativo para esta equipe.")
        return

    e1, e2, e3, e4 = st.columns(4)
    e1.metric("Total",            len(df_eq))
    e2.metric("Em produção",      int((df_eq["_status"] == "Em andamento").sum())      if "_status" in df_eq.columns else "—")
    e3.metric("Aguardando",       int((df_eq["_status"] == "Aguardando retorno").sum()) if "_status" in df_eq.columns else "—")
    e4.metric("Pausados",         int((df_eq["_status"] == "Pausado").sum())            if "_status" in df_eq.columns else "—")

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        if col_nome:
            por_pessoa = df_eq[col_nome].value_counts().reset_index()
            por_pessoa.columns = ["Pessoa", "Projetos"]
            fig = px.bar(
                por_pessoa, x="Projetos", y="Pessoa",
                orientation="h", text="Projetos",
                color_discrete_sequence=[cor],
                title="Projetos por pessoa",
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(
                yaxis={"categoryorder": "total ascending"},
                margin=dict(l=0, r=20, t=40, b=0), showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True, key=f"and_bar_{equipe}")

    with col_g2:
        if col_nome and "_status" in df_eq.columns:
            sp = df_eq.groupby([col_nome, "_status"]).size().reset_index(name="Qtd")
            fig2 = px.bar(
                sp, x=col_nome, y="Qtd",
                color="_status", barmode="stack",
                color_discrete_map=STATUS_CORES,
                labels={"_status": "Status", col_nome: ""},
                title="Status por pessoa",
            )
            fig2.update_layout(margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig2, use_container_width=True, key=f"and_status_{equipe}")

    st.markdown("#### Projetos por pessoa")
    if col_nome:
        for pessoa in sorted(df_eq[col_nome].unique()):
            df_p = df_eq[df_eq[col_nome] == pessoa].copy()
            status_counts = df_p["_status"].value_counts().to_dict() if "_status" in df_p.columns else {}
            badges = " ".join(
                f"<span style='background:{STATUS_CORES.get(s, '#64748b')};color:white;"
                f"border-radius:4px;padding:1px 7px;font-size:0.75rem'>{s}: {n}</span>"
                for s, n in status_counts.items()
            )
            cols_tab = [c for c in [col_tarefa, col_tipo, col_data, col_obs] if c]
            disp = df_p[cols_tab].copy()
            if col_data and col_data in disp.columns:
                disp[col_data] = pd.to_datetime(
                    disp[col_data], dayfirst=True, errors="coerce"
                ).dt.strftime("%d/%m/%Y").fillna("—")

            with st.expander(f"**{pessoa}** — {len(df_p)} projeto(s)", expanded=False):
                st.markdown(badges, unsafe_allow_html=True)
                st.dataframe(
                    disp.reset_index(drop=True),
                    use_container_width=True, hide_index=True,
                    height=min(38 * (len(disp) + 1) + 10, 400),
                )

for tab, equipe in zip([tab_des, tab_prog], ["Designers", "Programadores"]):
    with tab:
        membros = EQUIPES[equipe]
        df_eq = df_f[df_f[col_nome].isin(membros)] if col_nome else pd.DataFrame()
        _render_equipe_andamento(df_eq, equipe, CORES_EQUIPE[equipe])

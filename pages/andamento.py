import streamlit as st
import pandas as pd
import plotly.express as px
import requests

from config import URL_ANDAMENTO, EQUIPES, CORES_EQUIPE, PRIORIDADES_PRAZO, TIPOS_PROJETO, TIPOS_AJUSTE
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
# Classificação: Projeto vs Ajuste
# ------------------------------------------------------------------
_set_projeto = set(TIPOS_PROJETO)
_set_ajuste  = set(TIPOS_AJUSTE)

def _classificar_categoria(tipo_puro) -> str:
    if pd.isna(tipo_puro) or str(tipo_puro).strip() == "":
        return "Outro"
    partes = [p.strip() for p in str(tipo_puro).split(",")]
    for p in partes:
        if p in _set_ajuste:
            return "Ajuste"
    for p in partes:
        if p in _set_projeto:
            return "Projeto"
    return "Outro"

if "_tipo_puro" in df_f.columns:
    df_f["_categoria"] = df_f["_tipo_puro"].apply(_classificar_categoria)
else:
    df_f["_categoria"] = "Outro"

# ------------------------------------------------------------------
# Helpers de renderização
# ------------------------------------------------------------------
cols_dest = [c for c in [col_nome, col_tarefa, col_tipo, col_data, col_obs] if c]
cols_pessoa = [c for c in [col_tarefa, col_tipo, col_data, col_obs] if c]


@st.dialog("Detalhes", width="large")
def _modal_lista(df_sub: pd.DataFrame, titulo: str) -> None:
    disp = df_sub[cols_dest].copy() if cols_dest else df_sub.copy()
    if col_data and col_data in disp.columns:
        disp[col_data] = pd.to_datetime(
            disp[col_data], dayfirst=True, errors="coerce"
        ).dt.strftime("%d/%m/%Y").fillna("—")
    st.markdown(f"**{titulo}** — {len(disp)} item(s)")
    if disp.empty:
        st.info("Nenhum item.")
    else:
        st.dataframe(disp.reset_index(drop=True), use_container_width=True,
                     hide_index=True, height=min(38 * (len(disp) + 1) + 10, 500))


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
    row_h = 38 * (len(disp) + 1) + 10
    st.dataframe(disp.reset_index(drop=True), use_container_width=True, hide_index=True,
                 height=row_h if row_h <= 300 else 300)


def _render_categoria(df_cat: pd.DataFrame, df_cat_todos: pd.DataFrame, equipe: str, cor: str, categoria: str) -> None:
    if df_cat.empty and df_cat_todos.empty:
        st.info(f"Nenhum item em '{categoria}' para esta equipe.")
        return

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        if col_nome:
            por_pessoa = df_cat[col_nome].value_counts().reset_index()
            por_pessoa.columns = ["Pessoa", "Itens"]
            fig = px.bar(
                por_pessoa, x="Itens", y="Pessoa",
                orientation="h", text="Itens",
                color_discrete_sequence=[cor],
                title="Por pessoa",
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(
                yaxis={"categoryorder": "total ascending"},
                margin=dict(l=0, r=20, t=40, b=0), showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True, key=f"bar_{equipe}_{categoria}")

    with col_g2:
        if col_nome and "_status" in df_cat.columns:
            sp = df_cat.groupby([col_nome, "_status"]).size().reset_index(name="Qtd")
            fig2 = px.bar(
                sp, x=col_nome, y="Qtd",
                color="_status", barmode="stack",
                color_discrete_map=STATUS_CORES,
                labels={"_status": "Status", col_nome: ""},
                title="Status por pessoa",
            )
            fig2.update_layout(margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig2, use_container_width=True, key=f"status_{equipe}_{categoria}")

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        df_ag = df_cat[df_cat["_status"] == "Aguardando retorno"] if "_status" in df_cat.columns else pd.DataFrame()
        _tabela_destaque(df_ag, "#eab308", "⏳ Aguardando retorno", f"ag_{equipe}_{categoria}")
    with col_d2:
        df_pau = df_cat_todos[df_cat_todos["_status"] == "Pausado"] if "_status" in df_cat_todos.columns else pd.DataFrame()
        _tabela_destaque(df_pau, "#9ca3af", "⏸ Pausados", f"pau_{equipe}_{categoria}")

    st.markdown("#### Por pessoa")
    if col_nome:
        for pessoa in sorted(df_cat[col_nome].unique()):
            df_p = df_cat[df_cat[col_nome] == pessoa].copy()
            status_counts = df_p["_status"].value_counts().to_dict() if "_status" in df_p.columns else {}
            badges = " ".join(
                f"<span style='background:{STATUS_CORES.get(s, '#64748b')};color:white;"
                f"border-radius:4px;padding:1px 7px;font-size:0.75rem'>{s}: {n}</span>"
                for s, n in status_counts.items()
            )
            disp = df_p[cols_pessoa].copy()
            if col_data and col_data in disp.columns:
                disp[col_data] = pd.to_datetime(
                    disp[col_data], dayfirst=True, errors="coerce"
                ).dt.strftime("%d/%m/%Y").fillna("—")
            with st.expander(f"**{pessoa}** — {len(df_p)} item(s)", expanded=False):
                st.markdown(badges, unsafe_allow_html=True)
                st.dataframe(
                    disp.reset_index(drop=True),
                    use_container_width=True, hide_index=True,
                    height=min(38 * (len(disp) + 1) + 10, 400),
                )


def _render_tab_equipe(df_eq: pd.DataFrame, equipe: str, cor: str) -> None:
    if df_eq.empty:
        st.info("Nenhum item ativo para esta equipe.")
        return

    df_proj_todos  = df_eq[df_eq["_categoria"].isin(["Projeto", "Outro"])]
    df_ajust_todos = df_eq[df_eq["_categoria"] == "Ajuste"]
    _ativos  = df_eq["_status"] != "Pausado" if "_status" in df_eq.columns else pd.Series(True, index=df_eq.index)
    df_proj  = df_proj_todos[_ativos.reindex(df_proj_todos.index, fill_value=True)]
    df_ajust = df_ajust_todos[_ativos.reindex(df_ajust_todos.index, fill_value=True)]
    df_ag    = df_eq[df_eq["_status"] == "Aguardando retorno"] if "_status" in df_eq.columns else pd.DataFrame()
    df_pau   = df_eq[df_eq["_status"] == "Pausado"]            if "_status" in df_eq.columns else pd.DataFrame()

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        st.metric("Projetos", len(df_proj))
        if st.button("ver lista", key=f"btn_proj_{equipe}", use_container_width=True):
            _modal_lista(df_proj, f"Projetos — {equipe}")

    with k2:
        st.metric("Ajustes", len(df_ajust))
        if st.button("ver lista", key=f"btn_ajust_{equipe}", use_container_width=True):
            _modal_lista(df_ajust, f"Ajustes — {equipe}")

    with k3:
        st.metric("Aguardando retorno", len(df_ag))
        if st.button("ver lista", key=f"btn_ag_{equipe}", use_container_width=True):
            _modal_lista(df_ag, f"Aguardando retorno — {equipe}")

    with k4:
        st.metric("Pausados", len(df_pau))
        if st.button("ver lista", key=f"btn_pau_{equipe}", use_container_width=True):
            _modal_lista(df_pau, f"Pausados — {equipe}")

    sub_proj, sub_ajust = st.tabs(["Projetos", "Ajustes"])

    with sub_proj:
        _render_categoria(df_proj, df_proj_todos, equipe, cor, "Projetos")

    with sub_ajust:
        _render_categoria(df_ajust, df_ajust_todos, equipe, cor, "Ajustes")


# ------------------------------------------------------------------
# Layout principal — tabs por equipe
# ------------------------------------------------------------------
tab_des, tab_prog = st.tabs(["Designers", "Programadores"])

for tab, equipe in zip([tab_des, tab_prog], ["Designers", "Programadores"]):
    with tab:
        membros = EQUIPES[equipe]
        df_eq = df_f[df_f[col_nome].isin(membros)] if col_nome else pd.DataFrame()
        _render_tab_equipe(df_eq, equipe, CORES_EQUIPE[equipe])

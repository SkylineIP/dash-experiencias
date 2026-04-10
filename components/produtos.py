import streamlit as st
import pandas as pd
import plotly.express as px

from config import EQUIPES, CORES_EQUIPE, TIPOS_TELA, TIPOS_SALA, TIPOS_PRODUTO

_CORES_PRODUTO = {
    "Tela": "#f59e0b", "Tela Slim": "#fbbf24", "Tablet": "#34d399",
    "Sala 1 Projeção": "#60a5fa", "Sala 3 Projeções": "#3b82f6",
    "Sala 4 Projeções": "#2563eb", "Sala Semicircular": "#a78bfa",
    "Sala Semicircular cor": "#7c3aed", "Sala Trapézio": "#f472b6",
    "Sala Imersiva": "#ec4899",
}


def _filtrar_produtos(df: pd.DataFrame, df_exp: pd.DataFrame, col_tipo: str) -> pd.DataFrame:
    """Retorna df_exp apenas com produtos puros (sem Ajustes junto na mesma linha)."""
    idx_com_ajustes = df[
        df[col_tipo].astype(str).str.contains("Ajustes", case=False, na=False)
    ].index
    return df_exp[
        df_exp["_tipo"].isin(TIPOS_PRODUTO) &
        ~df_exp.index.isin(idx_com_ajustes)
    ]


def _kpis(df_prod: pd.DataFrame, col_nome: str) -> None:
    total = len(df_prod)
    telas = df_prod[df_prod["_tipo"].isin(TIPOS_TELA)][col_nome].count()
    salas = df_prod[df_prod["_tipo"].isin(TIPOS_SALA)][col_nome].count()

    c1, c2, c3, _, c4, c5 = st.columns([1, 1, 1, 0.1, 1, 1])
    c1.metric("Total de produtos", total)
    c2.metric("Telas", telas)
    c3.metric("Salas", salas)

    for col_eq, equipe in zip([c4, c5], ["Designers", "Programadores"]):
        membros = EQUIPES[equipe]
        qtd = df_prod[df_prod[col_nome].isin(membros)][col_nome].count()
        cor = CORES_EQUIPE[equipe]
        col_eq.markdown(
            f"<div style='border-left:3px solid {cor}; padding-left:8px'>"
            f"<span style='font-size:0.8rem; color:#6b7280'>{equipe}</span><br>"
            f"<span style='font-size:1.6rem; font-weight:700'>{qtd}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )


def _detalhe_grupos(df_prod: pd.DataFrame, col_nome: str, col_emp: str | None, key_suffix: str) -> None:
    """Gráfico + lista de entregas para Telas e Salas."""
    col_tela, col_sala = st.columns(2)

    for col_bloco, grupo_nome, tipos_grupo in [
        (col_tela, "Telas", TIPOS_TELA),
        (col_sala, "Salas", TIPOS_SALA),
    ]:
        df_grupo = df_prod[df_prod["_tipo"].isin(tipos_grupo)]

        with col_bloco:
            st.markdown(f"**{grupo_nome}** — {len(df_grupo)} entrega(s)")

            if df_grupo.empty:
                st.info("Nenhuma entrega no período.")
                continue

            por_tipo = df_grupo["_tipo"].value_counts().reset_index()
            por_tipo.columns = ["Tipo", "Qtd"]
            fig = px.bar(
                por_tipo, x="Tipo", y="Qtd",
                text="Qtd", color="Tipo",
                color_discrete_map=_CORES_PRODUTO,
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(
                showlegend=False,
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis_title="", yaxis_title="Qtd",
            )
            st.plotly_chart(fig, use_container_width=True, key=f"prod_{grupo_nome}_{key_suffix}")

            for equipe in ["Designers", "Programadores"]:
                membros = EQUIPES[equipe]
                df_eq = df_grupo[df_grupo[col_nome].isin(membros)]
                if df_eq.empty:
                    continue

                cor = CORES_EQUIPE[equipe]
                st.markdown(
                    f"<span style='color:{cor}; font-weight:600'>{equipe}</span>",
                    unsafe_allow_html=True,
                )
                linhas = []
                for _, row in df_eq.iterrows():
                    emp = str(row[col_emp]).strip() if col_emp and col_emp in row and str(row[col_emp]) != "nan" else ""
                    nome = row[col_nome]
                    tipo = row["_tipo"]
                    mes = (
                        row["_data_envio"].strftime("%d/%m")
                        if "_data_envio" in row and pd.notna(row.get("_data_envio"))
                        else ""
                    )
                    linhas.append(f"**{tipo}** — {emp} _{nome}_ {mes}")
                st.markdown("\n".join(f"- {l}" for l in linhas))


def _grafico_mensal(df_prod: pd.DataFrame, key_suffix: str) -> None:
    if "_mes_order" not in df_prod.columns or df_prod["_mes_order"].isna().all():
        return
    df_prod = df_prod.copy()
    df_prod["_grupo"] = df_prod["_tipo"].apply(
        lambda t: "Telas" if t in TIPOS_TELA else "Salas"
    )
    mensal = (
        df_prod.dropna(subset=["_mes_order"])
        .groupby(["_mes_order", "_grupo"])
        .size()
        .reset_index(name="Qtd")
        .sort_values("_mes_order")
    )
    mensal["Mês"] = mensal["_mes_order"].apply(lambda p: p.strftime("%b/%Y"))
    fig = px.bar(
        mensal, x="Mês", y="Qtd",
        color="_grupo", barmode="group", text="Qtd",
        color_discrete_map={"Telas": "#f59e0b", "Salas": "#3b82f6"},
        labels={"_grupo": ""},
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True, key=f"prod_mensal_{key_suffix}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def render_produtos(
    df_ano: pd.DataFrame,
    df_ano_exp: pd.DataFrame,
    df_mes: pd.DataFrame,
    df_mes_exp: pd.DataFrame,
    col_nome: str,
    col_tipo: str,
    col_emp: str | None,
) -> None:
    st.markdown(
        "<h3 style='margin-bottom:2px'>Produtos entregues</h3>"
        "<p style='color:#6b7280; margin-top:0; font-size:0.85rem'>"
        "Telas e Salas — apenas entregas sem Ajustes marcado junto</p>",
        unsafe_allow_html=True,
    )

    tab_ano, tab_mes = st.tabs(["Visão Anual", "Por Mês"])

    # ------------------------------------------------------------------
    # Visão Anual
    # ------------------------------------------------------------------
    with tab_ano:
        df_prod_ano = _filtrar_produtos(df_ano, df_ano_exp, col_tipo)

        if df_prod_ano.empty:
            st.info("Nenhum produto entregue no ano.")
        else:
            _kpis(df_prod_ano, col_nome)
            st.divider()
            _grafico_mensal(df_prod_ano, key_suffix="ano")
            st.divider()
            _detalhe_grupos(df_prod_ano, col_nome, col_emp, key_suffix="ano")

    # ------------------------------------------------------------------
    # Por Mês
    # ------------------------------------------------------------------
    with tab_mes:
        meses_disponiveis = []
        if "_mes_order" in df_ano.columns:
            meses_disponiveis = (
                df_ano.dropna(subset=["_mes_order"])
                .sort_values("_mes_order")["_mes_ano"]
                .unique()
                .tolist()
            )

        if not meses_disponiveis:
            st.info("Sem dados de data para filtrar por mês.")
        else:
            mes_sel = st.selectbox(
                "Mês",
                options=meses_disponiveis,
                index=len(meses_disponiveis) - 1,   # padrão: mês mais recente
                format_func=lambda m: pd.Period(m, "M").strftime("%B/%Y"),
                key="prod_mes_sel",
            )

            df_m     = df_ano[df_ano["_mes_ano"] == mes_sel]
            df_m_exp = df_ano_exp[df_ano_exp.index.isin(df_m.index)]
            df_prod_mes = _filtrar_produtos(df_m, df_m_exp, col_tipo)

            if df_prod_mes.empty:
                st.info("Nenhum produto entregue neste mês.")
            else:
                _kpis(df_prod_mes, col_nome)
                st.divider()
                _detalhe_grupos(df_prod_mes, col_nome, col_emp, key_suffix="mes")

    st.divider()

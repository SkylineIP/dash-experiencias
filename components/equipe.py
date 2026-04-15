import streamlit as st
import pandas as pd
import plotly.express as px

from config import CORES_TIPO


def render_equipe(
    df_equipe: pd.DataFrame,
    df_equipe_exp: pd.DataFrame,
    col_nome: str,
    titulo: str,
    cor: str,
) -> None:
    st.markdown(
        f"<h3 style='color:{cor}; margin-bottom:4px'>{titulo}</h3>",
        unsafe_allow_html=True,
    )

    if df_equipe.empty:
        st.info("Sem dados para esta equipe no período selecionado.")
        return

    # KPIs
    k1, k2, k3 = st.columns(3)
    k1.metric("Entregas", len(df_equipe))
    k2.metric("Membros ativos", df_equipe[col_nome].nunique())
    tipo_top = df_equipe_exp["_tipo"].value_counts().idxmax() if not df_equipe_exp.empty else "—"
    k3.metric("Tipo mais feito", tipo_top)

    col_a, col_b = st.columns(2)

    with col_a:
        por_pessoa = df_equipe[col_nome].value_counts().reset_index()
        por_pessoa.columns = ["Pessoa", "Entregas"]
        fig = px.bar(
            por_pessoa, x="Entregas", y="Pessoa",
            orientation="h", text="Entregas",
            color_discrete_sequence=[cor],
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            yaxis={"categoryorder": "total ascending"},
            margin=dict(l=0, r=20, t=10, b=0),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True, key=f"bar_pessoa_{titulo}")

    with col_b:
        if not df_equipe_exp.empty:
            por_tipo = df_equipe_exp["_tipo"].value_counts().reset_index()
            por_tipo.columns = ["Tipo", "Qtd"]
            fig2 = px.pie(
                por_tipo, names="Tipo", values="Qtd",
                hole=0.4, color="Tipo", color_discrete_map=CORES_TIPO,
            )
            fig2.update_traces(textposition="inside", textinfo="percent+label")
            fig2.update_layout(showlegend=False, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig2, use_container_width=True, key=f"pie_tipo_{titulo}")

    # Linha mensal por pessoa
    if "_mes_order" in df_equipe.columns and df_equipe["_mes_order"].notna().any():
        mensal = (
            df_equipe.dropna(subset=["_mes_order"])
            .groupby(["_mes_order", col_nome])
            .size()
            .reset_index(name="Entregas")
            .sort_values("_mes_order")
        )
        mensal["Mês"] = mensal["_mes_order"].apply(lambda p: p.strftime("%b/%Y"))
        fig4 = px.line(
            mensal, x="Mês", y="Entregas",
            color=col_nome, markers=True,
            labels={col_nome: ""},
            title="Entregas por mês",
        )
        fig4.update_layout(margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig4, use_container_width=True, key=f"linha_{titulo}")

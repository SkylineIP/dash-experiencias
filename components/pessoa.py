import streamlit as st
import pandas as pd
import plotly.express as px

from config import CORES_EQUIPE, CORES_TIPO
from data.processing import equipe_de


def render_pessoa(
    df_f: pd.DataFrame,
    df_exp: pd.DataFrame,
    col_nome: str,
    cols_completas: list[str],
    col_envio: str | None,
) -> None:
    st.subheader("Detalhe por pessoa")

    todas_pessoas = sorted(df_f[col_nome].unique().tolist())
    pessoa_sel = st.selectbox("Pessoa", todas_pessoas)

    df_p     = df_f[df_f[col_nome] == pessoa_sel]
    df_p_exp = df_exp[df_exp[col_nome] == pessoa_sel]
    equipe_p = equipe_de(pessoa_sel)
    cor_p    = CORES_EQUIPE.get(equipe_p, "#64748b")

    st.markdown(
        f"**Equipe:** <span style='color:{cor_p}'>{equipe_p}</span>",
        unsafe_allow_html=True,
    )

    p1, p2, p3 = st.columns(3)
    p1.metric("Entregas", len(df_p))
    p2.metric(
        "Meses com entrega",
        df_p["_mes_ano"].nunique() if "_mes_ano" in df_p.columns else "—",
    )
    tipo_p = df_p_exp["_tipo"].value_counts().idxmax() if not df_p_exp.empty else "—"
    p3.metric("Tipo mais feito", tipo_p)

    pd1, pd2 = st.columns(2)

    with pd1:
        if not df_p_exp.empty:
            tp = df_p_exp["_tipo"].value_counts().reset_index()
            tp.columns = ["Tipo", "Qtd"]
            fig_pie = px.pie(
                tp, names="Tipo", values="Qtd",
                hole=0.4, color="Tipo", color_discrete_map=CORES_TIPO,
                title="Distribuição de tipos",
            )
            fig_pie.update_traces(textposition="inside", textinfo="percent+label")
            fig_pie.update_layout(showlegend=False, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig_pie, use_container_width=True)

    with pd2:
        if "_mes_order" in df_p.columns and df_p["_mes_order"].notna().any():
            mp = (
                df_p.dropna(subset=["_mes_order"])
                .groupby("_mes_order")
                .size()
                .reset_index(name="Entregas")
                .sort_values("_mes_order")
            )
            mp["Mês"] = mp["_mes_order"].apply(lambda p: p.strftime("%b/%Y"))
            fig_bar = px.bar(
                mp, x="Mês", y="Entregas", text="Entregas",
                title="Entregas por mês",
                color_discrete_sequence=[cor_p],
            )
            fig_bar.update_traces(textposition="outside")
            fig_bar.update_layout(margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("#### Todos os registros")
    df_p_display = df_p[cols_completas].copy()
    if col_envio and col_envio in df_p_display.columns:
        df_p_display[col_envio] = pd.to_datetime(
            df_p_display[col_envio], dayfirst=True, errors="coerce"
        ).dt.strftime("%d/%m/%Y %H:%M")
    st.dataframe(
        df_p_display.reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
        height=400,
    )

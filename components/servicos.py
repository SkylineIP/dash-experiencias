import streamlit as st
import pandas as pd
import plotly.express as px

from config import EQUIPES, CORES_EQUIPE, CORES_TIPO


def render_servicos(
    df_f: pd.DataFrame,
    df_exp: pd.DataFrame,
    col_nome: str,
    cols_completas: list[str],
    col_envio: str | None,
) -> None:
    st.subheader("Serviços — visão completa por equipe")

    sub_design, sub_prog = st.tabs(["Designers", "Programadores"])

    for sub_aba, equipe in zip([sub_design, sub_prog], ["Designers", "Programadores"]):
        cor     = CORES_EQUIPE[equipe]
        membros = EQUIPES[equipe]
        df_eq     = df_f[df_f[col_nome].isin(membros)]
        df_eq_exp = df_exp[df_exp[col_nome].isin(membros)]

        with sub_aba:
            if df_eq.empty:
                st.info("Sem dados para esta equipe no período selecionado.")
                continue

            total_eq = len(df_eq)

            resumo = df_eq_exp["_tipo"].value_counts().reset_index()
            resumo.columns = ["Tipo de serviço", "Qtd"]
            resumo["% do total"] = (resumo["Qtd"] / total_eq * 100).round(1).astype(str) + "%"
            resumo = resumo.sort_values("Qtd", ascending=False)

            col_r1, col_r2 = st.columns(2)

            with col_r1:
                st.markdown(f"**Total de entregas: {total_eq}**")
                st.dataframe(
                    resumo,
                    use_container_width=True,
                    hide_index=True,
                    height=min(38 * (len(resumo) + 1) + 10, 400),
                )

            with col_r2:
                fig = px.bar(
                    resumo, x="Qtd", y="Tipo de serviço",
                    orientation="h", text="Qtd",
                    color="Tipo de serviço",
                    color_discrete_map=CORES_TIPO,
                )
                fig.update_traces(textposition="outside")
                fig.update_layout(
                    showlegend=False,
                    yaxis={"categoryorder": "total ascending"},
                    margin=dict(l=0, r=20, t=10, b=0),
                )
                st.plotly_chart(fig, use_container_width=True, key=f"serv_bar_{equipe}")

            st.divider()
            st.markdown("#### Registros por tipo de serviço")

            for tipo in resumo["Tipo de serviço"].tolist():
                idx_tipo = df_eq_exp[df_eq_exp["_tipo"] == tipo].index
                df_registros = df_eq.loc[df_eq.index.isin(idx_tipo), cols_completas].copy()

                if col_envio and col_envio in df_registros.columns:
                    df_registros[col_envio] = pd.to_datetime(
                        df_registros[col_envio], dayfirst=True, errors="coerce"
                    ).dt.strftime("%d/%m/%Y %H:%M")

                qtd = len(df_registros)
                label = f"**{tipo}** — {qtd} {'entrega' if qtd == 1 else 'entregas'}"
                with st.expander(label):
                    st.dataframe(
                        df_registros.reset_index(drop=True),
                        use_container_width=True,
                        hide_index=True,
                        height=min(38 * (qtd + 1) + 10, 500),
                    )

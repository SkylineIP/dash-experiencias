import requests
import pandas as pd
import streamlit as st
from io import StringIO

from config import ANO_ATUAL, OCULTAR
from data.processing import detect_col, nome_canonico, equipe_de, deve_ocultar


@st.cache_data(ttl=300)
def load_data(sheet_url: str) -> pd.DataFrame:
    """Aceita qualquer formato de URL do Google Sheets e retorna um DataFrame."""
    url = sheet_url.strip()
    if "spreadsheets/d/" in url:
        sheet_id = url.split("spreadsheets/d/")[1].split("/")[0]
        gid = "0"
        if "gid=" in url:
            gid = url.split("gid=")[1].split("&")[0].split("#")[0]
        csv_url = (
            f"https://docs.google.com/spreadsheets/d/{sheet_id}"
            f"/export?format=csv&gid={gid}"
        )
    else:
        csv_url = url

    response = requests.get(csv_url, timeout=15)
    response.raise_for_status()
    return pd.read_csv(StringIO(response.content.decode("utf-8")))


def prepare_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Parseia datas, normaliza nomes e adiciona colunas internas (_prefixo)."""
    df = df_raw.copy()
    df.columns = df.columns.str.strip()

    # Datas
    col_data = detect_col(df, ["data de envio", "data envio", "envio"])
    if col_data:
        df["_data_envio"] = pd.to_datetime(df[col_data], dayfirst=True, errors="coerce")
        df["_mes_ano"]    = df["_data_envio"].dt.to_period("M").astype(str)
        df["_mes_order"]  = df["_data_envio"].dt.to_period("M")
        df["_ano"]        = df["_data_envio"].dt.year

    # Nomes
    col_nome = detect_col(df, ["nome"])
    if col_nome:
        df[col_nome] = df[col_nome].astype(str).str.strip()
        df = df[df[col_nome].notna() & (df[col_nome] != "") & (df[col_nome] != "nan")]
        df[col_nome] = df[col_nome].apply(nome_canonico)
        df = df[~df[col_nome].apply(deve_ocultar)]

    # Filtro de ano
    if "_ano" in df.columns:
        df = df[df["_ano"] == ANO_ATUAL]

    # Equipe
    if col_nome:
        df["_equipe"] = df[col_nome].apply(equipe_de)

    return df

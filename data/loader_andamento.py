"""
Parser para a planilha de projetos em andamento.

A planilha tem múltiplas tabelas lado a lado, uma por pessoa:
  | Bia Leão | ... | ... | ... | Millena | ... | ... | ... |
  | Tarefa   | Data| Obs | Tipo| Tarefa  | Data| Obs | Tipo|
  | FFI...   | ... | ... | ... | Urba... | ... | ... | ... |

Este módulo lê essa estrutura e retorna um DataFrame flat:
  Nome | Tarefa | Data | Obs | Tipo de serviço
"""
import requests
import pandas as pd
import streamlit as st
from io import StringIO

from config import EQUIPES
from data.processing import normalizar, nome_canonico, equipe_de, deve_ocultar

STATUS_TIPOS = {"em andamento", "aguardando retorno", "pausado"}
_COL_CANDIDATOS_TAREFA = {"tarefa", "projeto", "task"}
_COL_CANDIDATOS_DATA   = {"data", "prazo", "date"}
_COL_CANDIDATOS_OBS    = {"obs", "observ", "descri", "nota"}
_COL_CANDIDATOS_TIPO   = {"tipo", "servico", "serviço"}


@st.cache_data(ttl=300)
def _fetch_raw(url: str) -> pd.DataFrame:
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
    r = requests.get(csv_url, timeout=15)
    r.raise_for_status()
    return pd.read_csv(StringIO(r.content.decode("utf-8")), header=None, dtype=str)


def _matches(cell: str, candidates: set) -> bool:
    n = normalizar(cell)
    return any(c in n for c in candidates)


def load_andamento(url: str) -> pd.DataFrame:
    """
    Carrega e parseia a planilha de andamento com múltiplas tabelas lado a lado.
    Retorna um DataFrame flat com colunas: Nome, Tarefa, Data, Obs, Tipo de serviço.
    """
    todos_membros = {
        normalizar(m): m
        for membros in EQUIPES.values()
        for m in membros
    }

    df_raw = _fetch_raw(url)
    n_rows, n_cols = df_raw.shape

    # ------------------------------------------------------------------
    # 1. Encontrar linha e coluna onde cada pessoa começa
    # ------------------------------------------------------------------
    person_col: dict[int, str] = {}   # col_idx -> nome canônico
    person_row: int | None = None

    for row_idx in range(min(8, n_rows)):
        found_in_row = {}
        for col_idx in range(n_cols):
            cell = str(df_raw.iloc[row_idx, col_idx]).strip()
            cell_norm = normalizar(cell)
            if cell_norm in todos_membros:
                found_in_row[col_idx] = todos_membros[cell_norm]
        if found_in_row:
            person_col = found_in_row
            person_row = row_idx
            break

    if not person_col:
        # Fallback: planilha já está no formato flat com coluna Nome
        df_flat = pd.read_csv(
            StringIO(requests.get(
                _csv_url(url), timeout=15
            ).content.decode("utf-8"))
        )
        return _pos_processar(df_flat)

    # ------------------------------------------------------------------
    # 2. Encontrar a linha de cabeçalhos (logo abaixo do nome da pessoa)
    # ------------------------------------------------------------------
    header_row: int | None = None
    for row_idx in range(person_row + 1, min(person_row + 4, n_rows)):
        row_vals = [str(df_raw.iloc[row_idx, c]) for c in range(n_cols)]
        if any(_matches(v, _COL_CANDIDATOS_TAREFA) for v in row_vals):
            header_row = row_idx
            break
    if header_row is None:
        header_row = person_row + 1

    # ------------------------------------------------------------------
    # 3. Para cada pessoa, extrair o bloco de dados
    # ------------------------------------------------------------------
    sorted_starts = sorted(person_col.keys())
    all_dfs: list[pd.DataFrame] = []

    for i, start_col in enumerate(sorted_starts):
        end_col = sorted_starts[i + 1] if i + 1 < len(sorted_starts) else n_cols
        nome = person_col[start_col]

        # Cabeçalhos deste bloco
        raw_headers = [
            str(df_raw.iloc[header_row, c]).strip()
            for c in range(start_col, end_col)
        ]

        # Normalizar nomes de colunas para os padrões esperados
        mapped: list[str] = []
        for h in raw_headers:
            if _matches(h, _COL_CANDIDATOS_TAREFA):
                mapped.append("Tarefa")
            elif _matches(h, _COL_CANDIDATOS_DATA):
                mapped.append("Data")
            elif _matches(h, _COL_CANDIDATOS_OBS):
                mapped.append("Obs")
            elif _matches(h, _COL_CANDIDATOS_TIPO):
                mapped.append("Tipo de serviço")
            else:
                mapped.append(h or f"col_{len(mapped)}")

        # Eliminar duplicatas de nome de coluna
        seen: dict[str, int] = {}
        dedup: list[str] = []
        for m in mapped:
            if m in seen:
                seen[m] += 1
                dedup.append(f"{m}_{seen[m]}")
            else:
                seen[m] = 0
                dedup.append(m)

        # Dados (linhas após cabeçalho)
        data_rows = df_raw.iloc[header_row + 1:, start_col:end_col].copy()
        data_rows.columns = dedup[:len(data_rows.columns)]

        # Remover linhas totalmente vazias ou sem tarefa
        _VAZIOS = {"nan", "none", "n/a", "-", ""}
        data_rows = data_rows.replace("nan", pd.NA).replace("None", pd.NA)
        if "Tarefa" in data_rows.columns:
            data_rows = data_rows[
                data_rows["Tarefa"].notna() &
                (~data_rows["Tarefa"].astype(str).str.strip().str.lower().isin(_VAZIOS))
            ]
        else:
            data_rows = data_rows.dropna(how="all")
        if data_rows.empty:
            continue

        data_rows.insert(0, "Nome", nome)
        all_dfs.append(data_rows)

    if not all_dfs:
        return pd.DataFrame()

    df = pd.concat(all_dfs, ignore_index=True)
    return _pos_processar(df)


def _csv_url(url: str) -> str:
    if "spreadsheets/d/" in url:
        sheet_id = url.split("spreadsheets/d/")[1].split("/")[0]
        gid = "0"
        if "gid=" in url:
            gid = url.split("gid=")[1].split("&")[0].split("#")[0]
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    return url


def _pos_processar(df: pd.DataFrame) -> pd.DataFrame:
    """Pós-processa o DataFrame flat: equipe, data, status."""
    _VAZIOS = {"nan", "none", "n/a", "-", ""}

    col_nome   = next((c for c in df.columns if normalizar(c) == "nome"), None)
    col_tarefa = next((c for c in df.columns if normalizar(c) == "tarefa"), None)
    col_tipo   = next((c for c in df.columns if "tipo" in normalizar(c)), None)
    col_data   = next((c for c in df.columns if normalizar(c) in ("data", "prazo")), None)

    # Garantir que só ficam linhas com tarefa real
    if col_tarefa:
        df = df[
            df[col_tarefa].notna() &
            (~df[col_tarefa].astype(str).str.strip().str.lower().isin(_VAZIOS))
        ]

    if col_nome:
        df[col_nome] = df[col_nome].astype(str).str.strip()
        df = df[df[col_nome].notna() & (df[col_nome] != "") & (df[col_nome] != "nan")]
        df[col_nome] = df[col_nome].apply(nome_canonico)
        df = df[~df[col_nome].apply(deve_ocultar)]
        df["_equipe"] = df[col_nome].apply(equipe_de)

    if col_data:
        df["_prazo_dt"] = pd.to_datetime(df[col_data], dayfirst=True, errors="coerce")
        hoje = pd.Timestamp.today().normalize()
        df["_dias_restantes"] = (df["_prazo_dt"] - hoje).dt.days

    if col_tipo:
        # Extrai status do campo tipo de serviço
        def extrair_status(val: str) -> str:
            partes = [p.strip() for p in str(val).split(",")]
            for p in partes:
                if normalizar(p) in STATUS_TIPOS:
                    return p
            return "Em andamento"   # padrão se não especificado

        def extrair_tipo_puro(val: str) -> str:
            partes = [p.strip() for p in str(val).split(",")]
            tipos = [p for p in partes if normalizar(p) not in STATUS_TIPOS and p not in ("nan", "")]
            return ", ".join(tipos) if tipos else ""

        df["_status"]     = df[col_tipo].apply(extrair_status)
        df["_tipo_puro"]  = df[col_tipo].apply(extrair_tipo_puro)

    return df

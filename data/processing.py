import unicodedata
import pandas as pd

from config import EQUIPES, OCULTAR


def normalizar(texto: str) -> str:
    """Remove acentos e coloca em minúsculas para comparação."""
    return unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode().lower().strip()


# Lookup accent/case-insensitive: {nome_normalizado: nome_canônico}
MEMBROS_NORM: dict[str, dict[str, str]] = {
    equipe: {normalizar(m): m for m in membros}
    for equipe, membros in EQUIPES.items()
}

_OCULTAR_NORM = {normalizar(o) for o in OCULTAR}


def detect_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Encontra a primeira coluna cujo nome contenha algum dos candidatos (sem acento/caixa)."""
    for col in df.columns:
        col_norm = normalizar(col)
        for c in candidates:
            if normalizar(c) in col_norm:
                return col
    return None


def equipe_de(nome: str) -> str:
    n = normalizar(nome)
    for equipe, membros_norm in MEMBROS_NORM.items():
        if n in membros_norm:
            return equipe
    return "Outros"


def nome_canonico(nome: str) -> str:
    """Mapeia um nome da planilha para o padrão definido em EQUIPES."""
    n = normalizar(nome)
    for membros_norm in MEMBROS_NORM.values():
        if n in membros_norm:
            return membros_norm[n]
    return nome


def deve_ocultar(nome: str) -> bool:
    return normalizar(nome) in _OCULTAR_NORM


def explode_tipos(df: pd.DataFrame, tipo_col: str) -> pd.DataFrame:
    """Expande linhas onde 'Tipo de serviço' tem múltiplos valores (vírgula/ponto-e-vírgula/quebra)."""
    df = df.copy()
    df["_tipos_list"] = df[tipo_col].astype(str).str.split(r"[,;\n]+")
    df = df.explode("_tipos_list")
    df["_tipo"] = df["_tipos_list"].str.strip()
    df = df[df["_tipo"].str.len() > 0]
    df = df[df["_tipo"] != "nan"]
    return df


def mes_label(period_str: str) -> str:
    return pd.Period(period_str, "M").strftime("%b/%Y")

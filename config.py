ANO_ATUAL = 2026

# URLs e senha lidas dos secrets (local: .streamlit/secrets.toml | produção: Streamlit Cloud)
import streamlit as _st
URL_ENTREGUES: str = _st.secrets["URL_ENTREGUES"]
URL_ANDAMENTO: str = _st.secrets["URL_ANDAMENTO"]
SENHA: str         = _st.secrets["SENHA"]

DESIGNERS     = ["Bia Leão", "Gustavo", "Jack", "Millena"]
PROGRAMADORES = ["Fernando", "Kaleb", "Bia Fernandes", "Leonardo"]
OCULTAR       = ["Matheus"]

EQUIPES: dict[str, list[str]] = {
    "Designers":     DESIGNERS,
    "Programadores": PROGRAMADORES,
}

CORES_EQUIPE: dict[str, str] = {
    "Designers":     "#6366f1",
    "Programadores": "#10b981",
}

# Tipos considerados "produto" (excluem ajustes quando marcados juntos)
TIPOS_TELA: list[str] = ["Tela", "Tela Slim", "Tablet"]
TIPOS_SALA: list[str] = [
    "Sala 1 Projeção", "Sala 3 Projeções", "Sala 4 Projeções",
    "Sala Semicircular", "Sala Semicircular cor", "Sala Trapézio", "Sala Imersiva",
]
TIPOS_PRODUTO: list[str] = TIPOS_TELA + TIPOS_SALA

# Sistema de prioridade por prazo (dias restantes → cor)
PRIORIDADES_PRAZO: list[tuple] = [
    # (dias_max, label, cor)
    (0,  "No dia ou atrasado", "#ef4444"),   # vermelho
    (2,  "2 dias",             "#f97316"),   # laranja
    (5,  "5 dias",             "#eab308"),   # amarelo
    (10, "10 dias",            "#06b6d4"),   # ciano
    (15, "15 dias",            "#3b82f6"),   # azul
    (999,"30 dias +",          "#22c55e"),   # verde
]

CORES_TIPO: dict[str, str] = {
    "Tela":                 "#f59e0b",
    "Tela Slim":            "#fbbf24",
    "Tablet":               "#34d399",
    "Sala 1 Projeção":      "#60a5fa",
    "Sala 3 Projeções":     "#3b82f6",
    "Sala 4 Projeções":     "#2563eb",
    "Sala Semicircular":    "#a78bfa",
    "Sala Semicircular cor":"#7c3aed",
    "Sala Trapézio":        "#f472b6",
    "Sala Imersiva":        "#ec4899",
    "Ajustes":              "#374151",
    "Interno":              "#6b7280",
    "Sistemas":             "#10b981",
    "Novo produto":         "#ef4444",
    "Em andamento":         "#f97316",
    "Aguardando retorno":   "#eab308",
    "Pausado":              "#9ca3af",
}

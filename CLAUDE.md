# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the app

```bash
python -m streamlit run app.py
```

Streamlit is not on PATH on Windows — always use `python -m streamlit`.

## Business context

Dashboard interno que lê uma planilha pública do Google Sheets com o fluxo de projetos. Quando alguém finaliza um projeto, marca como "finalizado" na planilha — o registro aparece aqui.

**Equipes:**
- Designers: Bia Leão, Gustavo, Jack, Millena
- Programadores: Fernando, Kaleb, Bia Fernandes, Leonardo
- Oculto (saiu da empresa): Matheus

Métricas são sempre separadas por equipe — nunca misturar os dois times num número agregado. O comparativo entre equipes existe no dashboard mas não deve ser enfatizado (pode gerar atrito).

**Campos da planilha:** Nome | Emprendimento e Incorporadora | Prazo | Outros | Tipo de serviço | Data de envio

**Tipos de serviço:** Tela, Tela Slim, Tablet, Sala 1 Projeção, Sala 3 Projeções, Sala 4 Projeções, Sala Semicircular, Sala Semicircular cor, Sala Trapézio, Sala Imersiva, Ajustes, Interno, Sistemas, Novo produto, Em andamento, Aguardando retorno, Pausado

## Project structure

```
dashboard/
├── app.py                  # Entry point: sidebar, filtros, KPIs, layout das abas
├── config.py               # Todas as constantes — editar aqui para mudar membros, cores, ano
├── data/
│   ├── loader.py           # load_data() (cache 5min), prepare_data()
│   └── processing.py       # normalizar, detect_col, explode_tipos, equipe_de, nome_canonico
└── components/
    ├── equipe.py           # render_equipe() — KPIs + barra + pizza + heatmap + linha mensal
    ├── servicos.py         # render_servicos() — aba Serviços com expanders por tipo
    └── pessoa.py           # render_pessoa() — aba Detalhe por pessoa
```

**Tab layout:** Designers | Programadores | Serviços | Detalhe por pessoa | Tabela

## Key concepts

**Para adicionar membro ou mudar cor:** editar só `config.py`, sem tocar em lógica.

**Matching de nomes (`data/processing.py`):**
`normalizar()` remove acentos e lowercasa. Usada em `detect_col()` (busca de colunas) e `nome_canonico()` (mapeia nomes da planilha para o padrão de `EQUIPES`). Ambos os lados de toda comparação passam por `normalizar()` — isso resolve variações como "Bia Leao" vs "Bia Leão".

**Data flow:**
1. `load_data()` — converte qualquer formato de URL do Sheets para CSV export e busca
2. `prepare_data()` — parseia datas → `_data_envio`, `_mes_ano`, `_mes_order`, `_ano`; normaliza nomes; filtra `OCULTAR` e `ANO_ATUAL`; adiciona `_equipe`
3. `explode_tipos()` — expande linhas onde "Tipo de serviço" tem múltiplos valores (vírgula/ponto-e-vírgula); adiciona coluna `_tipo`
4. Colunas internas sempre prefixadas com `_` para distinguir das colunas brutas da planilha

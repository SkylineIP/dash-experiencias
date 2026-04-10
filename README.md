# Dashboard de Projetos

Dashboard interno para acompanhamento do fluxo de projetos da equipe, dividido em duas visões: **projetos entregues** e **projetos em andamento**. Os dados são lidos diretamente do Google Sheets.

## Páginas

### ✅ Projetos Entregues
Alimentado pela planilha de histórico — projetos que foram finalizados e marcados como concluídos.

- **Produtos entregues** (destaque principal): contagem de Telas e Salas entregues no ano, com visão anual e por mês. Exclui automaticamente entregas que tenham "Ajustes" marcado junto.
- **Resumo geral** do ano: total de entregas, pessoas ativas, tipo mais frequente, mês mais movimentado.
- **Abas por equipe** (Designers / Programadores): KPIs, gráfico por pessoa, pizza de tipos, heatmap pessoa × tipo e evolução mensal.
- **Aba Serviços**: contagem e listagem completa de cada entrega agrupada por tipo de serviço.
- **Detalhe por pessoa**: distribuição de tipos e evolução mensal individual.

### 🔄 Projetos em Andamento
Alimentado pela planilha de andamento — cada membro da equipe tem sua própria tabela, o parser unifica tudo automaticamente.

- **KPIs da esteira**: total de projetos, em produção, aguardando retorno, pausados e no prazo/atrasados.
- **Destaques**: tabelas separadas de projetos "Aguardando retorno" e "Pausados".
- **Por equipe** (Designers / Programadores): projetos por pessoa e breakdown de status.
- **Sistema de prioridade de prazo** por cores (conforme legenda da sidebar).

## Equipes

| Designers | Programadores |
|-----------|---------------|
| Bia Leão  | Fernando      |
| Gustavo   | Kaleb         |
| Jack      | Bia Fernandes |
| Millena   | Leonardo      |

## Tipos de serviço

**Produtos** (Telas e Salas): Tela · Tela Slim · Tablet · Sala 1 Projeção · Sala 3 Projeções · Sala 4 Projeções · Sala Semicircular · Sala Semicircular cor · Sala Trapézio · Sala Imersiva

**Outros serviços**: Ajustes · Interno · Sistemas · Novo produto

**Status (em andamento)**: Em andamento · Aguardando retorno · Pausado

## Tecnologias

- [Streamlit](https://streamlit.io) — interface e navegação entre páginas
- [Pandas](https://pandas.pydata.org) — manipulação de dados
- [Plotly](https://plotly.com/python/) — gráficos interativos
- Google Sheets (CSV export) — fonte de dados

## Como rodar localmente

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

> `streamlit` pode não estar no PATH do Windows — use sempre `python -m streamlit`.

## Estrutura do projeto

```
dashboard/
├── app.py                   # Roteador de páginas (st.navigation)
├── config.py                # Constantes: equipes, cores, URLs das planilhas, prioridades
├── data/
│   ├── loader.py            # Carregamento e preparação da planilha de entregues
│   ├── loader_andamento.py  # Parser da planilha multi-pessoa de andamento
│   └── processing.py        # Funções auxiliares: normalizar, detect_col, explode_tipos
└── components/
    ├── equipe.py            # Seção de uma equipe (KPIs + gráficos)
    ├── produtos.py          # Indicador de produtos entregues
    ├── servicos.py          # Aba Serviços com expanders por tipo
    └── pessoa.py            # Detalhe por pessoa
```

## Deploy

O projeto está hospedado no [Streamlit Community Cloud](https://share.streamlit.io). A cada `git push` para o branch principal o deploy é atualizado automaticamente.

Para atualizar as planilhas de origem, edite as constantes `URL_ENTREGUES` e `URL_ANDAMENTO` em `config.py`. As planilhas precisam estar com acesso público ("qualquer pessoa com o link pode ver").

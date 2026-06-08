# app/pages/01_scorecards.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from components.utils import inject_css, edn_header, load_data, risk_badge, RISK_ORDER
from components.kpi_card import render_kpi_card
from components.charts import chart_risk_distribution, chart_score_by_dimension

st.set_page_config(page_title="Scorecards | ESG Dashboard", page_icon="🔴",
                   layout="wide", initial_sidebar_state="expanded")
inject_css()
edn_header("Scorecards & KPIs", "Principais indicadores · Ranking · Benchmarking")

df = load_data()

with st.sidebar:
    st.markdown("### Filtros")
    setores = ["Todos"] + sorted(df["setor"].dropna().unique().tolist())
    setor_sel    = st.selectbox("Setor", setores)
    exchange_sel = st.multiselect("Bolsa", df["bolsa"].unique().tolist(),
                                  default=df["bolsa"].unique().tolist())
    risco_sel    = st.multiselect("Nível de risco", RISK_ORDER, default=RISK_ORDER)

dff = df.copy()
if setor_sel != "Todos":
    dff = dff[dff["setor"] == setor_sel]
if exchange_sel:
    dff = dff[dff["bolsa"].isin(exchange_sel)]
if risco_sel:
    dff = dff[dff["nivel_risco"].isin(risco_sel)]

pct_baixo   = (dff["nivel_risco"] == "Baixo Risco").mean() * 100
pct_alto    = (dff["nivel_risco"] == "Alto Risco").mean()  * 100
score_medio = dff["pontuacao_total"].mean()
n_criticos  = (dff["nivel_risco"] == "Alto Risco").sum()

st.markdown('<div class="edn-section"><p class="edn-section-title">Principais indicadores</p>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1:
    render_kpi_card("Fornecedores Baixo Risco", f"{pct_baixo:.1f}%",
                    "ESG efetivamente implementado",
                    "up" if pct_baixo > 20 else "down")
with c2:
    render_kpi_card("Pontuação média ESG", f"{score_medio:.0f}",
                    "de 600 a 1536 pontos", "neu")
with c3:
    render_kpi_card("Riscos críticos identificados", str(int(n_criticos)),
                    f"{pct_alto:.1f}% do total",
                    "down" if pct_alto > 30 else "neu")
with c4:
    render_kpi_card("Empresas avaliadas", str(len(dff)),
                    f"De {len(df)} no total", "neu")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="edn-section"><p class="edn-section-title">Visão analítica</p>', unsafe_allow_html=True)
col_a, col_b = st.columns([1, 2])
with col_a:
    st.plotly_chart(chart_risk_distribution(dff), use_container_width=True)
with col_b:
    st.plotly_chart(chart_score_by_dimension(dff), use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="edn-section"><p class="edn-section-title">Ranking de fornecedores — líderes e retardatários</p>', unsafe_allow_html=True)

col_b1, col_b2 = st.columns(2)

COLS_BENCH = ["nome", "setor", "pontuacao_total", "pontuacao_ambiental",
              "pontuacao_social", "pontuacao_governanca", "nivel_risco"]
top5 = dff.nlargest(5, "pontuacao_total")[COLS_BENCH]
bot5 = dff.nsmallest(5, "pontuacao_total")[COLS_BENCH]

with col_b1:
    st.markdown("**Líderes ESG (top 5)**")
    st.dataframe(top5.reset_index(drop=True), use_container_width=True, hide_index=True)
with col_b2:
    st.markdown("**Retardatários ESG (bottom 5)**")
    st.dataframe(bot5.reset_index(drop=True), use_container_width=True, hide_index=True)

st.markdown('<div class="edn-section"><p class="edn-section-title">Benchmarking — líderes e retardatários</p>', unsafe_allow_html=True)

st.markdown("**Padrões identificados:**")
media_lid = top5[["pontuacao_ambiental", "pontuacao_social", "pontuacao_governanca"]].mean()
media_ret = bot5[["pontuacao_ambiental", "pontuacao_social", "pontuacao_governanca"]].mean()
diff      = media_lid - media_ret

col_i1, col_i2, col_i3 = st.columns(3)
for col, dim, chave in zip(
    [col_i1, col_i2, col_i3],
    ["Ambiental", "Social", "Governança"],
    ["pontuacao_ambiental", "pontuacao_social", "pontuacao_governanca"],
):
    with col:
        st.metric(f"Diferença {dim}", f"+{diff[chave]:.0f} pts", "líderes vs retardatários")

st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="edn-section"><p class="edn-section-title">Ranking Geral — Lista consolidada</p>', unsafe_allow_html=True)

col_r1, col_r2 = st.columns([2, 1])
with col_r1:
    dim_rank = st.selectbox(
        "Ordenar por",
        ["pontuacao_total", "pontuacao_ambiental", "pontuacao_social", "pontuacao_governanca"],
        format_func=lambda x: {
            "pontuacao_total":      "Pontuação total",
            "pontuacao_ambiental":  "Pontuação ambiental",
            "pontuacao_social":     "Pontuação social",
            "pontuacao_governanca": "Pontuação governança",
        }[x],
    )
with col_r2:
    ordem = st.radio("Ordem", ["Maior primeiro", "Menor primeiro"], horizontal=True)

asc = ordem == "Menor primeiro"
ranking = (
    dff[["nome", "setor", "pontuacao_total", "pontuacao_ambiental",
         "pontuacao_social", "pontuacao_governanca", "nivel_risco"]]
    .sort_values(dim_rank, ascending=asc)
    .reset_index(drop=True)
)
ranking.index += 1
ranking.index.name = "ranking"

st.dataframe(
    ranking,
    use_container_width=True,
    height=425,          # exibe ~25 linhas com scroll automático acima disso
    column_config={
        "nome":                st.column_config.TextColumn("Nome"),
        "setor":               st.column_config.TextColumn("Setor"),
        "nivel_risco":         st.column_config.TextColumn("Nível de risco"),
        "pontuacao_total":     st.column_config.NumberColumn("Pontuação total",     format="%d"),
        "pontuacao_ambiental": st.column_config.NumberColumn("Pontuação ambiental", format="%d"),
        "pontuacao_social":    st.column_config.NumberColumn("Pontuação social",     format="%d"),
        "pontuacao_governanca":st.column_config.NumberColumn("Pontuação governança", format="%d"),
    },
)
st.markdown('</div>', unsafe_allow_html=True)
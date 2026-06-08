# app/pages/02_matriz.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from components.utils import inject_css, edn_header, load_data, RISK_ORDER
from components.charts import chart_criticality_matrix

st.set_page_config(page_title="Matriz de Criticidade | ESG Dashboard", page_icon="🔴",
                   layout="wide", initial_sidebar_state="expanded")
inject_css()
edn_header("Matriz de Criticidade", "Classificação por impacto × probabilidade de não-conformidade")

df = load_data()

with st.sidebar:
    st.markdown("### Filtros")
    setores = ["Todos"] + sorted(df["setor"].dropna().unique().tolist())
    setor_sel    = st.selectbox("Setor", setores)
    risco_sel    = st.multiselect("Nível de risco", RISK_ORDER, default=RISK_ORDER)
    exchange_sel = st.multiselect("Bolsa", df["bolsa"].unique().tolist(),
                                  default=df["bolsa"].unique().tolist())

dff = df.copy()
if setor_sel != "Todos":
    dff = dff[dff["setor"] == setor_sel]
if risco_sel:
    dff = dff[dff["nivel_risco"].isin(risco_sel)]
if exchange_sel:
    dff = dff[dff["bolsa"].isin(exchange_sel)]

st.markdown('<div class="edn-section"><p class="edn-section-title">Resumo por nível de criticidade</p>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
for col, nivel, emoji in zip([c1, c2, c3],
                              ["Alto Risco", "Risco Moderado", "Baixo Risco"],
                              ["🔴", "🟡", "🟢"]):
    n   = (dff["nivel_risco"] == nivel).sum()
    pct = n / len(dff) * 100 if len(dff) else 0
    with col:
        st.metric(f"{emoji} {nivel}", f"{n} empresas", f"{pct:.1f}% da seleção")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="edn-section"><p class="edn-section-title">Mapa de posicionamento</p>', unsafe_allow_html=True)
st.plotly_chart(chart_criticality_matrix(dff), use_container_width=True)
st.caption(
    "Eixo X: Pontuação ESG total (quanto maior, menor o impacto de risco). "
    "Eixo Y: Probabilidade estimada de não-conformidade (inverso normalizado da pontuação). "
    "Passe o mouse sobre cada ponto para ver os detalhes da empresa."
)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="edn-section"><p class="edn-section-title">Empresas por nível de risco</p>', unsafe_allow_html=True)
nivel_tab = st.selectbox("Filtrar tabela por nível", ["Todos"] + RISK_ORDER)
tab_df = dff if nivel_tab == "Todos" else dff[dff["nivel_risco"] == nivel_tab]

COLS = ["sigla", "nome", "setor", "pontuacao_total",
        "pontuacao_ambiental", "pontuacao_social", "pontuacao_governanca", "nivel_risco"]
st.dataframe(
    tab_df[COLS].sort_values("pontuacao_total").reset_index(drop=True),
    use_container_width=True,
    hide_index=True,
    column_config={
        "sigla":               st.column_config.TextColumn("Sigla"),
        "nome":                st.column_config.TextColumn("Nome"),
        "setor":               st.column_config.TextColumn("Setor"),
        "nivel_risco":         st.column_config.TextColumn("Nível de risco"),
        "pontuacao_total":     st.column_config.NumberColumn("Pontuação total", format="%d"),
        "pontuacao_ambiental": st.column_config.NumberColumn("Ambiental", format="%d"),
        "pontuacao_social":    st.column_config.NumberColumn("Social", format="%d"),
        "pontuacao_governanca":st.column_config.NumberColumn("Governança", format="%d"),
    },
)
st.markdown('</div>', unsafe_allow_html=True)

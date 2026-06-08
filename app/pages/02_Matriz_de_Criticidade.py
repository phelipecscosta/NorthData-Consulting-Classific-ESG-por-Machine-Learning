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
edn_header("Matriz de Criticidade", "Classificação por Nível de Risco")

df = load_data()

with st.sidebar:
    st.markdown("### Filtros")
    setores = ["Todos"] + sorted(df["setor"].dropna().unique().tolist())
    setor_sel    = st.selectbox("Setor", setores)
    risco_sel    = st.multiselect("Nível de risco", RISK_ORDER, default=RISK_ORDER)
    exchange_sel = st.multiselect("Perfil", df["perfil"].unique().tolist(),
                                  default=df["perfil"].unique().tolist())

dff = df.copy()
if setor_sel != "Todos":
    dff = dff[dff["setor"] == setor_sel]
if risco_sel:
    dff = dff[dff["nivel_risco"].isin(risco_sel)]
if exchange_sel:
    dff = dff[dff["perfil"].isin(exchange_sel)]

st.markdown('<div class="edn-section"><p class="edn-section-title">Resumo por nível de criticidade</p>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
for col, nivel, emoji_c in zip([c1, c2, c3],
                              ["Alto Risco", "Risco Moderado", "Baixo Risco"],
                              ["🔴", "🟡", "🟢"]):
    n   = (dff["nivel_risco"] == nivel).sum()
    pct = n / len(dff) * 100 if len(dff) else 0
    with col:
        st.metric(f"{emoji_c} {nivel}", f"{n} empresas", f"{pct:.1f}% da avaliação")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="edn-section"><p class="edn-section-title">Mapa de posicionamento</p>', unsafe_allow_html=True)
st.plotly_chart(chart_criticality_matrix(dff), use_container_width=True)

with st.expander("Como interpretar este gráfico"):
    st.markdown("""
    - **Cada ponto é uma empresa** e a sua altura vertical indica a pontuação ESG total
    - **Pontos mais altos** = maior pontuação = menor risco de não-conformidade
    - **Pontos mais baixos** = menor pontuação = maior risco de não-conformidade
    - **Dentro de caixa** é mostrado onde estão as 50% das empresas do grupo
    - **A linha sólida** dentro da caixa é a mediana, ou seja, metade das empresas está acima, metade abaixo
    - **A linha tracejada** dentro da caixa é a média da pontuação do grupo
    - **As linhas saindo da caixa** acima e abaixo, indicam até onde vai a maioria das empresas do grupo, excluindo os casos extremos
    - **Pontos isoladas** indo além destas linhas máximas ou mínimas, são casos atípicos que merecem atenção especial (*outliers*)
    - **Compare as três caixas** de forma que o ideal é que a caixa verde (Baixo Risco) esteja claramente acima, a amarela (Risco Moderado) 
                no meio e a vermelha (Alto Risco) abaixo, sem mistura na altura entre elas. Quanto mais separadas, mais confiável é a classificação de risco
    """)

st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="edn-section"><p class="edn-section-title">Classificação das Empresas por nível de risco</p>', unsafe_allow_html=True)
col_f1, col_f2 = st.columns([2, 1])
with col_f1:
    nivel_tab = st.selectbox("Filtrar tabela por nível", ["Todos"] + RISK_ORDER)
with col_f2:
    ordem = st.radio("Ordem", ["Maior primeiro", "Menor primeiro"], horizontal=True)

asc = ordem == "Maior primeiro"
tab_df = dff if nivel_tab == "Todos" else dff[dff["nivel_risco"] == nivel_tab]

COLS = ["nivel_risco", "sigla", "nome", "setor", "pontuacao_total",
        "pontuacao_ambiental", "pontuacao_social", "pontuacao_governanca"]
st.dataframe(
    tab_df[COLS].sort_values("pontuacao_total", ascending=asc).reset_index(drop=True),
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

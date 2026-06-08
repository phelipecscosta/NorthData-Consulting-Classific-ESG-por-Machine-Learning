# app/Home.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from components.utils import inject_css, edn_header, load_data

st.set_page_config(
    page_title="ESG Risk Dashboard | Edenred",
    page_icon="🔴", layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
edn_header(
    "ESG Risk Dashboard",
    "Gestão de risco ESG de fornecedores — NorthData Consulting para Edenred",
)

df = load_data()

st.markdown('<div class="edn-section"><p class="edn-section-title">Visão geral</p>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Empresas avaliadas", len(df))
with c2:
    alto = (df["nivel_risco"] == "Alto Risco").sum()
    st.metric("Alto Risco", f"{alto} ({alto/len(df)*100:.0f}%)")
with c3:
    baixo = (df["nivel_risco"] == "Baixo Risco").sum()
    st.metric("Baixo Risco", f"{baixo} ({baixo/len(df)*100:.0f}%)")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
<div class="edn-section" style="margin-top:1rem">
    <p class="edn-section-title">Navegação</p>
    <p style="font-size:14px;color:#444441;line-height:1.8">
        Use o menu lateral para acessar as seções do dashboard:<br>
        <b>Scorecards</b> — KPIs principais, ranking e benchmarking<br>
        <b>Matriz de Criticidade</b> — Análise de riscos das empresas<br>
        <b>Mapa de Riscos ESG</b> — Mapa abrangente de risco ESG por setor e dimensão<br>
        <b>Fazer Previsão</b> — Classificar uma nova empresa
    </p>
</div>
""", unsafe_allow_html=True)

st.caption("@2026 NORTHDATA Consulting. Todos os direitos reservados")

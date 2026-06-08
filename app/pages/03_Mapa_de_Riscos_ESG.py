# app/pages/03_mapa_riscos.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from components.utils import inject_css, edn_header, load_data, RISK_ORDER
from components.charts import chart_sector_risk, chart_dimension_heatmap, chart_esg_radar

st.set_page_config(page_title="Mapa de Riscos | ESG Dashboard", page_icon="🔴",
                   layout="wide", initial_sidebar_state="expanded")
inject_css()
edn_header("Mapa de Riscos ESG", "Distribuição de risco por setor, dimensão e empresa")

df = load_data()

with st.sidebar:
    st.markdown("### Filtros")
    top_n        = st.slider("Top N setores", 5, len(df["setor"].unique()), 15)
    exchange_sel = st.multiselect("Perfil", df["perfil"].unique().tolist(),
                                  default=df["perfil"].unique().tolist())

dff = df[df["perfil"].isin(exchange_sel)] if exchange_sel else df

st.markdown('<div class="edn-section"><p class="edn-section-title">Alto Risco por setor de atuação</p>', unsafe_allow_html=True)
st.plotly_chart(chart_sector_risk(dff, top_n=top_n), use_container_width=True)
st.caption("Percentual de empresas classificadas como Alto Risco dentro de cada setor.")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="edn-section"><p class="edn-section-title">Pontuação média por setor x dimensão ESG</p>', unsafe_allow_html=True)
st.plotly_chart(chart_dimension_heatmap(dff), use_container_width=True)
st.caption("Verde = pontuação elevada (baixo risco). Vermelho = pontuação baixa (alto risco).")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="edn-section"><p class="edn-section-title">Recomendação de Plano de ação por nível de risco</p>', unsafe_allow_html=True)
planos = {
    "Alto Risco": {
        "cor": "#FCEBEB", "borda": "#E24B4A",
        "acoes": [
            "Auditoria presencial imediata",
            "Exigência de plano para adequação em até 30 dias",
            "Acompanhamento mensal de indicadores",
            "Obter certificações (Ex.: ISO 14001 / SA8000)",
            "Revisão de contrato com cláusulas ESG",
        ],
    },
    "Risco Moderado": {
        "cor": "#FAEEDA", "borda": "#BA7517",
        "acoes": [
            "Treinamento em práticas ESG (online ou presencial)",
            "Reforço documental — políticas e processos",
            "Acompanhamento trimestral",
            "Recomendações de melhoria por dimensão",
            "Desenvolvimento de política de diversidade e inclusão",
        ],
    },
    "Baixo Risco": {
        "cor": "#EAF3DE", "borda": "#639922",
        "acoes": [
            "Monitoramento semestral de indicadores",
            "Compartilhamento de boas práticas com a cadeia",
            "Elegível para programa de fornecedor preferencial",
            "Convite para grupo de trabalho ESG Edenred",
        ],
    },
}

for nivel, info in planos.items():
    n_empresas = (dff["nivel_risco"] == nivel).sum()
    with st.expander(f"{nivel} — {n_empresas} empresas na seleção", expanded=(nivel == "Alto Risco")):
        st.markdown(
            f"""
            <div style="background:{info['cor']};border-left:4px solid {info['borda']};
                        padding:1rem;border-radius:0 8px 8px 0;">
                <ul style="margin:0;padding-left:1.2rem;font-size:14px;line-height:2">
                    {''.join(f'<li>{a}</li>' for a in info['acoes'])}
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="edn-section"><p class="edn-section-title">Perfil individual de empresa</p>', unsafe_allow_html=True)
empresa_sel = st.selectbox(
    "Selecione uma empresa ou escreva (sigla ou nome)",
    options=dff["sigla"].tolist(),
    format_func=lambda t: f"{t} — {dff[dff['sigla']==t]['nome'].values[0]}",
)
row = dff[dff["sigla"] == empresa_sel].iloc[0]

col_r, col_i = st.columns([1, 1])
with col_r:
    st.plotly_chart(chart_esg_radar(row), use_container_width=True)
with col_i:
    nivel    = row["nivel_risco"]
    cor      = planos[nivel]["borda"]
    st.markdown(f"""
    <div style="padding:1rem">
        <p style="font-size:13px;color:#888780;text-transform:uppercase;letter-spacing:.06em">Empresa</p>
        <p style="font-size:18px;font-weight:500">{row['nome']} ({row['sigla']})</p>
        <p style="font-size:13px;color:#888780">Setor: {row['setor']} · Perfil: {row['perfil']}</p>
        <hr style="border-color:#F1EFE8">
        <p style="font-size:13px;color:#888780;text-transform:uppercase">Nível de risco</p>
        <p style="font-size:22px;font-weight:500;color:{cor}">{nivel}</p>
        <p>Pontuação total: <b>{int(row['pontuacao_total'])}</b></p>
        <p>Ambiental: {int(row['pontuacao_ambiental'])} ·
           Social: {int(row['pontuacao_social'])} ·
           Governança: {int(row['pontuacao_governanca'])}</p>
        <hr style="border-color:#F1EFE8">
        <p style="font-size:13px;color:#888780">
            Ambiental: {row['maturidade_ambiental']} · {row['confiabilidade_ambiental']}<br>
            Social: {row['maturidade_social']} · {row['confiabilidade_social']}<br>
            Governança: {row['maturidade_governanca']} · {row['confiabilidade_governanca']}
        </p>
    </div>
    """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

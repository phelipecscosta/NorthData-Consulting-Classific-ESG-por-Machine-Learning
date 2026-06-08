# app/pages/04_previsao.py
# Previsão de scores ESG para novas empresas usando modelos do MLflow.
# O formulário usa a linguagem do cliente (PT-BR).
# O translator.py faz a conversão para o modelo (EN) e de volta para PT.

import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"

import streamlit as st
import pandas as pd
import mlflow.sklearn

from components.utils import (
    inject_css, edn_header, load_data,
    append_new_company, RISK_COLORS,
)
from components.charts import chart_esg_radar
from translator import (
    traduzir_entrada_para_modelo,
    traduzir_linha_para_dashboard,
    SETOR_PT_PARA_EN,
    MATURIDADE_PT_PARA_EN,
    formatar_cnpj,
)

st.set_page_config(
    page_title="Previsão | ESG Dashboard",
    page_icon="🔴", layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
edn_header("Previsão de Risco ESG", "Classificar uma nova empresa usando o modelo treinado")

# ── Configuração dos modelos MLflow ───────────────────────────
ROOT = Path(__file__).parent.parent.parent
MLRUNS_URI = f"file:///{(ROOT / 'mlruns').as_posix()}"
mlflow.set_tracking_uri(MLRUNS_URI)

RUN_IDS = {
    "environment_score": "ad716cdf9b4e",
    "social_score":      "9c9dbca8c8dd",
    "governance_score":  "2815fb1d2881",
}

@st.cache_resource
def load_models():
    modelos = {}
    for target, run_id in RUN_IDS.items():
        uri = f"runs:/{run_id}/model"
        try:
            modelos[target] = mlflow.sklearn.load_model(uri)
        except Exception as e:
            st.error(f"Erro ao carregar modelo {target}: {e}")
    return modelos

modelos = load_models()

SETORES_PT     = sorted(SETOR_PT_PARA_EN.keys())
MATURIDADES_PT = list(MATURIDADE_PT_PARA_EN.keys())
CONFIABILIDADES_PT = ["Auditada", "Não auditada"]

df_gold = load_data()

# ── Formulário PT-BR ─────────────────────────────────────────
st.markdown('<div class="edn-section"><p class="edn-section-title">Dados da nova empresa</p>', unsafe_allow_html=True)

with st.form("form_previsao"):
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Identificação**")
        cnpj  = st.text_input("CNPJ (somente números)", max_chars=14, placeholder="00000000000000")
        sigla = st.text_input("Sigla (ticker)", max_chars=10).upper()
        nome  = st.text_input("Nome da empresa")
        bolsa = st.selectbox("Bolsa", ["NYSE", "NASDAQ"])
        setor = st.selectbox("Setor", SETORES_PT)

    with c2:
        st.markdown("**Porte**")
        faturamento = st.number_input("Faturamento anual (em milhões USD)", min_value=0, value=1000, step=100)
        tamanho     = st.number_input("Número de funcionários", min_value=0, value=5000, step=100)
        st.markdown("**Avaliação ESG**")
        col_m, col_c = st.columns(2)
        with col_m:
            mat_amb = st.selectbox("Maturidade Ambiental",  MATURIDADES_PT, key="mat_amb")
            mat_soc = st.selectbox("Maturidade Social",     MATURIDADES_PT, key="mat_soc")
            mat_gov = st.selectbox("Maturidade Governança", MATURIDADES_PT, key="mat_gov")
        with col_c:
            conf_amb = st.selectbox("Confiabilidade Ambiental",  CONFIABILIDADES_PT, key="conf_amb")
            conf_soc = st.selectbox("Confiabilidade Social",     CONFIABILIDADES_PT, key="conf_soc")
            conf_gov = st.selectbox("Confiabilidade Governança", CONFIABILIDADES_PT, key="conf_gov")

    submitted = st.form_submit_button("Classificar empresa", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

if submitted:
    if not cnpj or not sigla or not nome:
        st.warning("Preencha ao menos CNPJ, sigla e nome da empresa.")
        st.stop()

    cnpj_fmt = formatar_cnpj(cnpj)

    if sigla in df_gold["sigla"].str.upper().values:
        st.warning(f"A sigla '{sigla}' já existe no dataset.")
        st.stop()

    dados_pt = {
        "cnpj": cnpj_fmt, "sigla": sigla, "nome": nome,
        "bolsa": bolsa, "setor": setor,
        "faturamento": faturamento, "tamanho": tamanho,
        "maturidade_ambiental": mat_amb, "confiabilidade_ambiental": conf_amb,
        "maturidade_social": mat_soc,    "confiabilidade_social": conf_soc,
        "maturidade_governanca": mat_gov,"confiabilidade_governanca": conf_gov,
    }

    try:
        entrada_en = traduzir_entrada_para_modelo(dados_pt)
    except ValueError as e:
        st.error(f"Erro na tradução: {e}")
        st.stop()

    entrada_df = pd.DataFrame([entrada_en])
    scores = {}
    with st.spinner("Calculando scores ESG..."):
        for dim in ["environment_score", "social_score", "governance_score"]:
            pred = modelos[dim].predict(entrada_df)[0]
            scores[dim] = max(0, round(float(pred)))

    total_score = sum(scores.values())
    if total_score < 900:
        nivel_risco = "Alto Risco"
    elif total_score <= 1150:
        nivel_risco = "Risco Moderado"
    else:
        nivel_risco = "Baixo Risco"

    linha_en = {
        "cik": cnpj_fmt, "ticker": sigla, "name": nome,
        "exchange": bolsa, "industry": entrada_en["industry"],
        "revenue_M": faturamento, "employees": tamanho,
        "environment_grade": entrada_en["environment_grade"],
        "social_grade":      entrada_en["social_grade"],
        "governance_grade":  entrada_en["governance_grade"],
        "environment_score": scores["environment_score"],
        "social_score":      scores["social_score"],
        "governance_score":  scores["governance_score"],
        "total_score":       total_score,
        "risk_level":        nivel_risco,
    }
    linha_pt = traduzir_linha_para_dashboard(linha_en)

    st.markdown('<div class="edn-section"><p class="edn-section-title">Resultado da previsão</p>', unsafe_allow_html=True)
    cor_risco = RISK_COLORS.get(nivel_risco, "#888780")

    col_res1, col_res2 = st.columns([1, 1])
    with col_res1:
        st.markdown(f"""
        <div style="padding:1rem">
            <p style="font-size:13px;color:#888780;text-transform:uppercase">Empresa prevista</p>
            <p style="font-size:20px;font-weight:500">{nome} ({sigla})</p>
            <p style="font-size:13px;color:#888780">{setor} · {bolsa}</p>
            <hr style="border-color:#F1EFE8;margin:1rem 0">
            <p style="font-size:13px;color:#888780;text-transform:uppercase">Nível de risco previsto</p>
            <p style="font-size:28px;font-weight:500;color:{cor_risco}">{nivel_risco}</p>
            <p style="font-size:14px"><b>Pontuação total:</b> {total_score}</p>
            <p style="font-size:14px">
                Ambiental: <b>{scores['environment_score']}</b> ·
                Social: <b>{scores['social_score']}</b> ·
                Governança: <b>{scores['governance_score']}</b>
            </p>
            <hr style="border-color:#F1EFE8;margin:1rem 0">
            <p style="font-size:13px;color:#888780;text-transform:uppercase">Detalhamento ESG</p>
            <p style="font-size:13px">
                Ambiental: {linha_pt['maturidade_ambiental']} · {linha_pt['confiabilidade_ambiental']}<br>
                Social: {linha_pt['maturidade_social']} · {linha_pt['confiabilidade_social']}<br>
                Governança: {linha_pt['maturidade_governanca']} · {linha_pt['confiabilidade_governanca']}
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_res2:
        row_preview = pd.Series({
            "name": nome,
            "environment_score": scores["environment_score"],
            "social_score":      scores["social_score"],
            "governance_score":  scores["governance_score"],
        })
        st.plotly_chart(chart_esg_radar(row_preview), use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    append_new_company(linha_pt)
    st.success(f"Empresa '{nome}' salva com sucesso! Ela já aparece nas demais páginas.")

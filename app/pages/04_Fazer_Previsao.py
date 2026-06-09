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
from datetime import date
import mlflow.sklearn

from components.utils import (
    inject_css, edn_header, load_data,
    append_new_company, RISK_COLORS,
)
from components.charts import chart_esg_radar
from translator import (
    traduzir_entrada_para_modelo,
    traduzir_linha_para_dashboard,
    processar_planilha_em_lote,
    ler_planilha,
    verificar_duplicatas,
    SETOR_PT_PARA_EN,
    MATURIDADE_PT_PARA_EN,
    BOLSA_PT_PARA_EN,
    GOLD_COLS_PT,
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
TEMPLATE_PATH = ROOT / "data" / "template" / "modelo_cadastro_novas_empresas.xlsx"
GOLD_PATH     = ROOT / "data" / "gold" / "data_gold.csv"


@st.cache_resource
def load_models():
    modelos = {}
    nomes = {
        "environment_score": "Random Forest_environment_score.pkl",
        "social_score":      "Random Forest_social_score.pkl",
        "governance_score":  "Random Forest_governance_score.pkl",
    }
    for target, arquivo in nomes.items():
        try:
            import joblib
            modelos[target] = joblib.load(ROOT / "models" / arquivo)
        except Exception as e:
            st.error(f"Erro ao carregar modelo {target}: {e}")
    return modelos

modelos = load_models()

SETORES_PT     = sorted(SETOR_PT_PARA_EN.keys())
MATURIDADES_PT = list(MATURIDADE_PT_PARA_EN.keys())
CONFIABILIDADES_PT = ["Auditada", "Não auditada"]

df_gold = load_data()

def calcular_nivel_risco(total):
    if total < 900:     return "Alto Risco"
    elif total <= 1150: return "Risco Moderado"
    return "Baixo Risco"


def append_to_gold(df_novo: pd.DataFrame, sobrescrever_siglas: list = []):
    """Appenda ou sobrescreve linhas no data_gold.csv."""
    df_atual = pd.read_csv(GOLD_PATH, encoding="utf-8")
    if sobrescrever_siglas:
        df_atual = df_atual[~df_atual["sigla"].str.upper().isin(
            [s.upper() for s in sobrescrever_siglas]
        )]
    df_final = pd.concat([df_atual, df_novo[GOLD_COLS_PT]], ignore_index=True)
    df_final.to_csv(GOLD_PATH, index=False, encoding="utf-8")
    load_data.clear()

# ── Formulário PT-BR ─────────────────────────────────────────
aba1, aba2 = st.tabs([" Empresa individual", " Importar planilha (em lote)"])

# ── ABA 1: individual ─────────────────────────────────────────
with aba1:
    st.markdown('<div class="edn-section"><p class="edn-section-title">Dados da nova empresa</p>', unsafe_allow_html=True)


    with st.form("form_previsao"):
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("**Identificação**")
            cnpj  = st.text_input("CNPJ (somente números)", max_chars=14, placeholder="00000000000000")
            sigla = st.text_input("Sigla (ticker)", max_chars=10).upper()
            nome  = st.text_input("Nome da empresa")
            perfil = st.selectbox("Perfil", ["Tradicional", "Inovador"])
            setor = st.selectbox("Setor", SETORES_PT)

        with c2:
            st.markdown("**Porte**")
            faturamento = st.number_input("Faturamento anual (em R$)", min_value=0, value=1000, step=100)
            tamanho     = st.number_input("Número de funcionários", min_value=0, value=5000, step=100)
            st.markdown("**Avaliação ESG**")
            col_m, col_c = st.columns(2)
            with col_m:
                mat_amb = st.selectbox("Maturidade (Ambiental)",  MATURIDADES_PT, key="mat_amb")
                mat_soc = st.selectbox("Maturidade (Social)",     MATURIDADES_PT, key="mat_soc")
                mat_gov = st.selectbox("Maturidade (Governança)", MATURIDADES_PT, key="mat_gov")
            with col_c:
                conf_amb = st.selectbox("Confiabilidade (Ambiental)",  CONFIABILIDADES_PT, key="conf_amb")
                conf_soc = st.selectbox("Confiabilidade (Social)",     CONFIABILIDADES_PT, key="conf_soc")
                conf_gov = st.selectbox("Confiabilidade (Governança)", CONFIABILIDADES_PT, key="conf_gov")

        submitted = st.form_submit_button("Classificar empresa", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    if submitted:
        if not cnpj or not sigla or not nome:
            st.warning("Preencha ao menos CNPJ, sigla e nome da empresa.")
            st.stop()

        cnpj_fmt = formatar_cnpj(cnpj)
        sigla_up = sigla.upper()

        dup_sigla = sigla_up in df_gold["sigla"].str.upper().tolist()
        dup_cnpj  = cnpj_fmt in df_gold["cnpj"].astype(str).tolist()

        if dup_sigla or dup_cnpj:
            campo = "sigla" if dup_sigla else "cnpj"
            valor = sigla_up if dup_sigla else cnpj_fmt
            st.warning(f"⚠️ A empresa {campo.upper()} **{valor}** já cadastrada. Deseja sobrescrever e reavaliar?")
            col_sim, col_nao = st.columns(2)
            with col_sim:
                if st.button("✅ Sim, sobrescrever", use_container_width=True, key="ind_sim"):
                    st.session_state["ind_sobrescrever"] = sigla_up
            with col_nao:
                if st.button("❌ Não, cancelar", use_container_width=True, key="ind_nao"):
                    st.session_state.pop("ind_sobrescrever", None)
                    st.info("Operação cancelada.")
                    st.stop()

        if sigla in df_gold["sigla"].str.upper().values:
            st.warning(f"A sigla '{sigla}' já existe no dataset.")
            st.stop()

        dados_pt = {
            "cnpj": cnpj_fmt, 
            "sigla": sigla,
            "nome": nome,
            "perfil": perfil, 
            "setor": setor,
            "faturamento": faturamento, 
            "tamanho": tamanho,
            "maturidade_ambiental": mat_amb, 
            "confiabilidade_ambiental": conf_amb,
            "maturidade_social": mat_soc,    
            "confiabilidade_social": conf_soc,
            "maturidade_governanca": mat_gov,
            "confiabilidade_governanca": conf_gov,
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
            "cik": cnpj_fmt, 
            "ticker": sigla, 
            "name": nome,
            "exchange": BOLSA_PT_PARA_EN.get(perfil, perfil),
            "industry": entrada_en["industry"],
            "revenue_M": faturamento, "employees": tamanho,
            "environment_grade": entrada_en["environment_grade"],
            "social_grade":      entrada_en["social_grade"],
            "governance_grade":  entrada_en["governance_grade"],
            "environment_score": scores["environment_score"],
            "social_score":      scores["social_score"],
            "governance_score":  scores["governance_score"],
            "total_score":       total_score,
            "risk_level":        nivel_risco,
            "last_processing_date": date.today().strftime("%d/%m/%Y"),
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
                <p style="font-size:13px;color:#888780">{setor} · {perfil}</p>
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

        append_to_gold(pd.DataFrame([linha_pt]))
        st.success(f"Empresa '{nome}' salva com sucesso! Ela já aparece nas demais páginas.")

# ── ABA 2: em lote ────────────────────────────────────────────
with aba2:
    st.markdown('<div class="edn-section"><p class="edn-section-title">Cadastro em massa via planilha</p>', unsafe_allow_html=True)

    col_dl, col_up = st.columns([1, 2])
    with col_dl:
        st.markdown("**1. Baixar template**")
        if TEMPLATE_PATH.exists():
            with open(TEMPLATE_PATH, "rb") as f:
                st.download_button(
                    label="⬇️ Baixar planilha template",
                    data=f.read(),
                    file_name="modelo_cadastro_novas_empresas.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
        else:
            st.warning("Template não encontrado em data/template/.")

    with col_up:
        st.markdown("**2. Enviar planilha preenchida**")
        arquivo = st.file_uploader(
            "Selecione o arquivo .xlsx preenchido",
            type=["xlsx"],
            label_visibility="collapsed",
        )

    st.markdown('</div>', unsafe_allow_html=True)

    if arquivo:
        df_plan, erros_leitura = ler_planilha(arquivo)

        if erros_leitura:
            for e in erros_leitura:
                st.error(e)
            st.stop()

        st.success(f"Planilha lida com sucesso: **{len(df_plan)} empresas** encontradas.")
        st.dataframe(df_plan, use_container_width=True, height=200, hide_index=True)

        conflitos = verificar_duplicatas(df_plan, df_gold)

        if conflitos:
            st.warning(f"⚠️ Foram encontrados **{len(conflitos)} conflitos** com registros já existentes:")
            for c in conflitos:
                st.markdown(f"- Linha **{c['linha']}** — `{c['campo'].upper()}` **{c['valor']}** já cadastrado e avaliado.")

            st.markdown("**Deseja sobrescrever e reavaliar esses registros?**")
            col_s, col_n = st.columns(2)
            with col_s:
                if st.button("✅ Sim, sobrescrever todos", use_container_width=True, key="lote_sim"):
                    st.session_state["lote_sobrescrever"] = [c["valor"] for c in conflitos if c["campo"] == "sigla"]
                    st.session_state["lote_processar"]    = True
                    st.rerun()
            with col_n:
                if st.button("❌ Não — corrigir planilha", use_container_width=True, key="lote_nao"):
                    st.error("Operação cancelada. Corrija os registros duplicados e faça o upload novamente.")
                    st.stop()
        else:
            st.session_state["lote_processar"]    = True
            st.session_state["lote_sobrescrever"] = []

        if st.session_state.get("lote_processar"):
            sob_siglas = st.session_state.pop("lote_sobrescrever", [])
            st.session_state.pop("lote_processar", None)

            with st.spinner(f"Processando {len(df_plan)} empresas..."):
                df_resultado, erros_proc = processar_planilha_em_lote(df_plan, modelos)

            if erros_proc:
                st.warning(f"**{len(erros_proc)} linha(s) com erro** foram ignoradas:")
                for e in erros_proc:
                    st.markdown(f"- {e}")

            if not df_resultado.empty:
                append_to_gold(df_resultado, sobrescrever_siglas=sob_siglas)
                st.success(f"✅ **{len(df_resultado)} empresas** classificadas e salvas no dashboard!")

                st.markdown('<div class="edn-section"><p class="edn-section-title">Resultado do processamento</p>', unsafe_allow_html=True)
                dist = df_resultado["nivel_risco"].value_counts()
                c1, c2, c3 = st.columns(3)
                for col, nivel, emoji in zip(
                    [c1, c2, c3],
                    ["Alto Risco", "Risco Moderado", "Baixo Risco"],
                    ["🔴", "🟡", "🟢"]
                ):
                    with col:
                        st.metric(f"{emoji} {nivel}", dist.get(nivel, 0))

                st.dataframe(
                    df_resultado[["sigla", "nome", "setor", "pontuacao_total",
                                  "pontuacao_ambiental", "pontuacao_social",
                                  "pontuacao_governanca", "nivel_risco"]],
                    use_container_width=True,
                    height=350,
                    hide_index=True,
                )
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.error("Nenhuma empresa foi processada. Verifique os erros acima.")



st.caption("@2026 NORTHDATA Consulting. Todos os direitos reservados")
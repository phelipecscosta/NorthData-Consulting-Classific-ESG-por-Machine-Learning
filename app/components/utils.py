# app/components/utils.py
# Funções utilitárias compartilhadas entre todas as páginas.
# O Gold agora está em PT-BR — todas as referências de coluna refletem isso.

from pathlib import Path
import pandas as pd
import streamlit as st

ROOT     = Path(__file__).parent.parent.parent
GOLD     = ROOT / "data" / "gold" / "data_gold.csv"
NEW_CO   = ROOT / "data" / "gold" / "new_companies.csv"
CSS_PATH = Path(__file__).parent.parent / "style" / "edenred.css"

RISK_ORDER  = ["Alto Risco", "Risco Moderado", "Baixo Risco"]
RISK_COLORS = {
    "Alto Risco":     "#E24B4A",
    "Risco Moderado": "#BA7517",
    "Baixo Risco":    "#639922",
}
RISK_BADGES = {
    "Alto Risco":     "badge-alto",
    "Risco Moderado": "badge-moderado",
    "Baixo Risco":    "badge-baixo",
}


def inject_css():
    """Injeta CSS Edenred + JS para corrigir o botão de sidebar."""
    with open(CSS_PATH, encoding="utf-8") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    st.markdown(f"""
    <style>
    /* Esconde botão de recolher IMEDIATAMENTE — antes do render */
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"],
    button[aria-label="Close sidebar"],
    button[aria-label="Open sidebar"] {{
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
        width: 0 !important;
        height: 0 !important;
    }}
    </style>
    """, unsafe_allow_html=True)

def edn_header(title: str, subtitle: str = ""):
    sub_html = f'<p class="edn-subtitle">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f"""
        <div class="edn-header">
            <div class="edn-circle">E</div>
            <div>
                <h1>{title}</h1>
                {sub_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=60)
def load_data() -> pd.DataFrame:
    """
    Carrega Gold + New Companies (ambos em PT-BR) e concatena.
    Cache de 60s para refletir novas previsões rapidamente.
    """
    gold = pd.read_csv(GOLD, encoding="utf-8")
    try:
        new = pd.read_csv(NEW_CO, encoding="utf-8")
        if not new.empty:
            return pd.concat([gold, new], ignore_index=True)
    except Exception:
        pass
    return gold


def append_new_company(row: dict):
    """Adiciona uma nova empresa (já em PT-BR) ao new_companies.csv."""
    df_new = pd.DataFrame([row])
    if NEW_CO.exists() and NEW_CO.stat().st_size > 50:
        df_new.to_csv(NEW_CO, mode="a", header=False, index=False, encoding="utf-8")
    else:
        df_new.to_csv(NEW_CO, index=False, encoding="utf-8")
    load_data.clear()


def risk_badge(nivel: str) -> str:
    cls = RISK_BADGES.get(nivel, "badge-moderado")
    return f'<span class="{cls}">{nivel}</span>'


def calcular_nivel_risco(pontuacao_total: float) -> str:
    if pontuacao_total < 900:
        return "Alto Risco"
    elif pontuacao_total <= 1150:
        return "Risco Moderado"
    return "Baixo Risco"

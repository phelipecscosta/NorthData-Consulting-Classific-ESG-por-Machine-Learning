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

    st.markdown("""
    <script>
    (function fixSidebarButton() {
        function applyFix() {
            const btn = document.querySelector('[data-testid="stSidebarCollapsedControl"]');
            if (btn) {
                btn.style.cssText = [
                    'visibility:visible!important',
                    'display:flex!important',
                    'opacity:1!important',
                    'background-color:#E30613!important',
                    'border-radius:0 6px 6px 0!important',
                    'padding:8px 4px!important',
                    'position:fixed!important',
                    'left:0!important',
                    'top:50%!important',
                    'transform:translateY(-50%)!important',
                    'z-index:999999!important',
                    'box-shadow:2px 0 8px rgba(0,0,0,0.2)!important',
                ].join(';');
                const svg = btn.querySelector('svg');
                if (svg) svg.style.cssText = 'fill:white!important;color:white!important;stroke:white!important';
            }
        }
        applyFix();
        const id = setInterval(applyFix, 300);
        setTimeout(() => clearInterval(id), 5000);
        new MutationObserver(applyFix).observe(document.body, { childList: true, subtree: true });
    })();
    </script>
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

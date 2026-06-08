# app/components/kpi_card.py
# Card KPI reutilizável com identidade Edenred.

import streamlit as st


def render_kpi_card(label: str, value: str, delta: str = "", delta_type: str = "neu"):
    """
    Renderiza um card KPI com estilo Edenred.

    Parâmetros
    ----------
    label      : texto superior (ex: "Fornecedores ESG ativos")
    value      : valor principal (ex: "68%" ou "722")
    delta      : texto de variação (ex: "+4% vs mês ant.") — opcional
    delta_type : "up" (verde) | "down" (vermelho) | "neu" (cinza)
    """
    delta_class = f"kpi-delta-{delta_type}"
    delta_html  = f'<p class="{delta_class}">{delta}</p>' if delta else ""

    st.markdown(
        f"""
        <div class="kpi-card">
            <p class="kpi-label">{label}</p>
            <p class="kpi-value">{value}</p>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

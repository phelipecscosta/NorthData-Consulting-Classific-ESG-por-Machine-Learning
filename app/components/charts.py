# app/components/charts.py
# Funções de gráficos reutilizáveis — identidade visual Edenred.
# Todas as colunas usam nomenclatura PT-BR do Gold.

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

EDENRED_RED = "#E30613"
MUTED       = "#888780"

RISK_COLORS = {
    "Alto Risco":     "#E24B4A",
    "Risco Moderado": "#F5C400",
    "Baixo Risco":    "#75C118",
}

DIMENSION_COLORS = {
    "Ambiental":  "#5AD36C",
    "Social":     "#5988E0",
    "Governança": "#DA974C",
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor="white",
    plot_bgcolor="white",
    font_family="DM Sans, sans-serif",
    font_color="#1A1A1A",
    margin=dict(l=16, r=16, t=32, b=16),
)


def chart_risk_distribution(df: pd.DataFrame) -> go.Figure:
    """Donut com distribuição dos níveis de risco."""
    counts = (
        df["nivel_risco"]
        .value_counts()
        .reindex(["Alto Risco", "Risco Moderado", "Baixo Risco"])
        .fillna(0)
    )
    fig = go.Figure(go.Pie(
        labels=counts.index,
        values=counts.values,
        hole=0.55,
        marker_colors=[RISK_COLORS[l] for l in counts.index],
        textfont_size=12,
        textposition="outside",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        showlegend=True,
        legend=dict(orientation="h", y=-0.15, itemclick=False, itemdoubleclick=False),
        title=dict(text="Distribuição por nível de risco", font_size=13, x=0.5),
        height=400,
    )
    return fig


def chart_score_by_dimension(df: pd.DataFrame) -> go.Figure:
    """Barras agrupadas: pontuação média E, S, G por nível de risco."""
    medias = (
        df.groupby("nivel_risco")[
            ["pontuacao_ambiental", "pontuacao_social", "pontuacao_governanca"]
        ]
        .mean()
        .round(0)
        .reindex(["Alto Risco", "Risco Moderado", "Baixo Risco"])
    )

    fig = go.Figure()
    dims = {
        "pontuacao_ambiental":   ("Ambiental",  DIMENSION_COLORS["Ambiental"]),
        "pontuacao_social":      ("Social",     DIMENSION_COLORS["Social"]),
        "pontuacao_governanca":  ("Governança", DIMENSION_COLORS["Governança"]),
    }
    for col, (nome, cor) in dims.items():
        fig.add_trace(go.Bar(
            name=nome,
            x=medias.index,
            y=medias[col],
            marker_color=cor,
            text=medias[col].astype(int),
            textposition="outside",
        ))

    fig.update_layout(
        **PLOTLY_LAYOUT,
        barmode="group",
        title=dict(text="Pontuação média por dimensão e nível de risco", font_size=13, x=0),
        xaxis_title="",
        yaxis_title="Pontuação média",
        legend=dict(orientation="h", y=-0.15, itemclick=False, itemdoubleclick=False),
        height=400,
    )
    return fig


def chart_sector_risk(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """Barras horizontais: % de Alto Risco por setor (top N)."""
    sector_risk = (
        df.groupby("setor")
        .apply(lambda g: (g["nivel_risco"] == "Alto Risco").mean() * 100,
               include_groups=False)
        .rename("pct_alto")
        .reset_index()
        .sort_values("pct_alto", ascending=True)
        .tail(top_n)
    )

    fig = go.Figure(go.Bar(
        x=sector_risk["pct_alto"],
        y=sector_risk["setor"],
        orientation="h",
        marker_color=EDENRED_RED,
        text=sector_risk["pct_alto"].round(1).astype(str) + "%",
        textposition="outside",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text=f"% de Alto Risco por setor (top {top_n})", font_size=13, x=0),
        xaxis_title="% Alto Risco",
        yaxis_title="",
        height=max(350, top_n * 26),
        xaxis=dict(range=[0, 110]),
    )
    return fig


def chart_criticality_matrix(df: pd.DataFrame) -> go.Figure:
    """
    Scatter matrix de criticidade.
    Eixo X = pontuacao_total | Eixo Y = probabilidade de não-conformidade
    """
    df = df.copy()
    score_min = df["pontuacao_total"].min()
    score_max = df["pontuacao_total"].max()
    df["prob_nc"] = 100 - (
        (df["pontuacao_total"] - score_min) / (score_max - score_min) * 100
    )

    fig = px.scatter(
        df,
        x="pontuacao_total",
        y="prob_nc",
        color="nivel_risco",
        color_discrete_map=RISK_COLORS,
        hover_name="nome",
        hover_data={"sigla": True, "setor": True,
                    "pontuacao_total": True, "prob_nc": ":.1f"},
        labels={
            "pontuacao_total": "Pontuação ESG total (impacto)",
            "prob_nc":         "Probabilidade de não-conformidade (%)",
            "nivel_risco":     "Nível de risco",
        },
        opacity=0.75,
    )

    mid_x = df["pontuacao_total"].median()
    fig.add_vline(x=mid_x, line_dash="dash", line_color=MUTED, line_width=1)
    fig.add_hline(y=50,    line_dash="dash", line_color=MUTED, line_width=1)

    anots = [
        (score_min + 30, 90, "Alto impacto<br>Alto risco",   RISK_COLORS["Alto Risco"]),
        (mid_x + 30,     90, "Baixo impacto<br>Alto risco",  RISK_COLORS["Risco Moderado"]),
        (score_min + 30, 10, "Alto impacto<br>Baixo risco",  RISK_COLORS["Risco Moderado"]),
        (mid_x + 30,     10, "Baixo impacto<br>Baixo risco", RISK_COLORS["Baixo Risco"]),
    ]
    for ax, ay, txt, cor in anots:
        fig.add_annotation(x=ax, y=ay, text=txt, showarrow=False,
                           font=dict(size=10, color=cor), align="left")

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="Matriz de criticidade", font_size=13, x=0),
        height=480,
        legend=dict(orientation="h", y=-0.15),
    )
    return fig


def chart_esg_radar(row: pd.Series) -> go.Figure:
    """Radar chart para uma empresa individual."""
    # Aceita tanto colunas EN quanto PT
    env = row.get("pontuacao_ambiental", row.get("environment_score", 0))
    soc = row.get("pontuacao_social",    row.get("social_score", 0))
    gov = row.get("pontuacao_governanca",row.get("governance_score", 0))
    nome = row.get("nome", row.get("name", "Empresa"))

    categorias = ["Ambiental", "Social", "Governança"]
    valores    = [env, soc, gov]

    fig = go.Figure(go.Scatterpolar(
        r=valores + [valores[0]],
        theta=categorias + [categorias[0]],
        fill="toself",
        fillcolor="rgba(227,6,19,0.15)",
        line=dict(color=EDENRED_RED, width=2),
        name=nome,
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 750]),
            bgcolor="white",
        ),
        height=320,
        showlegend=False,
        title=dict(text="Perfil ESG por dimensão", font_size=13, x=0.5),
    )
    return fig


def chart_dimension_heatmap(df: pd.DataFrame) -> go.Figure:
    """Heatmap: pontuação média por setor e dimensão."""
    pivot = (
        df.groupby("setor")[
            ["pontuacao_ambiental", "pontuacao_social", "pontuacao_governanca"]
        ]
        .mean()
        .round(0)
        .rename(columns={
            "pontuacao_ambiental":  "Ambiental",
            "pontuacao_social":     "Social",
            "pontuacao_governanca": "Governança",
        })
        .sort_values("Ambiental")
    )

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[[0, "#FCEBEB"], [0.5, "#FAEEDA"], [1, "#EAF3DE"]],
        text=pivot.values.astype(int),
        texttemplate="%{text}",
        textfont_size=10,
        showscale=True,
        colorbar=dict(title="Pontuação", thickness=14),
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="Mapa de calor ESG por setor", font_size=13, x=0),
        height=max(400, len(pivot) * 22 + 60),
        yaxis=dict(autorange="reversed"),
    )
    return fig

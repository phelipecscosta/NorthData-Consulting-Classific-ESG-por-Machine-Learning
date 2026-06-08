# src/translator.py
# ============================================================
# Tradutor bidirecional entre o dataset do cliente (PT-BR)
# e o dataset do modelo de ML (EN).
#
# Responsabilidades:
#   - Renomear colunas PT → EN  (para o modelo)
#   - Renomear colunas EN → PT  (para o dashboard)
#   - Converter valores de setor, maturidade, grade
#   - Derivar grade a partir de maturidade + confiabilidade
#   - Aplicar zero-padding de 14 dígitos no CNPJ/cik
# ============================================================

# ── Mapeamento de colunas ────────────────────────────────────
COLUNAS_PT_PARA_EN = {
    "cnpj":                    "cik",
    "sigla":                   "ticker",
    "nome":                    "name",
    "perfil":                   "exchange",
    "setor":                   "industry",
    "faturamento":             "revenue_M",
    "tamanho":                 "employees",
    "confiabilidade_ambiental":"environment_grade",
    "maturidade_ambiental":    "environment_level",
    "pontuacao_ambiental":     "environment_score",
    "confiabilidade_social":   "social_grade",
    "maturidade_social":       "social_level",
    "pontuacao_social":        "social_score",
    "confiabilidade_governanca":"governance_grade",
    "maturidade_governanca":   "governance_level",
    "pontuacao_governanca":    "governance_score",
    "pontuacao_total":         "total_score",
    "nivel_risco":             "risk_level",
}

COLUNAS_EN_PARA_PT = {v: k for k, v in COLUNAS_PT_PARA_EN.items()}

# ── Mapeamento de bolsa (exchange) ───────────────────────────
BOLSA_EN_PARA_PT = {
    "NYSE":   "Tradicional",
    "NASDAQ": "Inovador",
}

BOLSA_PT_PARA_EN = {v: k for k, v in BOLSA_EN_PARA_PT.items()}


# ── Mapeamento de setores ────────────────────────────────────
SETOR_PT_PARA_EN = {
    "Aeroespacial e Defesa":                    "Aerospace and Defense",
    "Companhias Aéreas":                        "Airlines",
    "Componentes Automotivos":                  "Auto Components",
    "Automóveis":                               "Automobiles",
    "Bancos":                                   "Banking",
    "Bebidas":                                  "Beverages",
    "Biotecnologia":                            "Biotechnology",
    "Construção Civil":                         "Building",
    "Químicos":                                 "Chemicals",
    "Serviços e Suprimentos Comerciais":        "Commercial Services and Supplies",
    "Comunicações":                             "Communications",
    "Construção":                               "Construction",
    "Produtos de Consumo":                      "Consumer products",
    "Distribuidores":                           "Distributors",
    "Serviços Diversificados ao Consumidor":    "Diversified Consumer Services",
    "Equipamentos Elétricos":                   "Electrical Equipment",
    "Energia":                                  "Energy",
    "Serviços Financeiros":                     "Financial Services",
    "Produtos Alimentícios":                    "Food Products",
    "Cuidados com a Saúde":                     "Health Care",
    "Saúde":                                    "Healthcare",
    "Hotéis Restaurantes e Lazer":              "Hotels Restaurants and Leisure",
    "Conglomerados Industriais":                "Industrial Conglomerates",
    "Seguros":                                  "Insurance",
    "Produtos de Lazer":                        "Leisure Products",
    "Ferramentas e Serviços de Ciências da Vida":"Life Sciences Tools and Services",
    "Logística e Transporte":                   "Logistics and Transportation",
    "Maquinário":                               "Machinery",
    "Marinha":                                  "Marine",
    "Mídia":                                    "Media",
    "Metais e Mineração":                       "Metals and Mining",
    "Embalagens":                               "Packaging",
    "Farmacêuticos":                            "Pharmaceuticals",
    "Serviços Profissionais":                   "Professional Services",
    "Imobiliário":                              "Real Estate",
    "Varejo":                                   "Retail",
    "Rodovias e Ferrovias":                     "Road and Rail",
    "Semicondutores":                           "Semiconductors",
    "Tecnologia":                               "Technology",
    "Telecomunicações":                         "Telecommunication",
    "Têxteis Vestuário e Bens de Luxo":         "Textiles Apparel and Luxury Goods",
    "Tabaco":                                   "Tobacco",
    "Empresas Comerciais e Distribuidores":     "Trading Companies and Distributors",
    "Utilidades":                               "Utilities",
}

SETOR_EN_PARA_PT = {v: k for k, v in SETOR_PT_PARA_EN.items()}

# ── Mapeamento de maturidade (level) ─────────────────────────
MATURIDADE_PT_PARA_EN = {
    "Excelente": "Excellent",
    "Alta":      "High",
    "Média":     "Medium",
    "Baixa":     "Low",
}

MATURIDADE_EN_PARA_PT = {v: k for k, v in MATURIDADE_PT_PARA_EN.items()}

# ── Mapeamento de confiabilidade (grade) ─────────────────────
CONFIABILIDADE_PT_PARA_EN = {
    "Auditada":     "auditada",    # usado apenas internamente
    "Não auditada": "nao_auditada",
}

# ── Derivação de grade a partir de maturidade + confiabilidade
# Chave: (maturidade_PT, confiabilidade_PT) → grade_EN
GRADE_DE_MATURIDADE_CONFIABILIDADE = {
    ("Excelente", "Auditada"):     "AAA",
    ("Excelente", "Não auditada"): "AA",
    ("Alta",      "Auditada"):     "A",
    ("Alta",      "Não auditada"): "BBB",
    ("Média",     "Auditada"):     "BB",
    ("Média",     "Não auditada"): "B",
    ("Baixa",     "Auditada"):     "CCC",
    ("Baixa",     "Não auditada"): "C",
}

# Inverso: grade_EN → (maturidade_PT, confiabilidade_PT)
MATURIDADE_CONFIABILIDADE_DE_GRADE = {
    v: k for k, v in GRADE_DE_MATURIDADE_CONFIABILIDADE.items()
}

# ── Mapeamento de nível de risco ─────────────────────────────
RISCO_EN_PARA_PT = {
    "Alto Risco":     "Alto Risco",      # já em PT no nosso modelo
    "Risco Moderado": "Risco Moderado",
    "Baixo Risco":    "Baixo Risco",
}

# ── Funções utilitárias ──────────────────────────────────────

def derivar_grade(maturidade_pt: str, confiabilidade_pt: str) -> str:
    """
    Deriva o grade EN a partir da combinação de maturidade e confiabilidade
    em português.

    Exemplo:
        derivar_grade("Alta", "Auditada") → "A"
        derivar_grade("Média", "Não auditada") → "B"
    """
    chave = (maturidade_pt, confiabilidade_pt)
    grade = GRADE_DE_MATURIDADE_CONFIABILIDADE.get(chave)
    if grade is None:
        raise ValueError(
            f"Combinação inválida: maturidade='{maturidade_pt}', "
            f"confiabilidade='{confiabilidade_pt}'. "
            f"Valores aceitos: {list(MATURIDADE_PT_PARA_EN.keys())} / "
            f"['Auditada', 'Não auditada']"
        )
    return grade


def decompor_grade(grade_en: str) -> tuple[str, str]:
    """
    A partir de um grade EN, retorna (maturidade_PT, confiabilidade_PT).

    Exemplo:
        decompor_grade("A")   → ("Alta", "Auditada")
        decompor_grade("BBB") → ("Alta", "Não auditada")
    """
    resultado = MATURIDADE_CONFIABILIDADE_DE_GRADE.get(grade_en)
    if resultado is None:
        raise ValueError(f"Grade desconhecido: '{grade_en}'")
    return resultado  # (maturidade_PT, confiabilidade_PT)


def formatar_cnpj(valor) -> str:
    """
    Aplica zero-padding de 14 dígitos para padronizar CNPJ/cik.
    Remove pontos, barras e hifens antes de formatar.

    Exemplo:
        formatar_cnpj(12345)        → "00000000012345"
        formatar_cnpj("12.345.678") → "00000012345678"
    """
    limpo = str(valor).replace(".", "").replace("/", "").replace("-", "").strip()
    return limpo.zfill(14)


# ── Tradução de um registro PT → EN (para o modelo) ──────────

def traduzir_entrada_para_modelo(dados_pt: dict) -> dict:
    """
    Recebe um dicionário com os campos no formato do cliente (PT)
    e retorna um dicionário pronto para o modelo de ML (EN).

    Campos esperados no dicionário de entrada:
        cnpj, sigla, nome, perfil, setor,
        faturamento, tamanho,
        confiabilidade_ambiental, maturidade_ambiental,
        confiabilidade_social, maturidade_social,
        confiabilidade_governanca, maturidade_governanca

    Campos derivados automaticamente:
        environment_grade, social_grade, governance_grade
        (a partir da combinação maturidade + confiabilidade)
    """
    d = dados_pt

    # Derivar os três grades a partir de maturidade + confiabilidade
    env_grade  = derivar_grade(d["maturidade_ambiental"],  d["confiabilidade_ambiental"])
    soc_grade  = derivar_grade(d["maturidade_social"],     d["confiabilidade_social"])
    gov_grade  = derivar_grade(d["maturidade_governanca"], d["confiabilidade_governanca"])

    return {
        "exchange":           BOLSA_PT_PARA_EN.get(d["perfil"], d["perfil"]),
        "industry":           SETOR_PT_PARA_EN.get(d["setor"], d["setor"]),
        "revenue_M":          float(d["faturamento"]),
        "employees":          int(d["tamanho"]),
        "environment_grade":  env_grade,
        "social_grade":       soc_grade,
        "governance_grade":   gov_grade,
    }


# ── Tradução de um registro EN → PT (para o dashboard/Gold) ──

def traduzir_linha_para_dashboard(linha_en: dict) -> dict:
    """
    Recebe um dicionário no formato EN (Gold interno) e retorna
    um dicionário no formato PT para o dashboard e new_companies.csv.

    Converte setor, maturidade (level) e decompõe grade em
    maturidade + confiabilidade.
    """
    d = linha_en

    # Decompor grades em maturidade + confiabilidade (PT)
    mat_amb, conf_amb = decompor_grade(d.get("environment_grade", "B"))
    mat_soc, conf_soc = decompor_grade(d.get("social_grade", "B"))
    mat_gov, conf_gov = decompor_grade(d.get("governance_grade", "B"))

    return {
        "cnpj":                      formatar_cnpj(d.get("cik", 0)),
        "sigla":                     d.get("ticker", ""),
        "nome":                      d.get("name", ""),
        "perfil":                    BOLSA_EN_PARA_PT.get(d.get("exchange", ""), d.get("exchange", "")),
        "setor":                     SETOR_EN_PARA_PT.get(d.get("industry", ""), d.get("industry", "")),
        "faturamento":               d.get("revenue_M", 0),
        "tamanho":                   d.get("employees", 0),
        "confiabilidade_ambiental":  conf_amb,
        "maturidade_ambiental":      mat_amb,
        "pontuacao_ambiental":       d.get("environment_score", 0),
        "confiabilidade_social":     conf_soc,
        "maturidade_social":         mat_soc,
        "pontuacao_social":          d.get("social_score", 0),
        "confiabilidade_governanca": conf_gov,
        "maturidade_governanca":     mat_gov,
        "pontuacao_governanca":      d.get("governance_score", 0),
        "pontuacao_total":           d.get("total_score", 0),
        "nivel_risco":               d.get("risk_level", ""),
    }


import pandas as pd

def traduzir_dataframe_para_dashboard(df_en: pd.DataFrame) -> pd.DataFrame:
    """
    Converte um DataFrame inteiro do formato EN para o formato PT
    do dashboard. Usado pelo build_gold.py.
    """
    registros = [traduzir_linha_para_dashboard(row) for row in df_en.to_dict(orient="records")]
    return pd.DataFrame(registros)

"""
src/build_gold.py
=================
Gera o arquivo data/gold/data_gold.csv a partir do Silver.

O Gold é o arquivo final que alimenta o dashboard. Por isso,
todas as colunas e valores são convertidos para o formato do
cliente (PT-BR) via translator.py.

Regras aplicadas:
  - Remove colunas redundantes: total_grade, total_level, last_processing_date
  - Calcula nivel_risco via segmentação do total_score (regra de negócio pura)
  - Converte todas as colunas e valores para PT-BR (linguagem do cliente)
  - Aplica zero-padding de 14 dígitos no campo cnpj

Uso:
  python src/build_gold.py

Executar apenas uma vez (ou quando o Silver for atualizado).
"""

import sys
from pathlib import Path

# Garante que src/ está no path para importar translator
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
from translator import traduzir_dataframe_para_dashboard, formatar_cnpj

# ── Caminhos ─────────────────────────────────────────────────
SILVER   = ROOT / "data" / "silver" / "data_silver.csv"
GOLD_DIR = ROOT / "data" / "gold"
GOLD     = GOLD_DIR / "data_gold.csv"
NEW_CO   = GOLD_DIR / "new_companies.csv"

# ── Colunas do Gold em PT-BR (ordem final) ───────────────────
GOLD_COLS_PT = [
    "cnpj", "sigla", "nome", "bolsa", "setor",
    "faturamento", "tamanho",
    "confiabilidade_ambiental", "maturidade_ambiental", "pontuacao_ambiental",
    "confiabilidade_social",    "maturidade_social",    "pontuacao_social",
    "confiabilidade_governanca","maturidade_governanca", "pontuacao_governanca",
    "pontuacao_total", "nivel_risco",
]


def calcular_nivel_risco(total_score: int) -> str:
    """Regra de negócio: segmentação do total_score em níveis de risco."""
    if total_score < 900:
        return "Alto Risco"
    elif total_score <= 1150:
        return "Risco Moderado"
    return "Baixo Risco"


def build_gold():
    print(f"Lendo Silver: {SILVER}")
    df = pd.read_csv(SILVER)
    print(f"  {len(df)} empresas carregadas | colunas: {df.shape[1]}")

    # ── Calcular nivel_risco antes de traduzir ────────────────
    df["risk_level"] = df["total_score"].apply(calcular_nivel_risco)

    # ── Traduzir DataFrame EN → PT ────────────────────────────
    df_pt = traduzir_dataframe_para_dashboard(df)

    # ── Garantir apenas as colunas do Gold, na ordem correta ──
    df_gold = df_pt[GOLD_COLS_PT].copy()

    # ── Salvar Gold ───────────────────────────────────────────
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    df_gold.to_csv(GOLD, index=False, encoding="utf-8")
    print(f"Gold salvo: {GOLD}")
    print(f"  {len(df_gold)} empresas | {df_gold.shape[1]} colunas (formato PT-BR)")

    # ── Distribuição do nivel_risco ───────────────────────────
    print("\nDistribuição nivel_risco:")
    dist = df_gold["nivel_risco"].value_counts()
    for nivel, count in dist.items():
        pct = count / len(df_gold) * 100
        print(f"  {nivel:<18} {count:>4} empresas ({pct:.1f}%)")

    # ── Criar new_companies.csv vazio (só cabeçalho) se não existir
    if not NEW_CO.exists():
        pd.DataFrame(columns=GOLD_COLS_PT).to_csv(NEW_CO, index=False, encoding="utf-8")
        print(f"\nCriado: {NEW_CO} (vazio — aguardando novas previsões)")
    else:
        n = len(pd.read_csv(NEW_CO))
        print(f"\nNew companies existente: {n} previsões acumuladas")

    print("\nBuild Gold concluído com sucesso!")


if __name__ == "__main__":
    build_gold()

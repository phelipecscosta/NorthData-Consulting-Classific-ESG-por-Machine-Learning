"""
silver_transform.py
-------------------
Script de transformação da camada Silver.
Aplica todas as correções identificadas na EDA sobre o dado bruto
da camada Bronze e salva o resultado em data/silver/.

Arquitetura : Medalhão (Bronze → Silver → Gold)
Autor       : NorthData Consulting
"""

import json
import hashlib
import re
import time
import pandas as pd
import yfinance as yf
from pathlib import Path
from datetime import datetime


# ── Configuração ──────────────────────────────────────────────────────────────
BRONZE_FILE     = Path(__file__).resolve().parents[1] / "data" / "bronze" / "data.csv"
BRONZE_SIZE     = Path(__file__).resolve().parents[1] / "data" / "bronze" / "company_size_revenue_2021.csv"
SILVER_DIR      = Path(__file__).resolve().parents[1] / "data" / "silver"
SILVER_FILE     = SILVER_DIR / "data_silver.csv"

# Ordem final das colunas na camada Silver
COLUNAS_ORDENADAS = [
    "cik", "ticker", "name", "exchange", "industry",
    "revenue_M", "employees",
    "environment_grade", "environment_level", "environment_score",
    "social_grade",      "social_level",      "social_score",
    "governance_grade",  "governance_level",  "governance_score",
    "total_grade",       "total_level",       "total_score",
    "last_processing_date"
]

# CIKs confirmados manualmente como Financial Services (SPACs)
CIKS_FINANCIAL_SERVICES = [
    1914023, 1813658, 1824884, 1841661, 1826574,
    1824013, 1824846, 1829427, 1824301
]

# Mapeamento de nomes de bolsas para siglas
EXCHANGE_MAP = {
    "NEW YORK STOCK EXCHANGE, INC." : "NYSE",
    "NASDAQ NMS - GLOBAL MARKET"    : "NASDAQ",
}
# ──────────────────────────────────────────────────────────────────────────────


def calcular_hash(filepath: Path) -> str:
    """Gera hash MD5 do arquivo para garantia de integridade."""
    md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
    return md5.hexdigest()


def registrar_metadata(filepath: Path, etapas: list) -> None:
    """Salva JSON com metadados da transformação Silver."""
    meta = {
        "arquivo"          : filepath.name,
        "origem"           : str(BRONZE_FILE),
        "data_processo"    : datetime.now().isoformat(),
        "md5_hash"         : calcular_hash(filepath),
        "etapas_aplicadas" : etapas,
    }
    meta_path = filepath.parent / "metadata_silver.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=4, ensure_ascii=False)
    print(f"  Metadados salvos em: {meta_path}")


def carregar_bronze() -> pd.DataFrame:
    """Carrega o dado bruto da camada Bronze."""
    print(f"  Carregando: {BRONZE_FILE}")
    df = pd.read_csv(BRONZE_FILE)
    print(f"  Shape Bronze: {df.shape}")
    return df


def descartar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Descarta colunas sem utilidade para modelagem ou dashboard.
    Decisão baseada na EDA: logo, weburl e currency não agregam
    valor preditivo ao projeto. Exchange é mantida para padronização
    posterior em siglas.
    """
    colunas_descartar = ["logo", "weburl", "currency"]
    df = df.drop(columns=colunas_descartar)
    print(f"  Colunas descartadas : {colunas_descartar}")
    print(f"  Shape após descarte : {df.shape}")
    return df


def reordenar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reordena as colunas conforme a ordem semântica definida para a
    camada Silver. As colunas revenue_M e employees ainda não existem
    neste ponto — são adicionadas na etapa de enriquecimento.
    A reordenação final acontece após o join.
    """
    colunas_intermediarias = [
        c for c in COLUNAS_ORDENADAS
        if c in df.columns
    ]
    df = df[colunas_intermediarias]
    print(f"  Colunas reordenadas (parcial): {len(colunas_intermediarias)} colunas")
    return df


def normalizar_setor(texto: str) -> str:
    """
    Normaliza o nome do setor corrigindo inconsistências
    identificadas na EDA — seção 3.5 do notebook.
    """
    if pd.isna(texto):
        return texto
    texto = texto.strip()
    texto = re.sub(r"[&]+",   "and", texto)
    texto = re.sub(r"[,\.]+", " ",   texto)
    texto = re.sub(r"\s+",    " ",   texto)
    return texto.strip()


def corrigir_industry(df: pd.DataFrame) -> pd.DataFrame:
    """
    Corrige inconsistências nos nomes de setores identificadas na EDA.
    Aplica normalização definitiva — diferente da temporária usada na EDA.
    """
    antes = df["industry"].nunique()
    df["industry"] = df["industry"].apply(normalizar_setor)
    depois = df["industry"].nunique()
    print(f"  Setores antes da correção : {antes}")
    print(f"  Setores após a correção   : {depois}")
    print(f"  Setores consolidados      : {antes - depois}")
    return df


def preencher_nulos_industry(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preenche nulos em industry em duas etapas:

    Etapa 1 — Imputação manual por CIK:
        9 empresas confirmadas individualmente como SPACs classificadas
        em Financial Services. Preenchimento direto sem consulta à API.

    Etapa 2 — Busca via yfinance:
        Empresas restantes sem setor buscadas pela API do Yahoo Finance
        usando o ticker como chave. Fallback para 'Unknown'.
    """
    # ── Etapa 1: imputação manual por CIK ────────────────────────────────────
    mascara_cik = df["cik"].isin(CIKS_FINANCIAL_SERVICES) & df["industry"].isnull()
    qtd_manual  = mascara_cik.sum()
    df.loc[mascara_cik, "industry"] = "Financial Services"
    print(f"  Imputação manual (CIK confirmado) : {qtd_manual} empresas → 'Financial Services'")

    # ── Etapa 2: busca via yfinance para nulos restantes ─────────────────────
    nulos_restantes = df["industry"].isnull().sum()
    print(f"  Nulos restantes para busca via API: {nulos_restantes}")

    if nulos_restantes == 0:
        print("  Nenhum nulo adicional para tratar.")
        return df

    for idx in df[df["industry"].isnull()].index:
        ticker = df.at[idx, "ticker"]
        name   = df.at[idx, "name"]
        setor  = None

        print(f"  Buscando setor para: {name} ({ticker})")

        try:
            info  = yf.Ticker(ticker).info
            setor = info.get("sector") or info.get("industry")
            if setor:
                setor = normalizar_setor(setor)
        except Exception:
            pass

        if setor:
            print(f"    Setor encontrado : {setor}")
            df.at[idx, "industry"] = setor
        else:
            print(f"    Não encontrado   → imputando 'Unknown'")
            df.at[idx, "industry"] = "Unknown"

        time.sleep(0.5)

    print(f"  Nulos restantes após todas as etapas: {df['industry'].isnull().sum()}")
    return df


def converter_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converte last_processing_date de string para datetime.
    Formato identificado na EDA: %d-%m-%Y.
    """
    df["last_processing_date"] = pd.to_datetime(
        df["last_processing_date"], format="%d-%m-%Y"
    )
    print(f"  Coluna 'last_processing_date' convertida para datetime.")
    return df


def padronizar_cik(df: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza o CIK para o formato oficial da SEC:
    inteiro de 10 dígitos preenchido com zeros à esquerda.
    Exemplo: 1234 → '0000001234'
    """
    df["cik"] = df["cik"].astype(str).str.zfill(10)
    print(f"  CIK padronizado para 10 dígitos com zero-padding.")
    return df


def padronizar_ticker(df: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza o ticker para letras maiúsculas —
    formato padrão nos mercados financeiros.
    """
    df["ticker"] = df["ticker"].str.upper()
    print(f"  Ticker padronizado para maiúsculas.")
    return df


def padronizar_exchange(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converte os nomes completos das bolsas para siglas padronizadas.
    Valores não mapeados são mantidos sem alteração.
    """
    antes = df["exchange"].unique().tolist()
    df["exchange"] = df["exchange"].map(EXCHANGE_MAP).fillna(df["exchange"])
    depois = df["exchange"].unique().tolist()
    print(f"  Exchange antes : {antes}")
    print(f"  Exchange depois: {depois}")
    return df


def enriquecer_com_tamanho(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adiciona as colunas revenue_M e employees a partir do dataset
    company_size_revenue_2021.csv, fazendo join pelo CIK.

    Empresas com valor 0 em revenue_M estão abaixo de 1M de receita.
    Todas as empresas do dataset principal possuem correspondência.
    """
    print(f"  Carregando: {BRONZE_SIZE}")
    df_size = pd.read_csv(BRONZE_SIZE)

    # Padroniza o CIK do dataset de tamanho para o mesmo formato
    df_size["cik"] = df_size["cik"].astype(str).str.zfill(10)

    # Seleciona apenas as colunas necessárias
    df_size = df_size[["cik", "revenue_2021_millions_usd", "employees_2021"]]
    df_size = df_size.rename(columns={
        "revenue_2021_millions_usd" : "revenue_M",
        "employees_2021"            : "employees"
    })

    # Join pelo CIK
    antes  = len(df)
    df     = df.merge(df_size, on="cik", how="left")
    depois = len(df)

    sem_match = df["revenue_M"].isnull().sum()
    print(f"  Registros antes do join  : {antes}")
    print(f"  Registros após o join    : {depois}")
    print(f"  Empresas sem correspondência: {sem_match}")

    return df


def aplicar_ordem_final(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica a ordem final das colunas após todas as transformações,
    incluindo as colunas enriquecidas revenue_M e employees.
    """
    df = df[COLUNAS_ORDENADAS]
    print(f"  Ordem final aplicada: {len(COLUNAS_ORDENADAS)} colunas")
    return df


def salvar_silver(df: pd.DataFrame) -> None:
    """Salva o dataframe transformado na camada Silver."""
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(SILVER_FILE, index=False, encoding="utf-8")
    print(f"  Arquivo salvo em : {SILVER_FILE}")
    print(f"  Shape Silver     : {df.shape}")


def transformar() -> None:
    """Orquestra todo o pipeline de transformação Silver."""
    print("=" * 60)
    print("Iniciando transformação — camada Silver")
    print("=" * 60)

    etapas = []

    # 1. Carrega Bronze
    df = carregar_bronze()

    # 2. Descarta colunas sem utilidade
    print("\n[01/12] Descartando colunas...")
    df = descartar_colunas(df)
    etapas.append("Descarte de colunas: logo, weburl, currency")

    # 3. Reordena colunas (parcial — sem revenue_M e employees ainda)
    print("\n[02/12] Reordenando colunas (parcial)...")
    df = reordenar_colunas(df)
    etapas.append("Reordenamento parcial de colunas")

    # 4. Corrige inconsistências em industry
    print("\n[03/12] Corrigindo nomes de setores...")
    df = corrigir_industry(df)
    etapas.append("Normalização de nomes de setores em industry (47 → 43)")

    # 5. Preenche nulos em industry
    print("\n[04/12] Preenchendo nulos em industry...")
    df = preencher_nulos_industry(df)
    etapas.append(
        "Preenchimento de nulos em industry: "
        "9 via imputação manual por CIK (Financial Services) + busca via yfinance"
    )

    # 6. Converte data
    print("\n[05/12] Convertendo last_processing_date...")
    df = converter_data(df)
    etapas.append("Conversão de last_processing_date para datetime (formato %d-%m-%Y)")

    # 7. Padroniza CIK
    print("\n[06/12] Padronizando CIK...")
    df = padronizar_cik(df)
    etapas.append("CIK padronizado para 10 dígitos com zero-padding (padrão SEC)")

    # 8. Padroniza ticker
    print("\n[07/12] Padronizando ticker...")
    df = padronizar_ticker(df)
    etapas.append("Ticker padronizado para letras maiúsculas")

    # 9. Padroniza exchange
    print("\n[08/12] Padronizando exchange...")
    df = padronizar_exchange(df)
    etapas.append("Exchange convertida para siglas: NYSE e NASDAQ")

    # 10. Enriquece com receita e funcionários
    print("\n[09/12] Enriquecendo com revenue_M e employees...")
    df = enriquecer_com_tamanho(df)
    etapas.append(
        "Enriquecimento com company_size_revenue_2021.csv: "
        "colunas revenue_M e employees adicionadas via join por CIK"
    )

    # 11. Aplica ordem final das colunas
    print("\n[10/12] Aplicando ordem final das colunas...")
    df = aplicar_ordem_final(df)
    etapas.append("Ordem final das colunas aplicada")

    # 12. Salva Silver
    print("\n[11/12] Salvando camada Silver...")
    salvar_silver(df)
    etapas.append("Exportação para data/silver/data_silver.csv")

    # 13. Registra metadados
    print("\n[12/12] Registrando metadados...")
    registrar_metadata(SILVER_FILE, etapas)

    print("\n" + "=" * 60)
    print("Transformação concluída! Camada Silver pronta.")
    print("=" * 60)


if __name__ == "__main__":
    transformar()
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


# ── Configuração ──────────────────────────────────────────────
BRONZE_FILE = Path(__file__).resolve().parents[1] / "data" / "bronze" / "data.csv"
SILVER_DIR  = Path(__file__).resolve().parents[1] / "data" / "silver"
SILVER_FILE = SILVER_DIR / "data_silver.csv"
# ──────────────────────────────────────────────────────────────


def calcular_hash(filepath: Path) -> str:
    """Gera hash MD5 do arquivo para garantir integridade."""
    md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
    return md5.hexdigest()


def registrar_metadata(filepath: Path, etapas: list) -> None:
    """Salva JSON com metadados da transformação Silver."""
    meta = {
        "arquivo"        : filepath.name,
        "origem"         : str(BRONZE_FILE),
        "data_processo"  : datetime.now().isoformat(),
        "md5_hash"       : calcular_hash(filepath),
        "etapas_aplicadas": etapas,
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
    Decisão baseada na EDA: logo, weburl, currency e exchange
    não agregam valor preditivo ao projeto.
    """
    colunas_descartar = ["logo", "weburl", "currency", "exchange"]
    df = df.drop(columns=colunas_descartar)
    print(f"  Colunas descartadas: {colunas_descartar}")
    print(f"  Shape após descarte: {df.shape}")
    return df


def normalizar_setor(texto: str) -> str:
    """
    Normaliza o nome do setor corrigindo inconsistências
    identificadas na EDA — seção 3.5.
    """
    if pd.isna(texto):
        return texto
    texto = texto.strip()
    texto = re.sub(r"[&]+", "and", texto)
    texto = re.sub(r"[,\.]+", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
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


def buscar_setor_yfinance(ticker: str) -> str:
    """
    Busca o setor de uma empresa via API do Yahoo Finance pelo ticker.
    Retorna o setor encontrado ou None se não encontrar.
    """
    try:
        info = yf.Ticker(ticker).info
        setor = info.get("sector") or info.get("industry")
        if setor:
            return normalizar_setor(setor)
    except Exception:
        pass
    return None


def preencher_nulos_industry(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preenche nulos em industry buscando o setor via yfinance.
    Estratégia em cascata: ticker → name → cik → 'Unknown'.
    """
    nulos = df["industry"].isnull()
    total_nulos = nulos.sum()
    print(f"  Empresas sem setor: {total_nulos}")

    if total_nulos == 0:
        print("  Nenhum nulo para tratar.")
        return df

    for idx in df[nulos].index:
        ticker = df.at[idx, "ticker"]
        name   = df.at[idx, "name"]
        setor  = None

        # Tentativa 1 — pelo ticker
        print(f"  Buscando setor para: {name} ({ticker})")
        setor = buscar_setor_yfinance(ticker)

        # Tentativa 2 — pelo name (se ticker falhou)
        if not setor:
            setor = buscar_setor_yfinance(name)

        # Resultado
        if setor:
            print(f"    Setor encontrado : {setor}")
            df.at[idx, "industry"] = setor
        else:
            print(f"    Setor não encontrado — imputando 'Unknown'")
            df.at[idx, "industry"] = "Unknown"

        time.sleep(0.5)  # respeita o rate limit da API

    nulos_restantes = df["industry"].isnull().sum()
    print(f"  Nulos restantes após busca: {nulos_restantes}")
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


def salvar_silver(df: pd.DataFrame) -> None:
    """Salva o dataframe transformado na camada Silver."""
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(SILVER_FILE, index=False, encoding="utf-8")
    print(f"  Arquivo salvo em: {SILVER_FILE}")
    print(f"  Shape Silver    : {df.shape}")


def transformar() -> None:
    """Orquestra todo o pipeline de transformação Silver."""
    print("=" * 55)
    print("Iniciando transformação — camada Silver")
    print("=" * 55)

    etapas = []

    # 1. Carrega Bronze
    df = carregar_bronze()

    # 2. Descarta colunas sem utilidade
    print("\n[1/5] Descartando colunas...")
    df = descartar_colunas(df)
    etapas.append("Descarte de colunas: logo, weburl, currency, exchange")

    # 3. Corrige inconsistências em industry
    print("\n[2/5] Corrigindo nomes de setores...")
    df = corrigir_industry(df)
    etapas.append("Normalização de nomes de setores em industry")

    # 4. Preenche nulos em industry
    print("\n[3/5] Preenchendo nulos em industry...")
    df = preencher_nulos_industry(df)
    etapas.append("Preenchimento de nulos em industry via yfinance")

    # 5. Converte data
    print("\n[4/5] Convertendo last_processing_date...")
    df = converter_data(df)
    etapas.append("Conversão de last_processing_date para datetime")

    # 6. Salva Silver
    print("\n[5/5] Salvando camada Silver...")
    salvar_silver(df)
    etapas.append("Exportação para data/silver/data_silver.csv")

    # 7. Registra metadados
    registrar_metadata(SILVER_FILE, etapas)

    print("\n" + "=" * 55)
    print("Transformação concluída! Camada Silver pronta.")
    print("=" * 55)


if __name__ == "__main__":
    transformar()
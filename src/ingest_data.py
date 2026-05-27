"""
ingest_data.py
--------------
Script de ingestão da camada Bronze.
Baixa o dataset diretamente da API do Kaggle,
extrai e armazena em data/bronze/ com registro de metadados.

Arquitetura : Medalhão (Bronze → Silver → Gold)
Fonte       : https://www.kaggle.com/datasets/alistairking/public-company-esg-ratings-dataset
"""

import os
import json
import hashlib
import zipfile
import shutil
from pathlib import Path
from datetime import datetime


# ── Configuração ──────────────────────────────────────────────
KAGGLE_DATASET = "alistairking/public-company-esg-ratings-dataset"
BRONZE_DIR     = Path(__file__).resolve().parents[1] / "data" / "bronze"
DOWNLOAD_DIR   = Path(__file__).resolve().parents[1] / "data" / "_temp"
# ──────────────────────────────────────────────────────────────


def calcular_hash(filepath: Path) -> str:
    """Gera hash MD5 do arquivo para garantir integridade."""
    md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
    return md5.hexdigest()


def registrar_metadata(csv_path: Path, file_hash: str) -> None:
    """Salva JSON com metadados da ingestão para rastreabilidade."""
    meta = {
        "arquivo"        : csv_path.name,
        "fonte_original" : f"https://www.kaggle.com/datasets/{KAGGLE_DATASET}",
        "data_ingestao"  : datetime.now().isoformat(),
        "md5_hash"       : file_hash,
        "metodo"         : "Kaggle API",
    }
    meta_path = csv_path.parent / "metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=4, ensure_ascii=False)
    print(f"  Metadados salvos em: {meta_path}")


def baixar_dataset() -> Path:
    """Baixa o dataset do Kaggle e retorna o caminho do .zip."""
    import kaggle

    print(f"  Conectando à API do Kaggle...")
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    kaggle.api.authenticate()
    kaggle.api.dataset_download_files(
        dataset = KAGGLE_DATASET,
        path    = str(DOWNLOAD_DIR),
        unzip   = False,
    )

    zips = list(DOWNLOAD_DIR.glob("*.zip"))
    if not zips:
        raise FileNotFoundError("Download falhou: nenhum arquivo .zip encontrado.")

    print(f"  Arquivo baixado: {zips[0].name}")
    return zips[0]
def extrair_csv(zip_path: Path) -> Path:
    """Extrai o CSV do .zip e move para data/bronze/."""
    print(f"  Extraindo arquivo do Zip...")

    with zipfile.ZipFile(zip_path, "r") as z:
        arquivos = z.namelist()
        csvs = [f for f in arquivos if f.endswith(".csv")]

        if not csvs:
            raise FileNotFoundError("Nenhum arquivo .csv encontrado dentro do .zip.")

        for csv_nome in csvs:
            z.extract(csv_nome, DOWNLOAD_DIR)
            origem  = DOWNLOAD_DIR / csv_nome
            destino = BRONZE_DIR  / csv_nome

            BRONZE_DIR.mkdir(parents=True, exist_ok=True)
            shutil.move(str(origem), str(destino))
            print(f"  CSV movido para: {destino}")

    return BRONZE_DIR / csvs[0]


def limpar_temp() -> None:
    """Remove a pasta temporária de download."""
    if DOWNLOAD_DIR.exists():
        shutil.rmtree(DOWNLOAD_DIR)
        print(f"  Pasta temporária removida.")


def ingerir() -> None:
    """Orquestra todo o pipeline de ingestão."""
    print("=" * 55)
    print("Iniciando ingestão — camada Bronze")
    print(f"   Dataset : {KAGGLE_DATASET}")
    print("=" * 55)

    try:
        zip_path  = baixar_dataset()
        csv_path  = extrair_csv(zip_path)
        file_hash = calcular_hash(csv_path)
        print(f"  MD5: {file_hash}")
        registrar_metadata(csv_path, file_hash)

    finally:
        limpar_temp()

    print("=" * 55)
    print("Ingestão concluída para a camada Bronze!")
    print("=" * 55)


if __name__ == "__main__":
    ingerir()
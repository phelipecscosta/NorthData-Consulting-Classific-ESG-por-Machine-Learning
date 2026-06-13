import pandas as pd

arquivo = "data/template/modelo_cadastro_novas_empresas (1).xlsx"

# Leitura crua — sem nenhum ajuste
df_raw = pd.read_excel(arquivo, sheet_name="Cadastro", dtype=str, header=None)

print("=== Primeiras 4 linhas brutas ===")
print(df_raw.head(4).to_string())
print()
print("=== Shape:", df_raw.shape)
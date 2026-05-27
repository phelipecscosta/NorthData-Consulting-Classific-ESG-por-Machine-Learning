# Dicionário de Dados
## Projeto: Classificação ESG por Machine Learning
**Empresa:** NorthData Consulting  
**Dataset:** Public Company ESG Ratings  
**Fonte:** https://www.kaggle.com/datasets/alistairking/public-company-esg-ratings-dataset  
**Última atualização:** 27/05/2026

---

## Grupos de Colunas

O dataset está organizado em 4 grupos naturais e uma coluna de controle:

| Grupo | Colunas | Descrição |
|---|---|---|
| Identificação | 6 | Dados cadastrais da empresa |
| Links | 2 | URLs de logo e site |
| Scores | 4 | Pontuações numéricas ESG |
| Grades e Níveis | 8 | Classificações categóricas ESG |
| Controle | 1 | Data de processamento |

---

## Dicionário

### Grupo 1 — Identificação da Empresa

| # | Nome da Coluna (Feature) | Descrição / Significado | Tipo de Dado | Formato / Padrão | Domínio / Valores Permitidos |
|---|---|---|---|---|---|
| 1 | `ticker` | Código de negociação da empresa na bolsa de valores. Identificador único no mercado financeiro. | `str` | Letras maiúsculas | Ex: `AAPL`, `GOOGL`, `MSFT` |
| 2 | `name` | Nome completo oficial da empresa conforme registrado na bolsa. | `str` | Texto livre | Ex: `Apple Inc.`, `Google LLC` |
| 3 | `currency` | Moeda utilizada nas negociações da empresa na bolsa. | `str` | Código ISO 4217 (3 letras) | Ex: `USD`, `EUR`, `BRL` |
| 4 | `exchange` | Bolsa de valores onde as ações da empresa são negociadas. | `str` | Texto livre / sigla | Ex: `NASDAQ`, `NYSE`, `LSE` |
| 5 | `industry` | Setor ou segmento de mercado em que a empresa atua. | `str` | Texto livre | Ex: `Technology`, `Healthcare`, `Energy` |
| 6 | `cik` | Central Index Key — código de registro único da empresa junto à SEC (Securities and Exchange Commission), regulador do mercado americano. | `int64` | Número inteiro positivo | Valores inteiros positivos atribuídos pela SEC |

---

### Grupo 2 — Links

| # | Nome da Coluna (Feature) | Descrição / Significado | Tipo de Dado | Formato / Padrão | Domínio / Valores Permitidos |
|---|---|---|---|---|---|
| 7 | `logo` | URL da imagem do logotipo oficial da empresa. | `str` | URL válida (`https://...`) | Endereço web válido ou nulo |
| 8 | `weburl` | URL do site oficial da empresa. | `str` | URL válida (`https://...`) | Endereço web válido ou nulo |

> **Observação:** estas colunas não serão utilizadas na modelagem de Machine Learning. Podem ser úteis para exibição no dashboard.

---

### Grupo 3 — Scores Numéricos ESG

Pontuações numéricas brutas atribuídas a cada dimensão ESG. São as principais **features quantitativas** do dataset.

| # | Nome da Coluna (Feature) | Descrição / Significado | Tipo de Dado | Formato / Padrão | Domínio / Valores Permitidos |
|---|---|---|---|---|---|
| 9 | `environment_score` | Pontuação numérica de desempenho ambiental da empresa. Avalia práticas como gestão de carbono, uso de energia, resíduos e biodiversidade. | `int64` | Número inteiro | Valores positivos — quanto maior, melhor |
| 10 | `social_score` | Pontuação numérica de desempenho social. Avalia práticas como relações trabalhistas, diversidade, saúde e segurança, e impacto na comunidade. | `int64` | Número inteiro | Valores positivos — quanto maior, melhor |
| 11 | `governance_score` | Pontuação numérica de governança corporativa. Avalia transparência, estrutura de conselho, ética e conformidade regulatória. | `int64` | Número inteiro | Valores positivos — quanto maior, melhor |
| 12 | `total_score` | Pontuação ESG total da empresa. Composição dos três scores anteriores. | `int64` | Número inteiro | Valores positivos — soma dos scores E, S e G |

> **Relação entre colunas:** `total_score` = `environment_score` + `social_score` + `governance_score`. Verificar essa consistência .

---

### Grupo 4 — Grades e Níveis ESG

Classificações categóricas derivadas dos scores numéricos. Representam a mesma informação dos scores, porém de forma qualitativa e mais interpretável para o negócio.

| # | Nome da Coluna (Feature) | Descrição / Significado | Tipo de Dado | Formato / Padrão | Domínio / Valores Permitidos |
|---|---|---|---|---|---|
| 13 | `environment_grade` | Nota de desempenho ambiental em formato de letra. | `str` | Letra única ou com modificador | `A`, `A-`, `B`, `B-`, `C`, `C-`, `D`, `D-` |
| 14 | `environment_level` | Classificação textual do nível ambiental correspondente ao grade. | `str` | Texto em inglês | `Leader`, `Average`, `Laggard` |
| 15 | `social_grade` | Nota de desempenho social em formato de letra. | `str` | Letra única ou com modificador | `A`, `A-`, `B`, `B-`, `C`, `C-`, `D`, `D-` |
| 16 | `social_level` | Classificação textual do nível social correspondente ao grade. | `str` | Texto em inglês | `Leader`, `Average`, `Laggard` |
| 17 | `governance_grade` | Nota de desempenho de governança em formato de letra. | `str` | Letra única ou com modificador | `A`, `A-`, `B`, `B-`, `C`, `C-`, `D`, `D-` |
| 18 | `governance_level` | Classificação textual do nível de governança correspondente ao grade. | `str` | Texto em inglês | `Leader`, `Average`, `Laggard` |
| 19 | `total_grade` | Nota ESG geral da empresa em formato de letra. Derivada do `total_score`. | `str` | Letra única ou com modificador | `A`, `A-`, `B`, `B-`, `C`, `C-`, `D`, `D-` |
| 20 | `total_level` | Classificação textual do nível ESG geral correspondente ao grade total. | `str` | Texto em inglês | `Leader`, `Average`, `Laggard` |

> **Redundância intencional:** grades e levels são derivados dos scores. Na modelagem, evitar usar scores e grades simultaneamente como features para não introduzir **data leakage** (vazamento de informação).

---

### Coluna de Controle

| # | Nome da Coluna (Feature) | Descrição / Significado | Tipo de Dado | Formato / Padrão | Domínio / Valores Permitidos |
|---|---|---|---|---|---|
| 21 | `last_processing_date` | Data em que os dados da empresa foram processados/atualizados pela última vez na fonte. | `str` | `YYYY-MM-DD` | Datas válidas no formato ISO 8601 |

> **Nota:** esta coluna deve ser convertida para o tipo `datetime` durante o pré-processamento (camada Silver).

---

## Glossário ESG

| Termo | Significado |
|---|---|
| **ESG** | Environmental, Social and Governance — critérios usados para avaliar práticas sustentáveis e éticas de empresas |
| **Score** | Pontuação numérica bruta de desempenho |
| **Grade** | Nota em formato de letra derivada do score (similar a notas escolares) |
| **Level** | Classificação qualitativa: Leader (líder), Average (mediano), Laggard (retardatário) |
| **Leader** | Empresa com desempenho ESG acima da média do mercado |
| **Average** | Empresa com desempenho ESG dentro da média do mercado |
| **Laggard** | Empresa com desempenho ESG abaixo da média do mercado |
| **SEC** | Securities and Exchange Commission — regulador do mercado de capitais dos EUA |
| **Ticker** | Código de identificação de uma ação na bolsa de valores |
| **CIK** | Central Index Key — identificador único de empresas registradas na SEC |

---

## Observações Técnicas para Modelagem

**1. Colunas a descartar:** `logo` e `weburl` não agregam valor preditivo
**2. Redundância:** scores e grades representam a mesma informação em formatos diferentes — usar apenas um grupo como feature
**3. Target sugerido:** `total_level` para classificação (Leader / Average / Laggard) ou `total_score` para regressão
**4. Conversão necessária:** `last_processing_date` de `str` para `datetime`
**5. Encoding necessário:** colunas categóricas (`industry`, `exchange`, `grades`, `levels`) precisarão de encoding antes da modelagem

# NorthData-Consulting-Classificação-ESG-por-Machine-Learning
Projeto realizado em contexto acadêmico para a disciplina Machine Learning I (BD017) e vinculado à disciplina Projetos III, da turma 2026.1, terceiro período, do curso de Banco de Dados e IA do CESAR School.

**Pessoa responsável:** Phelipe C. S. Costa  

**Disciplinas envolvidas:** Machine Learning I (disciplina alvo) e Projetos III  

**Instituição de ensino:** CESAR SCHOOL  

# Instruções de compilação e execução:

## Preparando o ambiente

### 1. Extrair o projeto

Após baixar o arquivo `.zip`, extraia em um diretório de sua preferência.  
Exemplo:
```
D:\Projetos\NorthData-Consulting-Classific-ESG-por-Machine-Learning
```

---

### 2. VS Code: Abra o terminal na raiz do projeto

No **VS Code**: abra a pasta do projeto e use o atalho `` Ctrl+` `` para abrir o terminal integrado.

Confirme que você está na raiz do projeto — o terminal deve mostrar algo como:
```
D:\Projetos\NorthData-Consulting-Classific-ESG-por-Machine-Learning>
```
*Caso não esteja, digite `cd` seguido do respectivo diretório*

---

### 3. Crie o ambiente virtual

*=> Essencial para isolar as dependências e evitar conflito entre bibliotecas*

Digite no terminal

```
python -m venv venv
```

Isso criará uma pasta `venv/` na raiz do projeto com um Python isolado exclusivo para este projeto.

---

### 4. Ative o ambiente virtual

**Windows:**

Digite no terminal:
```
venv\Scripts\activate
```
***Obs.:*** É comum que a ativação do venv seja negada pela política de segurança do Windows. Para contornar, executar os seguintes comandos via terminal no VS Code:

```
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

Se o ambiente estiver de fato ativo, terminal irá exibir <span style="color:green;">(venv)</span>  no início da linha:

```
(venv) D:\Projetos\NorthData-Consulting-...>
```

---

### 5. Instale as dependências

Com o ambiente venv ativo, instale todas as bibliotecas necessárias de uma só vez:

```
pip install -r requirements.txt
```

---

### 6. Configure o interpretador Python no VS Code

1. Pressione `Ctrl+Shift+P`
2. Digite **Python: Select Interpreter**
3. Selecione a opção que contém `venv` no caminho

Exemplo do caminho esperado:
```
.\venv\Scripts\python.exe
```

---

### 7. Verifique a instalação

```
python -c "import pandas; import numpy; print('Ambiente OK!')"
```

Se aparecer `Ambiente OK!` no terminal, está pronto.

---

### 8. Estrutura do projeto

```
NorthData-Consulting-Classific-ESG-por-Machine-Learning/
│
├── data/
│   ├── bronze/       # Dado bruto original (nunca modificado)
│   ├── silver/       # Dado limpo e tratado
│   └── gold/         # Dado agregado para ML e BI
│
├── docs/             # Relatórios e documentação formal
├── notebooks/        # EDA e experimentos
├── src/              # Código reutilizável
├── app/              # Dashboard
├── mlruns/           # Experimentos MLflow
├── venv/             # Ambiente virtual (não versionar)
├── Dockerfile
├── requirements.txt
└── README.md
```

> **LEMBRE-SE:** A pasta venv não é baixada no pacote, mas sim criada posteriormente, conforme explicado nos passos 3 e 4 acima.

## FASE I - Extraindo dos Dados

Para extrais os dados via scrip, você precisa criar e configurar sua chave de acesso à API do Kaggle-

### Passo 1 — Gere sua chave de API no Kaggle

1. Acesse [kaggle.com](https://www.kaggle.com) no seu navegador e faça login na sua conta

2. Clique na sua **foto de perfil** no canto superior direito da tela

3. No menu que aparecer, clique em **Settings**

4. Na página de configurações, role a página para baixo até encontrar a seção **API**

5. Clique no botão **"Create New Token"**

*=> Será baixado o arquivo chamado `kaggle.json` para a sua pasta de Downloads*

> **Atenção:** esse arquivo contém sua chave secreta de acesso. Nunca compartilhe.

---

### Passo 2 — Onde e como guardar a sua chave

O Kaggle espera encontrar o `kaggle.json` em uma pasta específica do Windows.  
Siga os passos abaixo:

**2.1 — Abra o Explorador de Arquivos** (`Win + E`)

**2.2 — Navegue até a pasta do seu usuário:**
```
C:\Users\SeuUsuario\
```
> Substitua `SeuUsuario` pelo nome do seu usuário no Windows.  
> Exemplo: `C:\Users\Fulano\`

**2.3 — Verifique se a pasta `.kaggle` já existe**

- Se **existir**: entre na pasta e pule para o passo 2.5
- Se **não existir**: siga o passo 2.4

**2.4 — Crie a pasta `.kaggle`**

Clique com o botão direito em um espaço vazio da pasta → **Novo** → **Pasta**  
Nomeie como `.kaggle` (com o ponto no início) e pressione `Enter`

> O Windows pode negar o ponto no início do nome.  
> Se isso acontecer, crie pelo terminal com o comando:
> ```
> mkdir C:\Users\SeuUsuario\.kaggle
> ```

**2.5 — Mova o `kaggle.json` para dentro da pasta `.kaggle`**

Vá até sua pasta de **Downloads**, localize o arquivo `kaggle.json`  
e mova-o para:
```
C:\Users\SeuUsuario\.kaggle\kaggle.json
```

**Resultado esperado:**
```
C:\Users\SeuUsuario\
└── .kaggle\
    └── kaggle.json   ← arquivo aqui
```

---

No terminal, execute o script de ingestão:

```
python src/ingest_data.py
```

## FASE II - Transformando os Dados para Silver

No terminal, execute o script de transformação silver:

```
 python src/silver_transform.py
```

## FASE III - Transformando os Dados para Gold (necessário na primeira vez)
python src/build_gold.py

## FASE IV Iniciar o dashboard
```
streamlit run app/Home.py
```

## FASE V - Rodar com Docker

```bash
# 1. Construir a imagem
docker build -t esg-dashboard .

# 2. Rodar o container
docker run -p 8501:8501 esg-dashboard

# 3. Acessar no browser
# http://localhost:8501
```

## Fluxo do tradutor

```
Dataset cliente (PT-BR)
    → src/translator.py → entrada EN → modelo ML → scores EN
        → src/translator.py → resultado PT-BR
            → data/gold/new_companies.csv → dashboard PT-BR


## Modelos MLflow

Os modelos precisam estar disponíveis no diretório `mlruns/`.
Os run_ids configurados em `app/pages/04_previsao.py` devem existir.
Se os run_ids mudarem, atualizar o dicionário `RUN_IDS` no arquivo.




# Nosso site
**Google site:** https://sites.google.com/cesar.school/projetos3-edenred *(em revisão)*

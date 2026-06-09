# ============================================================
# Dockerfile — ESG Risk Dashboard (NorthData Consulting)
# ============================================================
# Aqui estarão as instruções o Docker executar em ordem, para criar uma "imagem" — um snapshot do ambiente da aplicação, com Python, bibliotecas e código.

# Escolha da imagem base ───────────────────────────
# python:3.11-slim é a imagem oficial do Python, versão "slim" (sem pacotes desnecessários, o que mantém o container leve).
FROM python:3.11-slim

# ── LABEL: metadados opcionais da imagem ─────────────────────
LABEL maintainer="NorthData Consulting"
LABEL description="ESG Risk Dashboard — Edenred · Streamlit + MLflow"

# ── WORKDIR: define o diretório de trabalho dentro do container
# Todos os comandos seguintes serão executados nesta pasta.
WORKDIR /app

# ── COPY requirements.txt primeiro (boa prática de cache) ────
# O Docker tem um sistema de cache por camadas. Se copiarmos o
# requirements.txt antes do código, as dependências só são
# reinstaladas quando o requirements.txt mudar — não a cada
# mudança no código Python. Isso acelera muito o build.
COPY requirements.txt .

# ── RUN: instala as dependências ─────────────────────────────
# --no-cache-dir: não salva cache local do pip (economiza espaço)
# --upgrade pip: garante pip atualizado antes de instalar
RUN pip install --upgrade pip --no-cache-dir \
 && pip install --no-cache-dir -r requirements.txt

# ── COPY: copia o resto do projeto para dentro do container ──
# O ponto "." copia tudo do diretório atual (na sua máquina)
# para o WORKDIR (/app) dentro do container.
COPY . .

# ── RUN: gera o arquivo Gold de base dentro do container ─────
# O build_gold.py cria data/gold/data_gold.csv
# Faz-se isso durante o build para que o container já inicie
# com os dados prontos.
RUN python src/build_gold.py

# ── EXPOSE: documenta a porta que a aplicação usa ────────────
# Isso NÃO abre a porta — é só documentação. A porta é aberta
# no docker run com -p 8501:8501.
EXPOSE 8501

# ── HEALTHCHECK: Docker verifica se a app está viva ──────────
# A cada 30s, tenta acessar o endpoint de health do Streamlit.
# Se falhar 3 vezes seguidas, o container é marcado como "unhealthy".
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# ── CMD: comando executado quando o container inicia ─────────
# Diferente do RUN (que roda durante o build), o CMD roda
# quando o container está vivo e recebendo requests.
#
# --server.port: porta interna do container
# --server.address: escuta em todas as interfaces (obrigatório no Docker)
# --server.headless: desativa aviso de "abrir browser" (não há browser no container)
CMD ["streamlit", "run", "app/Home.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]

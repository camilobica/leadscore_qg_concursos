# Usa uma imagem leve do Python
FROM python:3.10-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia todos os arquivos do projeto (inclusive secrets/, dados/, api/)
COPY ./api /app/api
COPY ./dados /app/dados
COPY requirements.txt /app

# Instala as dependências a partir do requirements.txt da raiz
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta da API
EXPOSE 8000

# Comando para iniciar a API FastAPI
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

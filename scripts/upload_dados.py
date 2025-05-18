import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis do .env que está na pasta secrets/
dotenv_path = Path(__file__).resolve().parent.parent / "secrets" / ".env"
load_dotenv(dotenv_path)

API_URL = os.getenv("API_PARQUET_URL") 
API_TOKEN = os.getenv("API_TOKEN")

# Caminho da pasta com os arquivos .parquet
parquet_dir = Path(__file__).resolve().parent.parent / "dados"

def upload_parquet(nome_arquivo):
    file_path = parquet_dir / nome_arquivo
    if not file_path.exists():
        print(f"❌ Arquivo não encontrado: {file_path}")
        return

    url = f"{API_URL}/dados/{nome_arquivo}"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}

    try:
        with open(file_path, "rb") as f:
            response = requests.put(url, headers=headers, files={"file": (nome_arquivo, f, "application/octet-stream")})

        if response.status_code == 200:
            print(f"✅ Upload bem-sucedido: {nome_arquivo}")
        else:
            print(f"❌ Falha no upload de {nome_arquivo}: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ Erro ao tentar enviar {nome_arquivo}: {e}")

# Subir os arquivos principais
upload_parquet("leads_leadscore.parquet")
upload_parquet("alunos_leadscore.parquet")

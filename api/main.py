from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from dotenv import load_dotenv
import os

# Caminho seguro para .env
dotenv_path = Path(__file__).resolve().parent.parent / "secrets" / ".env"
load_dotenv(dotenv_path)

app = FastAPI()

# Caminho dos dados
base_path = Path(__file__).resolve().parent.parent / "dados"
API_TOKEN = os.getenv("API_TOKEN")

def verificar_token(authorization: str):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token ausente ou inválido.")
    token = authorization.split(" ")[1]
    if token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Token incorreto.")

@app.get("/dados/{filename}")
def servir_parquet(filename: str, authorization: str = Header(None)):
    verificar_token(authorization)

    file_path = base_path / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")

    return FileResponse(file_path, media_type="application/octet-stream")

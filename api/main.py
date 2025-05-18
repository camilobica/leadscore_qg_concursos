from fastapi import FastAPI, Header, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pathlib import Path
from dotenv import load_dotenv
import os

# === Carrega variáveis de ambiente ===
dotenv_path = Path(__file__).resolve().parent.parent / "secrets" / ".env"
load_dotenv(dotenv_path)

app = FastAPI()

# === Diretório onde os .parquet estão armazenados ===
base_path = Path(__file__).resolve().parent.parent / "dados"
API_TOKEN = os.getenv("API_TOKEN")

# === Autenticação via Header Authorization ===
def verificar_token(authorization: str):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token ausente ou inválido.")
    token = authorization.split(" ")[1]
    if token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Token incorreto.")

# === Endpoint GET para servir os arquivos ===
@app.get("/dados/{filename}")
def servir_parquet(filename: str, authorization: str = Header(None)):
    verificar_token(authorization)

    file_path = base_path / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")

    return FileResponse(file_path, media_type="application/octet-stream")

# === Endpoint PUT para sobrescrever ou salvar novos arquivos ===
@app.put("/dados/{filename}")
async def upload_parquet(filename: str, file: UploadFile = File(...), authorization: str = Header(None)):
    verificar_token(authorization)

    file_path = base_path / filename
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar o arquivo: {e}")

    return {"detail": f"{filename} salvo com sucesso."}

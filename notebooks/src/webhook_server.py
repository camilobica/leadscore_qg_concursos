from fastapi import FastAPI, Request
import json
import pandas as pd
import os
from datetime import datetime
from pathlib import Path

app = FastAPI()

# Caminho absoluto para o arquivo de leads
caminho_arquivo = Path("C:/Users/Camilo_Bica/data_science/consultoria/portal_vhe/dados/leads_l3-25.csv")

# Garante que a pasta exista
caminho_arquivo.parent.mkdir(parents=True, exist_ok=True)

@app.post("/webhook")
async def receber_webhook(request: Request):
    try:
        payload = await request.json()
    except Exception as e:
        print(f"⚠️ Erro ao ler JSON: {e}")
        payload = {}

    print(f"📬 Novo webhook recebido: {datetime.now()}")
    print(json.dumps(payload, indent=2))

    if payload:  # Só salva se tiver dados
        df = pd.DataFrame([payload])

        if caminho_arquivo.exists():
            df.to_csv(caminho_arquivo, mode='a', header=False, index=False)
        else:
            df.to_csv(caminho_arquivo, index=False)

    return {"status": "ok"}

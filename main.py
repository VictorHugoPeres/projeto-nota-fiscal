"""Aplicação Principal FastAPI - Processamento de Notas Fiscais com Agentes de IA.

Disciplina: ESW424 - Prática de Engenharia de Software (UniRV)
Etapa 1: Processador de PDF utilizando Agente de IA para extração e classificação de despesas.
"""

import os
import shutil
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Importação estrita da arquitetura de agentes conforme especificado em aula
from agents.agent1.manipulacao_dados import Agent1

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "uploads"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Assegura existência dos diretórios
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Sistema de Extração e Classificação de Notas Fiscais",
    description="ESW424 - Prática de Engenharia de Software | UniRV",
    version="1.0.0"
)

# Configuração de CORS para máxima flexibilidade
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montagem de arquivos estáticos e templates Jinja2
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Instância global do Agente 1 (conforme modelo A2A dos slides)
agent1 = Agent1()


@app.get("/", response_class=HTMLResponse)
async def pagina_inicial(request: Request):
    """Renderiza a interface Web principal (conforme FIGURA 1 e FIGURA 2 do documento)."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"gemini_configurado": bool(agent1.client_ready)}
    )


@app.post("/api/extrair", response_class=JSONResponse)
async def extrair_nota_fiscal(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Endpoint que recebe o arquivo PDF da nota fiscal, armazena em uploads/

    e invoca o Agent1 para extrair os dados e classificar a despesa.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Formato inválido. Por favor, envie um arquivo em formato PDF (.pdf)."
        )

    # Caminho seguro de destino no diretório uploads
    destino_arquivo = UPLOADS_DIR / file.filename

    try:
        # Salva o arquivo no servidor
        with open(destino_arquivo, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Invocação do Agente de IA (conforme slide 16: agent1.extrair_dados(file))
        dados_extraidos = agent1.extrair_dados(str(destino_arquivo))

        return {
            "sucesso": True,
            "arquivo": file.filename,
            "tamanho_bytes": destino_arquivo.stat().st_size,
            "dados": dados_extraidos
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar a nota fiscal com o Agente: {str(e)}"
        )
    finally:
        file.file.close()


@app.get("/api/health")
async def health_check():
    """Endpoint de checagem de saúde e status do Agente."""
    return {
        "status": "online",
        "agente": "Agent1 (Percepção -> Processamento -> Decisão -> Ação)",
        "gemini_disponivel": agent1.client_ready,
        "uploads_total": len(list(UPLOADS_DIR.glob("*.pdf")))
    }


if __name__ == "__main__":
    import uvicorn
    porta = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"\n🚀 Servidor iniciando em: http://{host}:{porta}\n")
    uvicorn.run("main:app", host=host, port=porta, reload=True)

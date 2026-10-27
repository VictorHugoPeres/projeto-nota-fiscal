"""Aplicação Principal FastAPI - Sistema Administrativo-Financeiro com Agentes Inteligentes.

Disciplina: ESW424 - Prática de Engenharia de Software (UniRV)
1ª Etapa: Agente Inteligente de Extração e Classificação de Notas Fiscais (Agent1).
2ª Etapa: Agente de Verificação, Persistência e Lançamento de Movimentos (Agent2),
          Manter Pessoas, Manter Classificações e Registrar Contas a Pagar/Receber.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

# Arquitetura Modular de Agentes (Russell & Norvig / Especificação UniRV)
from agents.agent1.manipulacao_dados import Agent1
from agents.agent2.persistencia_dados import Agent2

# Banco de dados e Rotas da 2ª Etapa
from database.connection import get_db, init_db
from routes.cadastros import router as cadastros_router

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "uploads"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Assegura existência dos diretórios
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Sistema Administrativo-Financeiro - UniRV",
    description="ESW424 - Prática de Engenharia de Software | Avaliação N2 (Etapas 1 e 2)",
    version="2.0.0"
)


# Inicializa banco de dados ao iniciar a aplicação
@app.on_event("startup")
def on_startup():
    init_db()


# Configuração de CORS
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

# Instâncias dos Agentes de IA
agent1 = Agent1()
agent2 = Agent2()

REPO_URL = "https://github.com/VictorHugoPeres/projeto-nota-fiscal"


def obter_info_git() -> Dict[str, str]:
    """Retorna as informações do commit da última atualização do GitHub."""
    render_commit = os.getenv("RENDER_GIT_COMMIT", "").strip()
    if render_commit:
        return {
            "hash": render_commit[:7],
            "hash_completo": render_commit,
            "url": f"{REPO_URL}/commit/{render_commit}",
            "repo_url": REPO_URL,
            "mensagem": "Deploy automatizado (Render)"
        }

    try:
        short_hash = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            cwd=str(BASE_DIR)
        ).decode("utf-8").strip()

        full_hash = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            cwd=str(BASE_DIR)
        ).decode("utf-8").strip()

        msg = subprocess.check_output(
            ["git", "log", "-1", "--pretty=format:%s"],
            stderr=subprocess.DEVNULL,
            cwd=str(BASE_DIR)
        ).decode("utf-8").strip()

        if short_hash:
            return {
                "hash": short_hash,
                "hash_completo": full_hash,
                "url": f"{REPO_URL}/commit/{full_hash}",
                "repo_url": REPO_URL,
                "mensagem": msg
            }
    except Exception:
        pass

    version_file = BASE_DIR / "version.json"
    if version_file.exists():
        try:
            with open(version_file, "r", encoding="utf-8") as f:
                vdata = json.load(f)
                return {
                    "hash": vdata.get("hash", "16fac4d"),
                    "hash_completo": vdata.get("hash_completo", "16fac4dc655c02978126f2b7e0901b5281246dbe"),
                    "url": f"{REPO_URL}/commit/{vdata.get('hash_completo', '16fac4dc655c02978126f2b7e0901b5281246dbe')}",
                    "repo_url": REPO_URL,
                    "mensagem": vdata.get("mensagem", "")
                }
        except Exception:
            pass

    return {
        "hash": "16fac4d",
        "hash_completo": "16fac4dc655c02978126f2b7e0901b5281246dbe",
        "url": f"{REPO_URL}/commit/16fac4dc655c02978126f2b7e0901b5281246dbe",
        "repo_url": REPO_URL,
        "mensagem": "feat: Sistema Administrativo-Financeiro N2 UniRV"
    }


# Inclusão das rotas de cadastros da 2ª Etapa
app.include_router(cadastros_router)


# =============================================================
# ROTAS DE PÁGINAS HTML (INTERFACE WEB)
# =============================================================
@app.get("/", response_class=HTMLResponse)
async def pagina_inicial(request: Request):
    """Página de Importação, Análise e Lançamento de Notas Fiscais."""
    info_git = obter_info_git()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "aba_ativa": "notas",
            "gemini_configurado": bool(agent1.client_ready),
            "info_git": info_git
        }
    )


@app.get("/pessoas", response_class=HTMLResponse)
async def pagina_pessoas(request: Request):
    """Página de Manter Pessoas (Fornecedores, Clientes e Faturados)."""
    return templates.TemplateResponse(
        request=request,
        name="pessoas.html",
        context={"aba_ativa": "pessoas", "info_git": obter_info_git()}
    )


@app.get("/classificacoes", response_class=HTMLResponse)
async def pagina_classificacoes(request: Request):
    """Página de Manter Classificação (Despesas e Receitas)."""
    return templates.TemplateResponse(
        request=request,
        name="classificacoes.html",
        context={"aba_ativa": "classificacoes", "info_git": obter_info_git()}
    )


@app.get("/contas", response_class=HTMLResponse)
async def pagina_contas(request: Request):
    """Página de Registrar Contas (Contas a Pagar e a Receber)."""
    return templates.TemplateResponse(
        request=request,
        name="contas.html",
        context={"aba_ativa": "contas", "info_git": obter_info_git()}
    )


@app.get("/api/versao", response_class=JSONResponse)
@app.get("/api/git-info", response_class=JSONResponse)
async def versao_git():
    """Endpoint da API que retorna o código da última atualização no GitHub."""
    return obter_info_git()


# =============================================================
# ROTAS DA ETAPA 1 E ETAPA 2 (INTEGRAÇÃO DE AGENTES)
# =============================================================
@app.post("/api/extrair", response_class=JSONResponse)
async def extrair_nota_fiscal(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Endpoint da Etapa 1: recebe o PDF e extrai dados fiscais com o Agent1."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Formato inválido. Por favor, envie um arquivo em formato PDF (.pdf)."
        )

    destino_arquivo = UPLOADS_DIR / file.filename

    try:
        with open(destino_arquivo, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

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


@app.post("/api/verificar-existencia", response_class=JSONResponse)
@app.post("/api/analisar-entidades", response_class=JSONResponse)
async def verificar_existencia_endpoint(dados: Dict[str, Any], db: Session = Depends(get_db)):
    """Endpoint da Etapa 2: Agent2 consulta existência de Fornecedor, Faturado e Despesa."""
    try:
        resultado = agent2.verificar_existencia(dados, db)
        return {"sucesso": True, "analise": resultado}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao verificar existência de entidades no banco de dados: {str(e)}"
        )


@app.post("/api/persistir-movimento", response_class=JSONResponse)
@app.post("/api/lancar-movimento", response_class=JSONResponse)
async def persistir_movimento_endpoint(dados: Dict[str, Any], db: Session = Depends(get_db)):
    """Endpoint da Etapa 2: Agent2 cria entidades inexistentes e lança movimento com parcelas."""
    try:
        resultado = agent2.persistir_movimento(dados, db)
        return resultado
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao persistir movimento no banco de dados: {str(e)}"
        )


@app.get("/api/health")
async def health_check():
    """Endpoint de checagem de saúde e status dos Agentes."""
    return {
        "status": "online",
        "agentes": {
            "agent1": "Extração e Classificação Multimodal de DANFE (PDF)",
            "agent2": "Verificação, Conciliação e Persistência de Movimentos"
        },
        "gemini_disponivel": agent1.client_ready,
        "uploads_total": len(list(UPLOADS_DIR.glob("*.pdf")))
    }


if __name__ == "__main__":
    import uvicorn
    porta = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"\n🚀 Servidor iniciando em: http://{host}:{porta}\n")
    uvicorn.run("main:app", host=host, port=porta, reload=True)

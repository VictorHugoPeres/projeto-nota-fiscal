"""Módulo de Conexão com o Banco de Dados SQLite via SQLAlchemy.

Atende ao requisito:
- Banco de Dados: SQLite com SQLAlchemy (simples e sem dependências externas).
- Suporte a busca inteligente e insensível a acentuação e pontuação.
"""

import os
import re
import unicodedata
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "financeiro.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False
)


def _remover_acentos(text):
    """Normaliza texto removendo acentos e convertendo para minúsculas."""
    if not text:
        return ""
    return "".join(c for c in unicodedata.normalize("NFD", str(text)) if unicodedata.category(c) != "Mn").lower()


def _limpar_documento(text):
    """Remove pontuação e formatação deixando apenas números."""
    if not text:
        return ""
    return re.sub(r"\D", "", str(text))


# Registra funções customizadas no SQLite para busca insensível a acentos e pontuação
@event.listens_for(engine, "connect")
def configurar_funcoes_sqlite(dbapi_connection, connection_record):
    try:
        dbapi_connection.create_function("sem_acento", 1, _remover_acentos)
        dbapi_connection.create_function("limpar_doc", 1, _limpar_documento)
    except Exception:
        pass


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency do FastAPI para fornecer a sessão do banco por requisição."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Cria as tabelas e inicializa as classificações padrão do agronegócio."""
    from database.models import Classificacao

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Se não houver classificações, pré-popula as 9 oficiais de despesa e receitas
        if db.query(Classificacao).count() == 0:
            categorias_iniciais = [
                ("DESPESA", "INSUMOS AGRÍCOLAS"),
                ("DESPESA", "MANUTENÇÃO E OPERAÇÃO"),
                ("DESPESA", "RECURSOS HUMANOS"),
                ("DESPESA", "SERVIÇOS OPERACIONAIS"),
                ("DESPESA", "INFRAESTRUTURA E UTILIDADES"),
                ("DESPESA", "ADMINISTRATIVAS"),
                ("DESPESA", "SEGUROS E PROTEÇÃO"),
                ("DESPESA", "IMPOSTOS E TAXAS"),
                ("DESPESA", "INVESTIMENTOS"),
                ("RECEITA", "VENDA DE PRODUÇÃO AGRÍCOLA"),
                ("RECEITA", "PRESTAÇÃO DE SERVIÇOS AGRÍCOLAS"),
                ("RECEITA", "RECEITAS FINANCEIRAS"),
                ("RECEITA", "OUTRAS RECEITAS OPERACIONAIS"),
            ]
            for tipo, desc in categorias_iniciais:
                db.add(Classificacao(tipo=tipo, descricao=desc, status="ATIVO"))
            db.commit()
    finally:
        db.close()

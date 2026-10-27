"""Módulo de Compatibilidade de Banco de Dados.

Redireciona para o pacote modular `database.connection` e `database.models`.
"""

from database.connection import (
    Base,
    DB_PATH,
    DATABASE_URL,
    SessionLocal,
    engine,
    get_db,
    init_db,
)
from database.models import (
    Classificacao,
    MovimentoConta,
    ParcelaConta,
    Pessoa,
    movimento_classificacao,
)

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "init_db",
    "Pessoa",
    "Classificacao",
    "MovimentoConta",
    "ParcelaConta",
    "movimento_classificacao",
    "DB_PATH",
    "DATABASE_URL",
]

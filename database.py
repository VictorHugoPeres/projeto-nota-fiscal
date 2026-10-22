"""Módulo de Banco de Dados e Modelos ORM (SQLAlchemy) - Etapa 2.

Entidades solicitadas no documento UniRV:
- PESSOAS (Fornecedor, Cliente, Faturado)
- CLASSIFICACAO (Despesa, Receita)
- MOVIMENTOCONTAS (APAGAR, ARECEBER)
- PARCELACONTAS (Parcelas associadas ao Movimento)
"""

import os
from datetime import datetime
from pathlib import Path
from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'financeiro.db'}")

# SQLite precisa de check_same_thread=False no FastAPI
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Tabela associativa entre Movimento e Classificações (N:N)
# Conforme regra: "Um registro de contas a pagar pode ser classificado em uma ou mais Tipo de DESPESAS"
movimento_classificacao = Table(
    "movimento_classificacao",
    Base.metadata,
    Column("movimento_id", Integer, ForeignKey("movimentocontas.id", ondelete="CASCADE"), primary_key=True),
    Column("classificacao_id", Integer, ForeignKey("classificacao.id", ondelete="CASCADE"), primary_key=True),
)


class Pessoa(Base):
    """Entidade PESSOAS: Atende Fornecedor, Cliente e Faturado."""
    __tablename__ = "pessoas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tipo = Column(String(50), nullable=False)  # 'FORNECEDOR', 'CLIENTE', 'FATURADO', 'CLIENTE-FORNECEDOR'
    razao_social = Column(String(200), nullable=False, index=True)
    cpf_cnpj = Column(String(30), nullable=True, index=True)
    status = Column(String(20), default="ATIVO", nullable=False)  # 'ATIVO' ou 'INATIVO'

    # Relacionamentos
    movimentos_fornecedor = relationship("MovimentoConta", foreign_keys="MovimentoConta.pessoa_id", back_populates="pessoa")
    movimentos_faturado = relationship("MovimentoConta", foreign_keys="MovimentoConta.faturado_id", back_populates="faturado")

    def to_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "razao_social": self.razao_social,
            "cpf_cnpj": self.cpf_cnpj or "",
            "status": self.status,
        }


class Classificacao(Base):
    """Entidade CLASSIFICACAO: Atende Tipo de Despesa e Tipo de Receita."""
    __tablename__ = "classificacao"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tipo = Column(String(20), nullable=False)  # 'DESPESA' ou 'RECEITA'
    descricao = Column(String(150), nullable=False, index=True)
    status = Column(String(20), default="ATIVO", nullable=False)  # 'ATIVO' ou 'INATIVO'

    movimentos = relationship("MovimentoConta", secondary=movimento_classificacao, back_populates="classificacoes")

    def to_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "descricao": self.descricao,
            "status": self.status,
        }


class MovimentoConta(Base):
    """Entidade MOVIMENTOCONTAS: Contas a Pagar (APAGAR) ou Contas a Receber (ARECEBER)."""
    __tablename__ = "movimentocontas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tipo = Column(String(20), nullable=False)  # 'APAGAR' ou 'ARECEBER'
    descricao = Column(String(250), nullable=True)
    numero_nota = Column(String(50), nullable=True)
    valor_total = Column(Float, nullable=False, default=0.0)
    data_emissao = Column(String(20), nullable=True)
    status = Column(String(20), default="ATIVO", nullable=False)  # 'ATIVO' ou 'INATIVO'

    pessoa_id = Column(Integer, ForeignKey("pessoas.id"), nullable=True)
    faturado_id = Column(Integer, ForeignKey("pessoas.id"), nullable=True)

    pessoa = relationship("Pessoa", foreign_keys=[pessoa_id], back_populates="movimentos_fornecedor")
    faturado = relationship("Pessoa", foreign_keys=[faturado_id], back_populates="movimentos_faturado")
    parcelas = relationship("ParcelaConta", back_populates="movimento", cascade="all, delete-orphan")
    classificacoes = relationship("Classificacao", secondary=movimento_classificacao, back_populates="movimentos")

    def to_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "descricao": self.descricao or "",
            "numero_nota": self.numero_nota or "",
            "valor_total": self.valor_total,
            "data_emissao": self.data_emissao or "",
            "status": self.status,
            "pessoa": self.pessoa.to_dict() if self.pessoa else None,
            "faturado": self.faturado.to_dict() if self.faturado else None,
            "classificacoes": [c.to_dict() for c in self.classificacoes],
            "parcelas": [p.to_dict() for p in self.parcelas],
        }


class ParcelaConta(Base):
    """Entidade PARCELACONTAS: Parcelas de um movimento com vencimento e identificação única."""
    __tablename__ = "parcelacontas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    movimento_id = Column(Integer, ForeignKey("movimentocontas.id", ondelete="CASCADE"), nullable=False)
    identificacao = Column(String(80), nullable=False, unique=True, index=True)  # ÚNICA
    numero_parcela = Column(Integer, nullable=False, default=1)
    data_vencimento = Column(String(20), nullable=True)
    valor = Column(Float, nullable=False, default=0.0)
    status = Column(String(20), default="PENDENTE", nullable=False)  # 'PENDENTE', 'PAGO', 'INATIVO'

    movimento = relationship("MovimentoConta", back_populates="parcelas")

    def to_dict(self):
        return {
            "id": self.id,
            "movimento_id": self.movimento_id,
            "identificacao": self.identificacao,
            "numero_parcela": self.numero_parcela,
            "data_vencimento": self.data_vencimento or "",
            "valor": self.valor,
            "status": self.status,
        }


def get_db():
    """Dependency do FastAPI para obter sessão do banco."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Inicializa as tabelas e pré-popula classificações padrão se estiver vazio."""
    Base.metadata.create_all(bind=engine)

    # Pré-carregar classificações padrão da disciplina (Plano de Contas)
    db = SessionLocal()
    try:
        total_classif = db.query(Classificacao).count()
        if total_classif == 0:
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

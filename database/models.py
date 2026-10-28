"""Modelos do Banco de Dados Relacional (SQLAlchemy) - Etapas 1 e 2.

Atende rigorosamente aos Requisitos do Sistema:
- Pessoas: id, tipo ('CLIENTE-FORNECEDOR' ou 'FATURADO'), razao_social, nome_fantasia, documento (CNPJ/CPF), status ('ATIVO'/'INATIVO').
- Classificacao: id, tipo ('DESPESA' ou 'RECEITA'), descricao, status ('ATIVO'/'INATIVO').
- MovimentoContas: id, tipo ('APAGAR' ou 'ARECEBER'), fornecedor_id, faturado_id, numero_documento, data_emissao, valor_total, descricao_produtos, status ('ATIVO'/'INATIVO').
- ParcelaContas: id, movimento_id, numero_parcela, data_vencimento, valor, status ('ATIVO'/'INATIVO').
- MovimentoClassificacao: tabela associativa entre MovimentoContas e Classificacao.
"""

from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import relationship
from database.connection import Base

# Tabela Associativa entre MovimentoContas e Classificacao (N:N)
# Conforme requisito: "Um registro de contas a pagar, pode ser classificado em uma ou mais Tipo de DESPESAS"
movimento_classificacao = Table(
    "movimento_classificacao",
    Base.metadata,
    Column("movimento_id", Integer, ForeignKey("movimentocontas.id", ondelete="CASCADE"), primary_key=True),
    Column("classificacao_id", Integer, ForeignKey("classificacao.id", ondelete="CASCADE"), primary_key=True),
)


class Pessoa(Base):
    """Modelo PESSOAS: Fornecedores, Faturados e Clientes."""
    __tablename__ = "pessoas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tipo = Column(String(50), nullable=False, default="CLIENTE-FORNECEDOR")  # 'CLIENTE-FORNECEDOR' ou 'FATURADO'
    razao_social = Column(String(200), nullable=False, index=True)
    nome_fantasia = Column(String(200), nullable=True, default="")
    documento = Column(String(30), nullable=True, index=True)  # CNPJ ou CPF
    status = Column(String(20), default="ATIVO", nullable=False)  # 'ATIVO' ou 'INATIVO'

    # Relacionamentos com Movimentos
    movimentos_fornecedor = relationship(
        "MovimentoConta",
        foreign_keys="MovimentoConta.fornecedor_id",
        back_populates="fornecedor"
    )
    movimentos_faturado = relationship(
        "MovimentoConta",
        foreign_keys="MovimentoConta.faturado_id",
        back_populates="faturado"
    )

    # Compatibilidade com referências antigas (cpf_cnpj)
    @property
    def cpf_cnpj(self):
        return self.documento

    @cpf_cnpj.setter
    def cpf_cnpj(self, val):
        self.documento = val

    def to_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "razao_social": self.razao_social,
            "nome_fantasia": self.nome_fantasia or "",
            "documento": self.documento or "",
            "cpf_cnpj": self.documento or "",
            "status": self.status,
        }


class Classificacao(Base):
    """Modelo CLASSIFICACAO: Categorias de Despesas ou Receitas."""
    __tablename__ = "classificacao"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tipo = Column(String(20), nullable=False, default="DESPESA")  # 'DESPESA' ou 'RECEITA'
    descricao = Column(String(150), nullable=False, index=True)
    status = Column(String(20), default="ATIVO", nullable=False)  # 'ATIVO' ou 'INATIVO'

    # Relacionamento N:N com MovimentoContas
    movimentos = relationship(
        "MovimentoConta",
        secondary=movimento_classificacao,
        back_populates="classificacoes"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "descricao": self.descricao,
            "status": self.status,
        }


class MovimentoConta(Base):
    """Modelo MOVIMENTOCONTAS: Registro de Contas a Pagar (APAGAR) ou Contas a Receber (ARECEBER)."""
    __tablename__ = "movimentocontas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tipo = Column(String(20), nullable=False, default="APAGAR")  # 'APAGAR' ou 'ARECEBER'
    fornecedor_id = Column(Integer, ForeignKey("pessoas.id"), nullable=True)
    faturado_id = Column(Integer, ForeignKey("pessoas.id"), nullable=True)
    numero_documento = Column(String(50), nullable=True)  # Número da NF ou Título
    data_emissao = Column(String(20), nullable=True)
    valor_total = Column(Float, nullable=False, default=0.0)
    descricao_produtos = Column(Text, nullable=True)  # Discriminação dos produtos/serviços
    status = Column(String(20), default="ATIVO", nullable=False)  # 'ATIVO' ou 'INATIVO'

    # Relacionamentos
    fornecedor = relationship("Pessoa", foreign_keys=[fornecedor_id], back_populates="movimentos_fornecedor")
    faturado = relationship("Pessoa", foreign_keys=[faturado_id], back_populates="movimentos_faturado")
    pessoa = relationship("Pessoa", foreign_keys=[fornecedor_id], viewonly=True)
    parcelas = relationship("ParcelaConta", back_populates="movimento", cascade="all, delete-orphan")
    classificacoes = relationship("Classificacao", secondary=movimento_classificacao, back_populates="movimentos")

    # Aliases de compatibilidade
    @property
    def descricao(self):
        return self.descricao_produtos

    @descricao.setter
    def descricao(self, val):
        self.descricao_produtos = val

    @property
    def numero_nota(self):
        return self.numero_documento

    @numero_nota.setter
    def numero_nota(self, val):
        self.numero_documento = val

    @property
    def pessoa_id(self):
        return self.fornecedor_id

    @pessoa_id.setter
    def pessoa_id(self, val):
        self.fornecedor_id = val

    def to_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "fornecedor_id": self.fornecedor_id,
            "faturado_id": self.faturado_id,
            "numero_documento": self.numero_documento or "",
            "numero_nota": self.numero_documento or "",
            "data_emissao": self.data_emissao or "",
            "valor_total": self.valor_total,
            "descricao_produtos": self.descricao_produtos or "",
            "status": self.status,
            "fornecedor": self.fornecedor.to_dict() if self.fornecedor else None,
            "pessoa": self.fornecedor.to_dict() if self.fornecedor else None,
            "faturado": self.faturado.to_dict() if self.faturado else None,
            "classificacoes": [c.to_dict() for c in self.classificacoes],
            "parcelas": [p.to_dict() for p in self.parcelas],
        }


class ParcelaConta(Base):
    """Modelo PARCELACONTAS: Parcelas de um Movimento Financeiro."""
    __tablename__ = "parcelacontas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    movimento_id = Column(Integer, ForeignKey("movimentocontas.id", ondelete="CASCADE"), nullable=False)
    numero_parcela = Column(Integer, nullable=False, default=1)
    identificacao = Column(String(80), nullable=True, unique=True, index=True)
    data_vencimento = Column(String(20), nullable=True)
    valor = Column(Float, nullable=False, default=0.0)
    status = Column(String(20), default="ATIVO", nullable=False)  # 'ATIVO' ou 'INATIVO' (ou PENDENTE/PAGO)

    # Relacionamento com MovimentoConta
    movimento = relationship("MovimentoConta", back_populates="parcelas")

    def to_dict(self):
        return {
            "id": self.id,
            "movimento_id": self.movimento_id,
            "numero_parcela": self.numero_parcela,
            "identificacao": self.identificacao or f"PARC-{self.numero_parcela}",
            "data_vencimento": self.data_vencimento or "",
            "valor": self.valor,
            "status": self.status,
        }

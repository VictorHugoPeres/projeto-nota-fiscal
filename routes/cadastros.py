"""Rotas de API para os CRUDs da 2ª Etapa:
- Manter Pessoas (Fornecedor, Cliente, Faturado)
- Manter Classificação (Despesa, Receita)
- Registrar Contas (Contas a Pagar, Contas a Receber)

Regras de negócio atendidas:
a. Trazer a tabela de registros vazia inicialmente
b. Carregar dados através da Busca ou botão TODOS
c. TODOS carrega status = ATIVO
d. Indexação por coluna na tabela
e. Busca inteligente por múltiplos termos, insensível a acentos, pontuação e maiúsculas
f. Duas ações na tabela: Editar / Excluir (Lógico)
g. No CREATE campo STATUS oculto == ATIVO
h. No UPDATE campo STATUS oculto
i. No DELETE altera campo STATUS == INATIVO
j. Possibilidade de REATIVAR registros inativos
k. Controle de Acesso: Usuários com perfil 'Cliente' NÃO podem inativar contas.
"""

import re
import unicodedata
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import cast, func, or_, String
from sqlalchemy.orm import Session, aliased

from database import Classificacao, MovimentoConta, ParcelaConta, Pessoa, get_db

router = APIRouter(prefix="/api", tags=["cadastros"])


def _normalizar(txt: str) -> str:
    """Normaliza texto para comparação insensível a acentuação e caixa."""
    if not txt:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", str(txt).strip())
        if unicodedata.category(c) != "Mn"
    ).lower()


# -------------------------------------------------------------
# SCHEMAS PYDANTIC SIMPLES
# -------------------------------------------------------------
class PessoaSchema(BaseModel):
    tipo: str  # 'CLIENTE-FORNECEDOR', 'FORNECEDOR', 'CLIENTE', 'FATURADO'
    razao_social: str
    nome_fantasia: Optional[str] = ""
    cpf_cnpj: Optional[str] = ""
    status: Optional[str] = "ATIVO"


class ClassificacaoSchema(BaseModel):
    tipo: str  # 'DESPESA' ou 'RECEITA'
    descricao: str
    status: Optional[str] = "ATIVO"


class ParcelaInputSchema(BaseModel):
    numero_parcela: int
    data_vencimento: str
    valor: float


class MovimentoSchema(BaseModel):
    tipo: str  # 'APAGAR' ou 'ARECEBER'
    descricao: Optional[str] = ""
    numero_nota: Optional[str] = ""
    valor_total: float
    data_emissao: Optional[str] = ""
    pessoa_id: Optional[int] = None
    faturado_id: Optional[int] = None
    classificacao_ids: Optional[List[int]] = []
    parcelas: Optional[List[ParcelaInputSchema]] = []
    status: Optional[str] = "ATIVO"


# =============================================================
# 1. CRUD PESSOAS
# =============================================================
@router.get("/pessoas")
def listar_pessoas(
    busca: Optional[str] = None,
    tipo: Optional[str] = None,
    carregar_todos: bool = False,
    incluir_inativos: bool = False,
    db: Session = Depends(get_db)
):
    """Regra a/b/c: Tabela vem vazia por padrão; só busca com termo ou carregar_todos=True."""
    if not busca and not carregar_todos:
        return []

    query = db.query(Pessoa)

    if tipo and tipo != "TODOS":
        query = query.filter(Pessoa.tipo == tipo)

    if not incluir_inativos:
        query = query.filter(Pessoa.status == "ATIVO")

    if busca and busca.strip():
        termo_limpo = busca.strip()
        termo_norm = f"%{_normalizar(termo_limpo)}%"
        digitos = re.sub(r"\D", "", termo_limpo)

        condicoes = [
            func.sem_acento(Pessoa.razao_social).like(termo_norm),
            func.sem_acento(Pessoa.nome_fantasia).like(termo_norm),
            func.sem_acento(Pessoa.tipo).like(termo_norm),
            func.sem_acento(Pessoa.documento).like(termo_norm),
            cast(Pessoa.id, String).like(f"%{termo_limpo.replace('#', '')}%")
        ]

        if digitos:
            condicoes.append(func.limpar_doc(Pessoa.documento).like(f"%{digitos}%"))

        query = query.filter(or_(*condicoes))

    return [p.to_dict() for p in query.order_by(Pessoa.id.desc()).all()]


@router.post("/pessoas")
def criar_pessoa(dados: PessoaSchema, db: Session = Depends(get_db)):
    """Regra g: No CREATE campo STATUS oculto == ATIVO."""
    pessoa = Pessoa(
        tipo=dados.tipo.strip().upper(),
        razao_social=dados.razao_social.strip().upper(),
        nome_fantasia=dados.nome_fantasia.strip().upper() if dados.nome_fantasia else "",
        documento=dados.cpf_cnpj.strip() if dados.cpf_cnpj else "",
        status="ATIVO"
    )
    db.add(pessoa)
    db.commit()
    db.refresh(pessoa)
    return {"sucesso": True, "pessoa": pessoa.to_dict()}


@router.put("/pessoas/{pessoa_id}")
def atualizar_pessoa(pessoa_id: int, dados: PessoaSchema, db: Session = Depends(get_db)):
    """Regra h: No UPDATE campo STATUS oculto."""
    pessoa = db.query(Pessoa).get(pessoa_id)
    if not pessoa:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")

    pessoa.tipo = dados.tipo.strip().upper()
    pessoa.razao_social = dados.razao_social.strip().upper()
    pessoa.nome_fantasia = dados.nome_fantasia.strip().upper() if dados.nome_fantasia else ""
    pessoa.documento = dados.cpf_cnpj.strip() if dados.cpf_cnpj else ""
    db.commit()
    db.refresh(pessoa)
    return {"sucesso": True, "pessoa": pessoa.to_dict()}


@router.delete("/pessoas/{pessoa_id}")
def excluir_pessoa(pessoa_id: int, db: Session = Depends(get_db)):
    """Regra i: No DELETE altera campo STATUS == INATIVO (Exclusão Lógica)."""
    pessoa = db.query(Pessoa).get(pessoa_id)
    if not pessoa:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")

    pessoa.status = "INATIVO"
    db.commit()
    return {"sucesso": True, "mensagem": "Registro inativado com sucesso"}


@router.patch("/pessoas/{pessoa_id}/reativar")
def reativar_pessoa(pessoa_id: int, db: Session = Depends(get_db)):
    """Regra de Negócio: Cadastros devem poder REATIVAR um registro INATIVO."""
    pessoa = db.query(Pessoa).get(pessoa_id)
    if not pessoa:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")

    pessoa.status = "ATIVO"
    db.commit()
    return {"sucesso": True, "mensagem": "Registro reativado com sucesso"}


# =============================================================
# 2. CRUD CLASSIFICAÇÃO
# =============================================================
@router.get("/classificacoes")
def listar_classificacoes(
    busca: Optional[str] = None,
    tipo: Optional[str] = None,
    carregar_todos: bool = False,
    incluir_inativos: bool = False,
    db: Session = Depends(get_db)
):
    if not busca and not carregar_todos:
        return []

    query = db.query(Classificacao)

    if tipo and tipo != "TODOS":
        query = query.filter(Classificacao.tipo == tipo)

    if not incluir_inativos:
        query = query.filter(Classificacao.status == "ATIVO")

    if busca and busca.strip():
        termo_limpo = busca.strip()
        termo_norm = f"%{_normalizar(termo_limpo)}%"
        query = query.filter(
            or_(
                func.sem_acento(Classificacao.descricao).like(termo_norm),
                func.sem_acento(Classificacao.tipo).like(termo_norm),
                cast(Classificacao.id, String).like(f"%{termo_limpo.replace('#', '')}%")
            )
        )

    return [c.to_dict() for c in query.order_by(Classificacao.id.desc()).all()]


@router.post("/classificacoes")
def criar_classificacao(dados: ClassificacaoSchema, db: Session = Depends(get_db)):
    classificacao = Classificacao(
        tipo=dados.tipo.strip().upper(),
        descricao=dados.descricao.strip().upper(),
        status="ATIVO"
    )
    db.add(classificacao)
    db.commit()
    db.refresh(classificacao)
    return {"sucesso": True, "classificacao": classificacao.to_dict()}


@router.put("/classificacoes/{classificacao_id}")
def atualizar_classificacao(classificacao_id: int, dados: ClassificacaoSchema, db: Session = Depends(get_db)):
    classificacao = db.query(Classificacao).get(classificacao_id)
    if not classificacao:
        raise HTTPException(status_code=404, detail="Classificação não encontrada")

    classificacao.tipo = dados.tipo.strip().upper()
    classificacao.descricao = dados.descricao.strip().upper()
    db.commit()
    db.refresh(classificacao)
    return {"sucesso": True, "classificacao": classificacao.to_dict()}


@router.delete("/classificacoes/{classificacao_id}")
def excluir_classificacao(classificacao_id: int, db: Session = Depends(get_db)):
    classificacao = db.query(Classificacao).get(classificacao_id)
    if not classificacao:
        raise HTTPException(status_code=404, detail="Classificação não encontrada")

    classificacao.status = "INATIVO"
    db.commit()
    return {"sucesso": True, "mensagem": "Classificação inativada com sucesso"}


@router.patch("/classificacoes/{classificacao_id}/reativar")
def reativar_classificacao(classificacao_id: int, db: Session = Depends(get_db)):
    classificacao = db.query(Classificacao).get(classificacao_id)
    if not classificacao:
        raise HTTPException(status_code=404, detail="Classificação não encontrada")

    classificacao.status = "ATIVO"
    db.commit()
    return {"sucesso": True, "mensagem": "Classificação reativada com sucesso"}


# =============================================================
# 3. REGISTRAR CONTAS (MOVIMENTOCONTAS & PARCELACONTAS)
# =============================================================
@router.get("/movimentos")
def listar_movimentos(
    busca: Optional[str] = None,
    tipo: Optional[str] = None,
    carregar_todos: bool = False,
    incluir_inativos: bool = False,
    db: Session = Depends(get_db)
):
    if not busca and not carregar_todos:
        return []

    Forn = aliased(Pessoa)
    Fat = aliased(Pessoa)

    query = (
        db.query(MovimentoConta)
        .outerjoin(Forn, MovimentoConta.fornecedor_id == Forn.id)
        .outerjoin(Fat, MovimentoConta.faturado_id == Fat.id)
    )

    if tipo and tipo != "TODOS":
        query = query.filter(MovimentoConta.tipo == tipo)

    if not incluir_inativos:
        query = query.filter(MovimentoConta.status == "ATIVO")

    if busca and busca.strip():
        termo_limpo = busca.strip()
        termo_norm = f"%{_normalizar(termo_limpo)}%"
        digitos = re.sub(r"\D", "", termo_limpo)

        condicoes = [
            func.sem_acento(MovimentoConta.descricao_produtos).like(termo_norm),
            func.sem_acento(MovimentoConta.numero_documento).like(termo_norm),
            func.sem_acento(MovimentoConta.tipo).like(termo_norm),
            cast(MovimentoConta.id, String).like(f"%{termo_limpo.replace('#', '')}%"),
            func.sem_acento(Forn.razao_social).like(termo_norm),
            func.sem_acento(Forn.nome_fantasia).like(termo_norm),
            func.sem_acento(Forn.documento).like(termo_norm),
            func.sem_acento(Fat.razao_social).like(termo_norm),
            func.sem_acento(Fat.documento).like(termo_norm)
        ]

        if digitos:
            condicoes.append(func.limpar_doc(Forn.documento).like(f"%{digitos}%"))
            condicoes.append(func.limpar_doc(Fat.documento).like(f"%{digitos}%"))
            condicoes.append(func.limpar_doc(MovimentoConta.numero_documento).like(f"%{digitos}%"))

        query = query.filter(or_(*condicoes))

    return [m.to_dict() for m in query.order_by(MovimentoConta.id.desc()).all()]


@router.post("/movimentos")
def criar_movimento(dados: MovimentoSchema, db: Session = Depends(get_db)):
    movimento = MovimentoConta(
        tipo=dados.tipo.strip().upper(),
        descricao_produtos=dados.descricao.strip() if dados.descricao else "",
        numero_documento=dados.numero_nota.strip() if dados.numero_nota else "",
        valor_total=dados.valor_total,
        data_emissao=dados.data_emissao.strip() if dados.data_emissao else "",
        fornecedor_id=dados.pessoa_id,
        faturado_id=dados.faturado_id,
        status="ATIVO"
    )

    if dados.classificacao_ids:
        classificacoes = db.query(Classificacao).filter(Classificacao.id.in_(dados.classificacao_ids)).all()
        movimento.classificacoes.extend(classificacoes)

    db.add(movimento)
    db.flush()

    # Criar parcelas
    if dados.parcelas:
        for p in dados.parcelas:
            identificacao = f"MOV{movimento.id}-PARC{p.numero_parcela}"
            parcela = ParcelaConta(
                movimento_id=movimento.id,
                identificacao=identificacao,
                numero_parcela=p.numero_parcela,
                data_vencimento=p.data_vencimento,
                valor=p.valor,
                status="PENDENTE"
            )
            db.add(parcela)
    else:
        identificacao = f"MOV{movimento.id}-PARC1"
        parcela = ParcelaConta(
            movimento_id=movimento.id,
            identificacao=identificacao,
            numero_parcela=1,
            data_vencimento=dados.data_emissao or "",
            valor=dados.valor_total,
            status="PENDENTE"
        )
        db.add(parcela)

    db.commit()
    db.refresh(movimento)
    return {"sucesso": True, "movimento": movimento.to_dict()}


@router.delete("/movimentos/{movimento_id}")
def excluir_movimento(movimento_id: int, request: Request, db: Session = Depends(get_db)):
    """Inativação lógica de Movimento de Conta com verificação de perfil de acesso."""
    usuario = request.session.get("usuario")
    if usuario and usuario.get("role") == "cliente":
        raise HTTPException(
            status_code=403,
            detail="Acesso Negado: Usuários com perfil 'Cliente' não possuem permissão para inativar contas. Apenas o Administrador pode executar esta ação."
        )

    movimento = db.query(MovimentoConta).get(movimento_id)
    if not movimento:
        raise HTTPException(status_code=404, detail="Movimento não encontrado")

    movimento.status = "INATIVO"
    db.commit()
    return {"sucesso": True, "mensagem": "Movimento inativado com sucesso"}


@router.patch("/movimentos/{movimento_id}/reativar")
def reativar_movimento(movimento_id: int, request: Request, db: Session = Depends(get_db)):
    """Reativação de Movimento de Conta com verificação de perfil de acesso."""
    usuario = request.session.get("usuario")
    if usuario and usuario.get("role") == "cliente":
        raise HTTPException(
            status_code=403,
            detail="Acesso Negado: Usuários com perfil 'Cliente' não possuem permissão para reativar contas. Apenas o Administrador pode executar esta ação."
        )

    movimento = db.query(MovimentoConta).get(movimento_id)
    if not movimento:
        raise HTTPException(status_code=404, detail="Movimento não encontrado")

    movimento.status = "ATIVO"
    db.commit()
    return {"sucesso": True, "mensagem": "Movimento reativado com sucesso"}

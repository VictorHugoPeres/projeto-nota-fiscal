"""Módulo do Agente 2 (Agent2): Análise, Conciliação e Lançamento de Dados no Banco de Dados.

Disciplina: ESW424 - Prática de Engenharia de Software (UniRV)
Etapa 2:
1. Consultar existência de Fornecedor, Faturado e Despesa no Banco de Dados.
2. Apresentar diagnóstico na tela para o usuário.
3. Se confirmado, persistir Fornecedor, Faturado, Despesa, Movimento a Pagar e Parcelas.
"""

import re
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from database import Classificacao, MovimentoConta, ParcelaConta, Pessoa


def normalizar_documento(doc: Optional[str]) -> str:
    """Remove caracteres não numéricos de CPF/CNPJ para comparação robusta."""
    if not doc:
        return ""
    return re.sub(r"\D", "", doc)


class Agent2:
    """Agente de Análise e Persistência de Dados Fiscais e Financeiros."""

    def __init__(self):
        pass

    def consultar_entidades(self, dados: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Consulta no banco de dados se Fornecedor, Faturado e Despesa existem."""
        # 1. Consulta Fornecedor
        fornecedor_dados = dados.get("fornecedor", {})
        razao_social_forn = (
            fornecedor_dados.get("razao_social")
            or fornecedor_dados.get("nome_fantasia")
            or "FORNECEDOR NÃO INFORMADO"
        )
        cnpj_forn = fornecedor_dados.get("cnpj", "")
        cnpj_limpo = normalizar_documento(cnpj_forn)

        fornecedor_existente = None
        if cnpj_limpo:
            # Busca por CNPJ
            pessoas = db.query(Pessoa).filter(Pessoa.tipo.in_(["FORNECEDOR", "CLIENTE-FORNECEDOR"])).all()
            for p in pessoas:
                if normalizar_documento(p.cpf_cnpj) == cnpj_limpo:
                    fornecedor_existente = p
                    break

        if not fornecedor_existente and razao_social_forn:
            # Busca por Razão Social
            fornecedor_existente = db.query(Pessoa).filter(
                Pessoa.tipo.in_(["FORNECEDOR", "CLIENTE-FORNECEDOR"]),
                Pessoa.razao_social.ilike(razao_social_forn.strip())
            ).first()

        resultado_fornecedor = {
            "nome": razao_social_forn,
            "documento": cnpj_forn or "NÃO INFORMADO",
            "existe": fornecedor_existente is not None,
            "id": fornecedor_existente.id if fornecedor_existente else None,
            "status_bd": fornecedor_existente.status if fornecedor_existente else None
        }

        # 2. Consulta Faturado
        faturado_dados = dados.get("faturado", {})
        nome_faturado = faturado_dados.get("nome", "FATURADO NÃO INFORMADO")
        cpf_faturado = faturado_dados.get("cpf", "")
        cpf_limpo = normalizar_documento(cpf_faturado)

        faturado_existente = None
        if cpf_limpo:
            pessoas = db.query(Pessoa).filter(Pessoa.tipo == "FATURADO").all()
            for p in pessoas:
                if normalizar_documento(p.cpf_cnpj) == cpf_limpo:
                    faturado_existente = p
                    break

        if not faturado_existente and nome_faturado:
            faturado_existente = db.query(Pessoa).filter(
                Pessoa.tipo == "FATURADO",
                Pessoa.razao_social.ilike(nome_faturado.strip())
            ).first()

        resultado_faturado = {
            "nome": nome_faturado,
            "documento": cpf_faturado or "NÃO INFORMADO",
            "existe": faturado_existente is not None,
            "id": faturado_existente.id if faturado_existente else None,
            "status_bd": faturado_existente.status if faturado_existente else None
        }

        # 3. Consulta Despesa
        classificacao_dados = dados.get("classificacao_despesa", {})
        categoria_despesa = classificacao_dados.get("categoria", "MANUTENÇÃO E OPERAÇÃO")

        despesa_existente = db.query(Classificacao).filter(
            Classificacao.tipo == "DESPESA",
            Classificacao.descricao.ilike(categoria_despesa.strip())
        ).first()

        resultado_despesa = {
            "descricao": categoria_despesa,
            "existe": despesa_existente is not None,
            "id": despesa_existente.id if despesa_existente else None,
            "status_bd": despesa_existente.status if despesa_existente else None
        }

        return {
            "fornecedor": resultado_fornecedor,
            "faturado": resultado_faturado,
            "despesa": resultado_despesa
        }

    def lancar_no_banco(self, dados: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Executa os 5 passos do documento:

        1. CRIAR O NOVO FORNECEDOR (se for o caso)
        2. CRIAR O NOVO FATURADO (se for o caso)
        3. CRIAR NOVA DESPESA (se for o caso)
        4. CRIAR UM NOVO REGISTRO DO MOVIMENTO E SUA PARCELA
        5. INFORMAR AO USUÁRIO QUE REGISTRO FOI LANÇADO COM SUCESSO.
        """
        analise = self.consultar_entidades(dados, db)

        # 1. Obter ou Criar Fornecedor
        fornecedor_info = analise["fornecedor"]
        if fornecedor_info["existe"]:
            fornecedor = db.query(Pessoa).get(fornecedor_info["id"])
            fornecedor_criado = False
        else:
            fornecedor = Pessoa(
                tipo="CLIENTE-FORNECEDOR",
                razao_social=fornecedor_info["nome"],
                cpf_cnpj=fornecedor_info["documento"] if fornecedor_info["documento"] != "NÃO INFORMADO" else "",
                status="ATIVO"
            )
            db.add(fornecedor)
            db.flush()
            fornecedor_criado = True

        # 2. Obter ou Criar Faturado
        faturado_info = analise["faturado"]
        if faturado_info["existe"]:
            faturado = db.query(Pessoa).get(faturado_info["id"])
            faturado_criado = False
        else:
            faturado = Pessoa(
                tipo="FATURADO",
                razao_social=faturado_info["nome"],
                cpf_cnpj=faturado_info["documento"] if faturado_info["documento"] != "NÃO INFORMADO" else "",
                status="ATIVO"
            )
            db.add(faturado)
            db.flush()
            faturado_criado = True

        # 3. Obter ou Criar Despesa
        despesa_info = analise["despesa"]
        if despesa_info["existe"]:
            despesa = db.query(Classificacao).get(despesa_info["id"])
            despesa_criada = False
        else:
            despesa = Classificacao(
                tipo="DESPESA",
                descricao=despesa_info["descricao"],
                status="ATIVO"
            )
            db.add(despesa)
            db.flush()
            despesa_criada = True

        # 4. Criar Novo Registro de Movimento (MOVIMENTOCONTAS)
        valor_total_raw = dados.get("valor_total", 0.0)
        try:
            if isinstance(valor_total_raw, str):
                valor_limpo = valor_total_raw.replace("R$", "").replace(".", "").replace(",", ".").strip()
                valor_total = float(valor_limpo)
            else:
                valor_total = float(valor_total_raw)
        except Exception:
            valor_total = 0.0

        numero_nota = str(dados.get("numero_nota", "") or "")
        data_emissao = str(dados.get("data_emissao", "") or "")

        # Descrição com produtos
        produtos = dados.get("descricao_produtos", [])
        descricao_mov = f"NF {numero_nota} - {fornecedor.razao_social}"
        if produtos:
            primeiros_produtos = ", ".join(produtos[:2])
            descricao_mov += f" ({primeiros_produtos})"

        movimento = MovimentoConta(
            tipo="APAGAR",
            descricao=descricao_mov[:245],
            numero_nota=numero_nota,
            valor_total=valor_total,
            data_emissao=data_emissao,
            status="ATIVO",
            pessoa_id=fornecedor.id,
            faturado_id=faturado.id,
        )
        movimento.classificacoes.append(despesa)
        db.add(movimento)
        db.flush()

        # 4.1 Criar Parcelas (PARCELACONTAS)
        parcelas_dados = dados.get("parcelas", [])
        qtd_parcelas = int(dados.get("quantidade_parcelas", 1) or 1)

        parcelas_criadas = []
        if parcelas_dados and isinstance(parcelas_dados, list):
            for idx, p in enumerate(parcelas_dados, start=1):
                num_parc = p.get("numero", idx)
                venc = p.get("data_vencimento") or dados.get("data_vencimento") or ""
                v_raw = p.get("valor", valor_total / max(qtd_parcelas, 1))
                try:
                    if isinstance(v_raw, str):
                        v_parc = float(v_raw.replace("R$", "").replace(".", "").replace(",", ".").strip())
                    else:
                        v_parc = float(v_raw)
                except Exception:
                    v_parc = valor_total / max(qtd_parcelas, 1)

                identificacao_unica = f"MOV{movimento.id}-PARC{num_parc}"
                parcela_obj = ParcelaConta(
                    movimento_id=movimento.id,
                    identificacao=identificacao_unica,
                    numero_parcela=int(num_parc),
                    data_vencimento=venc,
                    valor=v_parc,
                    status="PENDENTE"
                )
                db.add(parcela_obj)
                parcelas_criadas.append(identificacao_unica)
        else:
            # Parcela única
            venc = dados.get("data_vencimento") or ""
            identificacao_unica = f"MOV{movimento.id}-PARC1"
            parcela_obj = ParcelaConta(
                movimento_id=movimento.id,
                identificacao=identificacao_unica,
                numero_parcela=1,
                data_vencimento=venc,
                valor=valor_total,
                status="PENDENTE"
            )
            db.add(parcela_obj)
            parcelas_criadas.append(identificacao_unica)

        db.commit()

        # 5. Informar ao usuário que o registro foi lançado com sucesso
        return {
            "sucesso": True,
            "mensagem": "REGISTRO LANÇADO COM SUCESSO!",
            "detalhes": {
                "movimento_id": movimento.id,
                "tipo_movimento": movimento.tipo,
                "numero_nota": movimento.numero_nota,
                "valor_total": movimento.valor_total,
                "fornecedor": {
                    "id": fornecedor.id,
                    "nome": fornecedor.razao_social,
                    "criado_agora": fornecedor_criado
                },
                "faturado": {
                    "id": faturado.id,
                    "nome": faturado.razao_social,
                    "criado_agora": faturado_criado
                },
                "despesa": {
                    "id": despesa.id,
                    "descricao": despesa.descricao,
                    "criada_agora": despesa_criada
                },
                "parcelas": parcelas_criadas
            }
        }

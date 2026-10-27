"""Módulo do Agente 2 (Agent2): Persistência, Verificação e Lançamento de Dados no Banco.

Estrutura Modular Obrigatória:
- agents/agent2/persistencia_dados.py
- Classe Agent2 com:
    - verificar_existencia(dados, db)
    - persistir_movimento(dados, db)
"""

import re
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from database.models import Classificacao, MovimentoConta, ParcelaConta, Pessoa


def normalizar_documento(doc: Optional[str]) -> str:
    """Remove pontuação e caracteres não numéricos de CPF e CNPJ."""
    if not doc:
        return ""
    return re.sub(r"\D", "", str(doc))


class Agent2:
    """Agente de Verificação, Análise e Persistência de Dados Fiscais/Financeiros."""

    def __init__(self):
        pass

    def verificar_existencia(self, dados: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Consulta no Banco de Dados se Fornecedor, Faturado e Despesa existem.
        
        Atende às regras da 2ª Etapa (Páginas 1 e 2 do Documento UniRV):
        - FORNECEDOR: Deve consultar no Banco de Dados e informar se o FORNECEDOR existe ou não
        - FATURADO: Deve consultar no Banco de Dados e informar se o FATURADO existe ou não
        - DESPESA: Deve consultar no Banco de Dados e informar se a classificação da DESPESA existe ou não
        """
        # 1. FORNECEDOR
        fornecedor_dados = dados.get("fornecedor", {})
        razao_forn = (
            fornecedor_dados.get("razao_social")
            or fornecedor_dados.get("nome_fantasia")
            or fornecedor_dados.get("fantasia")
            or "FORNECEDOR NÃO INFORMADO"
        ).strip()
        fantasia_forn = (fornecedor_dados.get("nome_fantasia") or fornecedor_dados.get("fantasia") or "").strip()
        cnpj_forn = (fornecedor_dados.get("cnpj") or fornecedor_dados.get("documento") or "").strip()
        cnpj_limpo = normalizar_documento(cnpj_forn)

        fornecedor_existente = None

        # Busca por CNPJ primeiro (mais preciso)
        if cnpj_limpo:
            candidatos = db.query(Pessoa).filter(
                Pessoa.tipo.in_(["CLIENTE-FORNECEDOR", "FORNECEDOR", "CLIENTE"])
            ).all()
            for p in candidatos:
                if normalizar_documento(p.documento) == cnpj_limpo:
                    fornecedor_existente = p
                    break

        # Busca por Razão Social ou Nome Fantasia se não encontrou por CNPJ
        if not fornecedor_existente and razao_forn:
            fornecedor_existente = db.query(Pessoa).filter(
                Pessoa.tipo.in_(["CLIENTE-FORNECEDOR", "FORNECEDOR", "CLIENTE"]),
                Pessoa.razao_social.ilike(razao_forn)
            ).first()

        resultado_fornecedor = {
            "nome": razao_forn,
            "nome_fantasia": fantasia_forn,
            "documento": cnpj_forn or "NÃO INFORMADO",
            "cnpj": cnpj_forn or "NÃO INFORMADO",
            "existe": fornecedor_existente is not None,
            "id": fornecedor_existente.id if fornecedor_existente else None,
            "status": fornecedor_existente.status if fornecedor_existente else None
        }

        # 2. FATURADO
        faturado_dados = dados.get("faturado", {})
        nome_fat = (
            faturado_dados.get("nome")
            or faturado_dados.get("razao_social")
            or "FATURADO NÃO INFORMADO"
        ).strip()
        cpf_fat = (faturado_dados.get("cpf") or faturado_dados.get("documento") or "").strip()
        cpf_limpo = normalizar_documento(cpf_fat)

        faturado_existente = None

        if cpf_limpo:
            candidatos = db.query(Pessoa).filter(Pessoa.tipo == "FATURADO").all()
            for p in candidatos:
                if normalizar_documento(p.documento) == cpf_limpo:
                    faturado_existente = p
                    break

        if not faturado_existente and nome_fat:
            faturado_existente = db.query(Pessoa).filter(
                Pessoa.tipo == "FATURADO",
                Pessoa.razao_social.ilike(nome_fat)
            ).first()

        resultado_faturado = {
            "nome": nome_fat,
            "documento": cpf_fat or "NÃO INFORMADO",
            "cpf": cpf_fat or "NÃO INFORMADO",
            "existe": faturado_existente is not None,
            "id": faturado_existente.id if faturado_existente else None,
            "status": faturado_existente.status if faturado_existente else None
        }

        # 3. DESPESA
        classif_dados = dados.get("classificacao_despesa", {})
        if isinstance(classif_dados, list) and len(classif_dados) > 0:
            classif_dados = classif_dados[0]

        categoria_despesa = (
            dados.get("tipo_despesa")
            or (classif_dados.get("categoria") if isinstance(classif_dados, dict) else None)
            or "MANUTENÇÃO E OPERAÇÃO"
        ).strip()

        despesa_existente = db.query(Classificacao).filter(
            Classificacao.tipo == "DESPESA",
            Classificacao.descricao.ilike(categoria_despesa)
        ).first()

        resultado_despesa = {
            "descricao": categoria_despesa,
            "categoria": categoria_despesa,
            "existe": despesa_existente is not None,
            "id": despesa_existente.id if despesa_existente else None,
            "status": despesa_existente.status if despesa_existente else None
        }

        return {
            "fornecedor": resultado_fornecedor,
            "faturado": resultado_faturado,
            "despesa": resultado_despesa
        }

    # Alias para compatibilidade
    consultar_entidades = verificar_existencia

    def persistir_movimento(self, dados: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Executa os 5 passos obrigatórios após a verificação (Página 2):
        
        1. CRIAR O NOVO FORNECEDOR (se for o caso)
        2. CRIAR O NOVO FATURADO (se for o caso)
        3. CRIAR NOVA DESPESA (se for o caso)
        4. CRIAR UM NOVO REGISTRO DO MOVIMENTO E SUA PARCELA
        5. INFORMAR AO USUÁRIO QUE REGISTRO FOI LANÇADO COM SUCESSO.
        """
        analise = self.verificar_existencia(dados, db)

        # 1. CRIAR NOVO FORNECEDOR (se for o caso)
        forn_info = analise["fornecedor"]
        if forn_info["existe"]:
            fornecedor = db.query(Pessoa).get(forn_info["id"])
            fornecedor_criado = False
        else:
            doc = forn_info["documento"] if forn_info["documento"] != "NÃO INFORMADO" else ""
            fornecedor = Pessoa(
                tipo="CLIENTE-FORNECEDOR",
                razao_social=forn_info["nome"],
                nome_fantasia=forn_info.get("nome_fantasia", ""),
                documento=doc,
                status="ATIVO"  # Regra g: no CREATE campo status == ATIVO
            )
            db.add(fornecedor)
            db.flush()
            fornecedor_criado = True

        # 2. CRIAR NOVO FATURADO (se for o caso)
        fat_info = analise["faturado"]
        if fat_info["existe"]:
            faturado = db.query(Pessoa).get(fat_info["id"])
            faturado_criado = False
        else:
            doc = fat_info["documento"] if fat_info["documento"] != "NÃO INFORMADO" else ""
            faturado = Pessoa(
                tipo="FATURADO",
                razao_social=fat_info["nome"],
                nome_fantasia="",
                documento=doc,
                status="ATIVO"
            )
            db.add(faturado)
            db.flush()
            faturado_criado = True

        # 3. CRIAR NOVA DESPESA (se for o caso)
        desp_info = analise["despesa"]
        if desp_info["existe"]:
            despesa = db.query(Classificacao).get(desp_info["id"])
            despesa_criada = False
        else:
            despesa = Classificacao(
                tipo="DESPESA",
                descricao=desp_info["descricao"].strip().upper(),
                status="ATIVO"
            )
            db.add(despesa)
            db.flush()
            despesa_criada = True

        # 4. CRIAR NOVO REGISTRO DO MOVIMENTO E SUA PARCELA
        valor_raw = dados.get("valor_total", 0.0)
        try:
            if isinstance(valor_raw, str):
                v_limpo = valor_raw.replace("R$", "").replace(".", "").replace(",", ".").strip()
                valor_total = float(v_limpo)
            else:
                valor_total = float(valor_raw)
        except Exception:
            valor_total = 0.0

        num_doc = str(dados.get("numero_documento") or dados.get("numero_nota") or dados.get("numero") or "")
        dt_emissao = str(dados.get("data_emissao") or "")

        # Montagem do resumo de descrição de produtos
        produtos_list = dados.get("descricao_produtos") or dados.get("itens") or []
        resumo_produtos = ""
        if isinstance(produtos_list, list) and produtos_list:
            if isinstance(produtos_list[0], dict):
                descs = [it.get("descricao", "") for it in produtos_list if it.get("descricao")]
                resumo_produtos = ", ".join(descs[:3])
            else:
                resumo_produtos = ", ".join([str(p) for p in produtos_list[:3]])

        movimento = MovimentoConta(
            tipo="APAGAR",
            fornecedor_id=fornecedor.id,
            faturado_id=faturado.id,
            numero_documento=num_doc,
            data_emissao=dt_emissao,
            valor_total=valor_total,
            descricao_produtos=resumo_produtos[:490],
            status="ATIVO"
        )
        movimento.classificacoes.append(despesa)
        db.add(movimento)
        db.flush()

        # 4.1 PARCELAS DO MOVIMENTO
        parcelas_dados = dados.get("parcelas", [])
        qtd_parcelas = int(dados.get("quantidade_parcelas") or 1)
        parcelas_criadas = []

        if parcelas_dados and isinstance(parcelas_dados, list):
            for idx, p in enumerate(parcelas_dados, start=1):
                num_p = int(p.get("numero", idx) or idx)
                venc = p.get("data_vencimento") or dados.get("data_vencimento") or ""
                v_parc_raw = p.get("valor", valor_total / max(qtd_parcelas, 1))
                try:
                    if isinstance(v_parc_raw, str):
                        v_parc = float(v_parc_raw.replace("R$", "").replace(".", "").replace(",", ".").strip())
                    else:
                        v_parc = float(v_parc_raw)
                except Exception:
                    v_parc = valor_total / max(qtd_parcelas, 1)

                identificacao = f"MOV{movimento.id}-PARC{num_p}"
                parcela = ParcelaConta(
                    movimento_id=movimento.id,
                    numero_parcela=num_p,
                    identificacao=identificacao,
                    data_vencimento=venc,
                    valor=v_parc,
                    status="ATIVO"
                )
                db.add(parcela)
                parcelas_criadas.append(identificacao)
        else:
            # Parcela Única
            venc = dados.get("data_vencimento") or ""
            identificacao = f"MOV{movimento.id}-PARC1"
            parcela = ParcelaConta(
                movimento_id=movimento.id,
                numero_parcela=1,
                identificacao=identificacao,
                data_vencimento=venc,
                valor=valor_total,
                status="ATIVO"
            )
            db.add(parcela)
            parcelas_criadas.append(identificacao)

        db.commit()

        # 5. INFORMAR AO USUÁRIO QUE REGISTRO FOI LANÇADO COM SUCESSO (Página 2)
        return {
            "sucesso": True,
            "mensagem": "REGISTRO FOI LANÇADO COM SUCESSO!",
            "detalhes": {
                "movimento_id": movimento.id,
                "tipo": movimento.tipo,
                "numero_documento": movimento.numero_documento,
                "valor_total": movimento.valor_total,
                "fornecedor": {
                    "id": fornecedor.id,
                    "razao_social": fornecedor.razao_social,
                    "documento": fornecedor.documento,
                    "criado_agora": fornecedor_criado
                },
                "faturado": {
                    "id": faturado.id,
                    "razao_social": faturado.razao_social,
                    "documento": faturado.documento,
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

    # Alias para compatibilidade
    lancar_no_banco = persistir_movimento


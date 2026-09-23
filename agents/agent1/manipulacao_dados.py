"""Módulo do Agente 1 (Agent1): Manipulação, Extração e Classificação de Notas Fiscais (PDF).

Arquitetura de Agentes Inteligentes (Russell & Norvig):
1. Perceber (Perception): Capta os dados do ambiente (leitura do arquivo PDF da NF).
2. Processar (Processing): Interpreta o texto bruto e estrutura os dados preliminares.
3. Decidir (Decision): Emprega LLM (Google Gemini) ou regras especializadas para classificar a despesa.
4. Agir (Action): Monta e devolve a resposta final no formato JSON estruturado.
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import PyPDF2
from dotenv import load_dotenv

# Carrega variáveis de ambiente (.env)
load_dotenv()

# Categorias oficiais de despesas conforme especificação do projeto ESW424 (UniRV)
CATEGORIAS_DESPESAS = {
    "INSUMOS AGRÍCOLAS": [
        "Sementes",
        "Fertilizantes",
        "Defensivos Agrícolas",
        "Corretivos"
    ],
    "MANUTENÇÃO E OPERAÇÃO": [
        "Combustíveis e Lubrificantes",
        "Peças, Parafusos, Componentes Mecânicos",
        "Manutenção de Máquinas e Equipamentos",
        "Pneus, Filtros, Correias",
        "Ferramentas e Utensílios"
    ],
    "RECURSOS HUMANOS": [
        "Mão de Obra Temporária",
        "Salários e Encargos"
    ],
    "SERVIÇOS OPERACIONAIS": [
        "Frete e Transporte",
        "Colheita Terceirizada",
        "Secagem e Armazenagem",
        "Pulverização e Aplicação"
    ],
    "INFRAESTRUTURA E UTILIDADES": [
        "Energia Elétrica",
        "Arrendamento de Terras",
        "Construções e Reformas",
        "Materiais de Construção"
    ],
    "ADMINISTRATIVAS": [
        "Honorários (Contábeis, Advocatícios, Agronômicos)",
        "Despesas Bancárias e Financeiras"
    ],
    "SEGUROS E PROTEÇÃO": [
        "Seguro Agrícola",
        "Seguro de Ativos (Máquinas/Veículos)",
        "Seguro Prestamista"
    ],
    "IMPOSTOS E TAXAS": [
        "ITR, IPTU, IPVA, INCRA-CCIR"
    ],
    "INVESTIMENTOS": [
        "Aquisição de Máquinas e Implementos",
        "Aquisição de Veículos",
        "Aquisição de Imóveis",
        "Infraestrutura Rural"
    ]
}


class Agent1:
    """Agente de IA responsável pela percepção, extração de dados fiscais

    e classificação de despesas a partir de arquivos PDF de Notas Fiscais.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Inicializa o agente e configura o acesso ao Google Gemini."""
        self.api_key = (
            api_key
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
            or ""
        )
        self.client_ready = False

        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client_ready = True
            except Exception as e:
                print(f"[Agent1] Aviso ao configurar Google Gemini: {e}")

    # =========================================================================
    # CICLO DO AGENTE: 1. PERCEBER (Perception)
    # =========================================================================
    def perceber(self, file_path: str) -> str:
        """Captura o estado do ambiente extraindo o conteúdo textual bruto do PDF."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        texto_completo = []
        try:
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for index, page in enumerate(reader.pages):
                    texto_pagina = page.extract_text() or ""
                    texto_completo.append(texto_pagina)
        except Exception as e:
            raise ValueError(f"Falha ao ler o PDF da nota fiscal: {e}")

        conteudo = "\n".join(texto_completo).strip()
        if not conteudo:
            raise ValueError("O arquivo PDF está vazio ou não contém texto extraível.")

        return conteudo

    # =========================================================================
    # CICLO DO AGENTE: 2. PROCESSAR (Processing / Interpreting)
    # =========================================================================
    def processar(self, texto_bruto: str) -> Dict[str, Any]:
        """Processa e estrutura dados preliminares a partir do texto do documento."""
        linhas = [linha.strip() for linha in texto_bruto.split("\n") if linha.strip()]
        texto_limpo = "\n".join(linhas)

        dados_preliminares = self._extrair_por_heuristica(texto_limpo)
        return {
            "texto_limpo": texto_limpo,
            "dados_preliminares": dados_preliminares
        }

    # =========================================================================
    # CICLO DO AGENTE: 3. DECIDIR (Decision Making)
    # =========================================================================
    def decidir(self, processado: Dict[str, Any], file_path: Optional[str] = None) -> Dict[str, Any]:
        """Decide a classificação e a estrutura final dos dados da NF utilizando

        Google Gemini com fallback para o motor especialista em regras de negócio.
        """
        texto = processado["texto_limpo"]
        dados_base = processado["dados_preliminares"]

        # Se houver chave configurada do Gemini, invoca o modelo de IA
        if self.client_ready:
            try:
                dados_ia = self._chamar_gemini(texto)
                if dados_ia and isinstance(dados_ia, dict):
                    return self._harmonizar_dados(dados_ia, dados_base)
            except Exception as e:
                print(f"[Agent1] Falha na chamada ao Gemini, utilizando motor de contingência: {e}")

        # Se Gemini não estiver disponível ou falhar, utiliza classificação especialista por regras
        classificacao = self._classificar_despesa_por_regras(
            dados_base.get("descricao_produtos", []),
            texto
        )
        dados_base["tipo_despesa"] = classificacao["categoria"]
        dados_base["classificacao_despesa"] = [classificacao]
        return dados_base

    # =========================================================================
    # CICLO DO AGENTE: 4. AGIR (Action)
    # =========================================================================
    def agir(self, dados_finais: Dict[str, Any]) -> Dict[str, Any]:
        """Executa a ação de formatar, validar e entregar o JSON padronizado."""
        resultado = {
            "fornecedor": {
                "razao_social": dados_finais.get("fornecedor", {}).get("razao_social") or "NÃO IDENTIFICADO",
                "fantasia": dados_finais.get("fornecedor", {}).get("fantasia") or "",
                "cnpj": dados_finais.get("fornecedor", {}).get("cnpj") or ""
            },
            "faturado": {
                "nome": dados_finais.get("faturado", {}).get("nome") or "NÃO IDENTIFICADO",
                "cpf": dados_finais.get("faturado", {}).get("cpf") or ""
            },
            "numero_nota": str(dados_finais.get("numero_nota") or ""),
            "data_emissao": dados_finais.get("data_emissao") or "",
            "descricao_produtos": dados_finais.get("descricao_produtos") or [],
            "quantidade_parcelas": int(dados_finais.get("quantidade_parcelas") or 1),
            "parcelas": dados_finais.get("parcelas") or [
                {
                    "numero": 1,
                    "data_vencimento": dados_finais.get("data_vencimento") or "",
                    "valor": float(dados_finais.get("valor_total") or 0.0)
                }
            ],
            "data_vencimento": dados_finais.get("data_vencimento") or "",
            "valor_total": float(dados_finais.get("valor_total") or 0.0),
            "tipo_despesa": dados_finais.get("tipo_despesa") or "MANUTENÇÃO E OPERAÇÃO",
            "classificacao_despesa": dados_finais.get("classificacao_despesa") or [
                {
                    "categoria": dados_finais.get("tipo_despesa") or "MANUTENÇÃO E OPERAÇÃO",
                    "subcategoria": "Peças, Parafusos, Componentes Mecânicos",
                    "justificativa": "Classificação baseada nos itens da nota fiscal."
                }
            ]
        }

        # Aliases de compatibilidade e facilidade de integração
        resultado["numero"] = resultado["numero_nota"]
        resultado["dataEmissao"] = resultado["data_emissao"]
        resultado["itens"] = resultado["descricao_produtos"]
        resultado["cliente"] = resultado["faturado"]

        return resultado

    # =========================================================================
    # MÉTODO PRINCIPAL EXIGIDO: extrair_dados(file_path)
    # =========================================================================
    def extrair_dados(self, file_path: str) -> Dict[str, Any]:
        """Método principal exigido nos critérios de avaliação.

        Executa o ciclo completo do Agente Inteligente:
        Perceber -> Processar -> Decidir -> Agir.
        """
        # 1. Perceber
        texto_bruto = self.perceber(file_path)

        # 2. Processar
        processado = self.processar(texto_bruto)

        # 3. Decidir
        decisao = self.decidir(processado, file_path=file_path)

        # 4. Agir
        resultado_final = self.agir(decisao)

        return resultado_final

    # =========================================================================
    # INTEGRAÇÃO COM GOOGLE GEMINI (LLM)
    # =========================================================================
    def _chamar_gemini(self, texto_nf: str) -> Optional[Dict[str, Any]]:
        """Invoca o modelo Google Gemini para extrair e classificar a Nota Fiscal."""
        import google.generativeai as genai

        prompt_sistema = f"""
Você é um Agente Especialista em Engenharia de Software e Processamento de Documentos Fiscais.
Sua missão é ler o texto extraído de uma Nota Fiscal (DANFE - Contas a Pagar) e gerar um JSON com:
1. Extração exata dos campos obrigatórios.
2. Classificação assertiva da DESPESA baseada estritamente nos produtos adquiridos.

REGRAS DE CLASSIFICAÇÃO DE DESPESA (CATEGORIAS OBRIGATÓRIAS):
{json.dumps(CATEGORIAS_DESPESAS, indent=2, ensure_ascii=False)}

Exemplos de classificação:
- Compra de Óleo Diesel, Combustíveis, Graxa, Rolamentos, Parafusos -> Categoria: "MANUTENÇÃO E OPERAÇÃO"
- Compra de Tubos, Conexões, Material Hidráulico, Cimento -> Categoria: "INFRAESTRUTURA E UTILIDADES"
- Sementes de Soja/Milho, Adubo, Fertilizante, Herbicida -> Categoria: "INSUMOS AGRÍCOLAS"
- Frete de grãos, caminhão de transporte -> Categoria: "SERVIÇOS OPERACIONAIS"

FORMATO JSON OBRIGATÓRIO DE SAÍDA:
{{
  "fornecedor": {{
    "razao_social": "Razão Social do Emitente",
    "fantasia": "Nome Fantasia (se houver)",
    "cnpj": "00.000.000/0000-00"
  }},
  "faturado": {{
    "nome": "Nome Completo do Destinatário",
    "cpf": "000.000.000-00 (ou CNPJ se faturado para PJ)"
  }},
  "numero_nota": "Número da NF (ex: 000.084.682)",
  "data_emissao": "DD/MM/AAAA",
  "descricao_produtos": [
    {{
      "codigo": "código se houver",
      "descricao": "Nome/Descrição do produto",
      "quantidade": 1.0,
      "unidade": "UN",
      "valor_unitario": 0.0,
      "valor_total": 0.0
    }}
  ],
  "quantidade_parcelas": 1,
  "parcelas": [
    {{
      "numero": 1,
      "data_vencimento": "DD/MM/AAAA",
      "valor": 0.0
    }}
  ],
  "data_vencimento": "DD/MM/AAAA",
  "valor_total": 0.0,
  "tipo_despesa": "NOME EXATO DA CATEGORIA PRINCIPAL (ex: MANUTENÇÃO E OPERAÇÃO)",
  "classificacao_despesa": [
    {{
      "categoria": "NOME EXATO DA CATEGORIA",
      "subcategoria": "Subcategoria correspondente",
      "justificativa": "Explicação técnica sucinta do porquê os produtos se enquadram nesta categoria"
    }}
  ]
}}

Responda APENAS com o objeto JSON válido, sem comentários ou texto adicional.
"""

        prompt_usuario = f"Aqui está o texto da Nota Fiscal:\n\n{texto_nf}"

        # Modelos com fallback sequencial
        modelos = [
            "gemini-1.5-flash",
            "gemini-2.0-flash",
            "gemini-2.5-flash",
            "gemini-1.5-pro"
        ]

        for nome_modelo in modelos:
            try:
                model = genai.GenerativeModel(
                    model_name=nome_modelo,
                    system_instruction=prompt_sistema,
                    generation_config={"response_mime_type": "application/json"}
                )
                response = model.generate_content(prompt_usuario)
                texto_resposta = response.text.strip()
                if texto_resposta.startswith("```json"):
                    texto_resposta = texto_resposta[7:]
                if texto_resposta.endswith("```"):
                    texto_resposta = texto_resposta[:-3]
                dados = json.loads(texto_resposta.strip())
                if isinstance(dados, dict):
                    return dados
            except Exception as e:
                print(f"[Agent1] Erro ao consultar modelo {nome_modelo}: {e}")
                continue

        return None

    # =========================================================================
    # MOTOR DE EXTRAÇÃO E CLASSIFICAÇÃO DETERMINÍSTICO (Contingência / Regras)
    # =========================================================================
    def _extrair_por_heuristica(self, texto: str) -> Dict[str, Any]:
        """Extração estruturada de dados da DANFE."""
        dados = {
            "fornecedor": {"razao_social": "", "fantasia": "", "cnpj": ""},
            "faturado": {"nome": "", "cpf": ""},
            "numero_nota": "",
            "data_emissao": "",
            "descricao_produtos": [],
            "quantidade_parcelas": 1,
            "parcelas": [],
            "data_vencimento": "",
            "valor_total": 0.0,
            "tipo_despesa": "",
            "classificacao_despesa": []
        }

        # 1. Número da Nota
        match_numero = re.search(r"No\.?\s*([0-9]{3}\.?[0-9]{3}\.?[0-9]{3}|[0-9]{1,9})", texto, re.IGNORECASE)
        if match_numero:
            dados["numero_nota"] = match_numero.group(1).strip()

        # 2. Fornecedor / Emitente
        match_rec = re.search(r"RECEBI\(EMOS\)\s+DE\s+([^,]+),", texto, re.IGNORECASE)
        if match_rec:
            razao = match_rec.group(1).strip()
            dados["fornecedor"]["razao_social"] = razao
            # Cria nome fantasia elegante
            fantasia = re.sub(r"\s+(?:LTDA|S/A|SA|ME|EPP)\b.*", "", razao, flags=re.IGNORECASE).strip()
            dados["fornecedor"]["fantasia"] = fantasia

        cnpjs = re.findall(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", texto)
        if cnpjs:
            dados["fornecedor"]["cnpj"] = cnpjs[0]

        # 3. Faturado / Destinatário
        match_dest = re.search(
            r"DESTINAT[AÁ]RIO/REMETENTE\s*(?:NOME/RAZ[AÃ]O\s*SOCIAL)?\s*\n\s*([^\n]+)",
            texto,
            re.IGNORECASE
        )
        if match_dest:
            nome_candidato = match_dest.group(1).strip()
            nome_candidato = re.sub(r"C\.?N\.?P\.?J\.?|C\.?P\.?F\.?", "", nome_candidato, flags=re.IGNORECASE).strip()
            nome_candidato = re.sub(r"[/\\]+", "", nome_candidato).strip()
            if not any(k in nome_candidato.upper() for k in ["ENDEREÇO", "BAIRRO", "CEP", "MUNICIPIO"]):
                dados["faturado"]["nome"] = nome_candidato

        cpfs = re.findall(r"\d{3}\.\d{3}\.\d{3}-\d{2}", texto)
        if cpfs:
            dados["faturado"]["cpf"] = cpfs[0]

        # 4. Data de Emissão
        datas = re.findall(r"\b(\d{2}/\d{2}/\d{4})\b", texto)
        if datas:
            dados["data_emissao"] = datas[0]

        # 5. Fatura / Duplicatas / Vencimento
        match_fat = re.search(
            r"(?:FATURA/DUPLICATAS|DUPLICATAS|VENCIMENTO)[^\n]*\n?([^\n]+)",
            texto,
            re.IGNORECASE
        )
        if match_fat:
            linha_fat = match_fat.group(0) + " " + match_fat.group(1)
            match_venc = re.search(r"(\d{2}/\d{2}/\d{4})", linha_fat)
            if match_venc:
                dados["data_vencimento"] = match_venc.group(1)

        if not dados["data_vencimento"] and len(datas) > 1:
            dados["data_vencimento"] = datas[1]

        # 6. Valor Total da Nota
        match_total = re.search(
            r"VALOR\s+TOTAL\s+DA\s+NOTA[^\d]*([\d\.]+(?:,\d{2}))",
            texto,
            re.IGNORECASE
        )
        if match_total:
            val_str = match_total.group(1).replace(".", "").replace(",", ".")
            try:
                dados["valor_total"] = float(val_str)
            except ValueError:
                pass
        else:
            valores = re.findall(r"\b\d{1,3}(?:\.\d{3})*,\d{2}\b", texto)
            if valores:
                try:
                    dados["valor_total"] = float(valores[-1].replace(".", "").replace(",", "."))
                except ValueError:
                    pass

        # 7. Produtos
        produtos = self._extrair_produtos_do_texto(texto)
        dados["descricao_produtos"] = produtos

        # 8. Parcelas
        dados["parcelas"] = [
            {
                "numero": 1,
                "data_vencimento": dados["data_vencimento"] or dados["data_emissao"],
                "valor": dados["valor_total"]
            }
        ]

        return dados

    def _extrair_produtos_do_texto(self, texto: str) -> List[Dict[str, Any]]:
        """Extrai os produtos e serviços constantes no documento fiscal com precisão."""
        produtos = []
        linhas = texto.split("\n")

        for linha in linhas:
            linha_s = linha.strip()
            # Verifica se é uma linha com valores fiscais da DANFE (ex: ... 19,00 0,00 ITEM)
            partes = re.split(r"\s+\d{1,2},\d{2}\s+\d{1,2},\d{2}\s+", linha_s)
            if len(partes) >= 2:
                colunas_num = partes[0]
                item_str = partes[-1].strip()

                # Tenta separar o código e a descrição
                cod = ""
                desc = item_str
                match_code_desc = re.match(r"^([A-Za-z0-9/\-]+\d(?:/\d)?)\s*([A-ZÇÃÕÁÉÍÓÚ\s].+)$", item_str)
                if match_code_desc:
                    cod = match_code_desc.group(1).strip()
                    desc = match_code_desc.group(2).strip()

                # Tenta extrair unidade, quantidade e valores numéricos
                un = "UN"
                qtd = 1.0
                v_unit = 0.0
                v_total = 0.0

                match_un = re.search(r"(UN|PC|CX|KG|LT|M|PAR)(\d+)", colunas_num)
                if match_un:
                    un = match_un.group(1)
                    try:
                        qtd = float(match_un.group(2))
                    except ValueError:
                        qtd = 1.0

                # Pega valores decimais na linha
                decimais = re.findall(r"\d+(?:[.,]\d+)?", colunas_num)
                if decimais:
                    try:
                        v_total = float(decimais[-1].replace(",", "."))
                        v_unit = float(decimais[-2].replace(",", ".")) if len(decimais) > 1 else v_total
                    except ValueError:
                        pass

                produtos.append({
                    "codigo": cod,
                    "descricao": desc,
                    "unidade": un,
                    "quantidade": qtd,
                    "valor_unitario": v_unit,
                    "valor_total": v_total
                })
            else:
                # Caso alternativo: busca por itens conhecidos
                for termo in ["GRAXA", "ROLAMENTO", "BUCHA", "ANEL", "ESTOPA", "PANO", "LIMPADOR", "OLEO", "DIESEL"]:
                    if termo in linha_s.upper() and not any(p["descricao"] == linha_s for p in produtos):
                        produtos.append({
                            "codigo": "",
                            "descricao": linha_s,
                            "unidade": "UN",
                            "quantidade": 1.0,
                            "valor_unitario": 0.0,
                            "valor_total": 0.0
                        })
                        break

        if not produtos:
            produtos = [
                {
                    "codigo": "01",
                    "descricao": "PRODUTOS/SERVIÇOS CONFORME NOTA FISCAL",
                    "unidade": "UN",
                    "quantidade": 1.0,
                    "valor_unitario": 0.0,
                    "valor_total": 0.0
                }
            ]

        return produtos

    def _classificar_despesa_por_regras(self, produtos: List[Dict[str, Any]], texto: str) -> Dict[str, str]:
        """Classifica a despesa de acordo com as 9 categorias exigidas na disciplina."""
        texto_analise = " ".join([p.get("descricao", "") for p in produtos]) + " " + texto
        texto_analise = texto_analise.upper()

        # 1. MANUTENÇÃO E OPERAÇÃO
        termos_manutencao = [
            "GRAXA", "ROLAMENTO", "BUCHA", "ANEL", "PARAFUSO", "PEÇA", "PECAS",
            "OLEO", "LUBRIFICANTE", "DIESEL", "COMBUSTIVEL", "FILTRO", "CORREIA",
            "PNEU", "FERRAMENTA", "ESTOPA", "LIMPADOR", "SOLDA", "RETENTOR", "APOIO"
        ]
        if any(t in texto_analise for t in termos_manutencao):
            return {
                "categoria": "MANUTENÇÃO E OPERAÇÃO",
                "subcategoria": "Peças, Parafusos, Componentes Mecânicos e Lubrificantes",
                "justificativa": "Os produtos identificados na Nota Fiscal (peças mecânicas, graxa, rolamentos, anéis e utilitários) destinam-se à manutenção e operação de máquinas agrícolas."
            }

        # 2. INSUMOS AGRÍCOLAS
        termos_insumos = ["SEMENTE", "FERTILIZANTE", "ADUBO", "DEFENSIVO", "HERBICIDA", "FUNGICIDA", "INSETICIDA", "CALCARIO", "CORRETIVO"]
        if any(t in texto_analise for t in termos_insumos):
            return {
                "categoria": "INSUMOS AGRÍCOLAS",
                "subcategoria": "Sementes, Fertilizantes e Defensivos",
                "justificativa": "Identificada aquisição de insumos destinados ao cultivo e nutrição vegetal."
            }

        # 3. INFRAESTRUTURA E UTILIDADES
        termos_infra = ["ENERGIA", "ELETRICA", "HIDRAULICO", "TUBOS", "CONEXOES", "CIMENTO", "TIJOLO", "REFORMA", "CONSTRUCAO"]
        if any(t in texto_analise for t in termos_infra):
            return {
                "categoria": "INFRAESTRUTURA E UTILIDADES",
                "subcategoria": "Materiais de Construção e Instalações",
                "justificativa": "Identificada aquisição de materiais ou serviços para instalações, energia ou infraestrutura."
            }

        # 4. SERVIÇOS OPERACIONAIS
        termos_servicos = ["FRETE", "TRANSPORTE", "COLHEITA", "SECAGEM", "ARMAZENAGEM", "PULVERIZACAO"]
        if any(t in texto_analise for t in termos_servicos):
            return {
                "categoria": "SERVIÇOS OPERACIONAIS",
                "subcategoria": "Frete e Serviços Operacionais Agrícolas",
                "justificativa": "Identificada contratação de frete, colheita ou serviços operacionais."
            }

        # 5. ADMINISTRATIVAS
        termos_adm = ["HONORARIOS", "CONTABIL", "ADVOCATICIO", "AGRONOMICO", "TARIFA", "BANCARIA"]
        if any(t in texto_analise for t in termos_adm):
            return {
                "categoria": "ADMINISTRATIVAS",
                "subcategoria": "Honorários e Serviços Administrativos",
                "justificativa": "Identificada contratação de assessoria técnica, advocatícia, contábil ou financeira."
            }

        # 6. SEGUROS E PROTEÇÃO
        termos_seguros = ["SEGURO", "APOLICE", "SINISTRO", "PRESTAMISTA"]
        if any(t in texto_analise for t in termos_seguros):
            return {
                "categoria": "SEGUROS E PROTEÇÃO",
                "subcategoria": "Seguro Agrícola ou de Ativos",
                "justificativa": "Despesa referente a contratação ou renovação de cobertura de seguros."
            }

        # 7. IMPOSTOS E TAXAS
        termos_impostos = ["ITR", "IPTU", "IPVA", "INCRA", "CCIR", "TAXA", "TRIBUTO"]
        if any(t in texto_analise for t in termos_impostos):
            return {
                "categoria": "IMPOSTOS E TAXAS",
                "subcategoria": "Tributos e Taxas Rurais/Urbanas",
                "justificativa": "Pagamento de impostos, certidões ou taxas oficiais governamentais."
            }

        # 8. RECURSOS HUMANOS
        termos_rh = ["FOLHA", "SALARIO", "ENCARGO", "DIARIA", "RESCISAO", "TEMPORARIO"]
        if any(t in texto_analise for t in termos_rh):
            return {
                "categoria": "RECURSOS HUMANOS",
                "subcategoria": "Salários, Diárias e Encargos",
                "justificativa": "Despesa com mão de obra, contratação ou encargos trabalhistas."
            }

        # 9. INVESTIMENTOS
        termos_invest = ["TRATOR", "COLHEITADEIRA", "VEICULO", "CAMINHONETE", "IMPLEMENTO", "IMOVEL", "TERRA"]
        if any(t in texto_analise for t in termos_invest):
            return {
                "categoria": "INVESTIMENTOS",
                "subcategoria": "Aquisição de Máquinas e Implementos",
                "justificativa": "Identificada aquisição de ativo fixo / bem de capital."
            }

        return {
            "categoria": "MANUTENÇÃO E OPERAÇÃO",
            "subcategoria": "Geral de Operações",
            "justificativa": "Classificação padrão atribuída conforme contexto operacional da nota fiscal."
        }

    def _harmonizar_dados(self, dados_ia: Dict[str, Any], dados_base: Dict[str, Any]) -> Dict[str, Any]:
        """Harmoniza dados da IA com os dados extraídos da base para garantir completude."""
        resultado = dict(dados_ia)

        for campo in ["numero_nota", "data_emissao", "data_vencimento", "valor_total"]:
            if not resultado.get(campo) and dados_base.get(campo):
                resultado[campo] = dados_base[campo]

        for sub in ["fornecedor", "faturado"]:
            if sub not in resultado or not isinstance(resultado[sub], dict):
                resultado[sub] = dados_base.get(sub, {})
            else:
                for k, v in dados_base.get(sub, {}).items():
                    if not resultado[sub].get(k):
                        resultado[sub][k] = v

        if not resultado.get("descricao_produtos") and dados_base.get("descricao_produtos"):
            resultado["descricao_produtos"] = dados_base["descricao_produtos"]

        if not resultado.get("tipo_despesa"):
            classif = resultado.get("classificacao_despesa")
            if classif and isinstance(classif, list) and len(classif) > 0:
                resultado["tipo_despesa"] = classif[0].get("categoria", "MANUTENÇÃO E OPERAÇÃO")
            else:
                resultado["tipo_despesa"] = "MANUTENÇÃO E OPERAÇÃO"

        return resultado

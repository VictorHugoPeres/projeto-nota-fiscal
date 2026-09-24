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
                dados_ia = self._chamar_gemini(texto, file_path=file_path)
                if dados_ia and isinstance(dados_ia, dict):
                    return self._harmonizar_dados(dados_ia, dados_base)
            except Exception as e:
                print(f"[Agent1] Falha na chamada ao Gemini, utilizando motor de contingência: {e}")

        # Se Gemini não estiver disponível ou falhar, utiliza classificação especialista por regras
        classificacao_dict = self._classificar_despesa_por_regras(
            dados_base.get("descricao_produtos", []),
            texto
        )
        dados_base["tipo_despesa"] = classificacao_dict["categoria"]
        dados_base["classificacao_despesa"] = classificacao_dict["lista"]
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
    def _chamar_gemini(self, texto_nf: str, file_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Invoca o modelo Google Gemini para extrair e classificar a Nota Fiscal."""
        import google.generativeai as genai

        prompt_sistema = f"""
Você é um Agente Especialista em Engenharia de Software e Processamento de Documentos Fiscais.
Sua missão é analisar uma Nota Fiscal (DANFE - Contas a Pagar) e gerar um JSON com:
1. Extração exata dos campos obrigatórios (Fornecedor, Faturado, NF, Emissão, Produtos com quantidade e valores, Vencimento, Total).
2. Classificação assertiva da DESPESA baseada estritamente nos produtos adquiridos.

REGRAS DE CLASSIFICAÇÃO DE DESPESA (CATEGORIAS OBRIGATÓRIAS):
{json.dumps(CATEGORIAS_DESPESAS, indent=2, ensure_ascii=False)}

Exemplos de classificação:
- Compra de Óleo Diesel, Combustíveis, Graxa, Rolamentos, Parafusos -> Categoria: "MANUTENÇÃO E OPERAÇÃO"
- Aquisição de Tratores, Colheitadeiras, Implementos, Veículos -> Categoria: "INVESTIMENTOS"
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
      "codigo": "código do produto",
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
  "tipo_despesa": "NOME EXATO DA CATEGORIA PRINCIPAL (ex: MANUTENÇÃO E OPERAÇÃO ou INVESTIMENTOS)",
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

        # Prepara o conteúdo para o Gemini: multimodal (PDF) se o arquivo existir, ou texto
        conteudo_requisicao = []
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, "rb") as f:
                    pdf_bytes = f.read()
                conteudo_requisicao = [
                    {"mime_type": "application/pdf", "data": pdf_bytes},
                    "Por favor, analise cuidadosamente este documento fiscal eletrônico (DANFE em anexo), extraia todos os itens e gere o JSON estruturado de acordo com as instruções do sistema."
                ]
            except Exception as e:
                conteudo_requisicao = [f"Aqui está o texto da Nota Fiscal:\n\n{texto_nf}"]
        else:
            conteudo_requisicao = [f"Aqui está o texto da Nota Fiscal:\n\n{texto_nf}"]

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
                response = model.generate_content(conteudo_requisicao)
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
        """Extrai os produtos e serviços constantes no documento fiscal com precisão para múltiplos formatos de DANFE."""
        produtos = []
        linhas = texto.split("\n")

        for linha in linhas:
            linha_s = linha.strip()
            if not linha_s:
                continue

            # -----------------------------------------------------------------
            # Formato B1 (DANFE Agrotech: Código+Descrição no início e colunas fiscais concatenadas)
            # Exemplo: TRT001TRATOR COMPACTO 50CV 870191000005102UN 14.500,004.500,00...
            # -----------------------------------------------------------------
            m_agro = re.match(
                r"^([A-Za-z0-9/\.\-]+?\d+)([A-ZÇÃÕÁÉÍÓÚ].+?)\s+(\d{8})(\d{3})(\d{4})([A-Za-z]{2})\s+(.+)$",
                linha_s
            )
            if m_agro:
                cod = m_agro.group(1).strip()
                desc = m_agro.group(2).strip()
                un = m_agro.group(6).strip().upper()
                resto = m_agro.group(7).strip()
                matched_agro = False
                for q_len in [1, 2]:
                    cand_q = resto[:q_len]
                    if not cand_q.isdigit() or int(cand_q) == 0:
                        continue
                    q = float(cand_q)
                    sobrou = resto[q_len:]
                    moedas = list(re.finditer(r"([\d\.]+,\d{2})", sobrou))
                    if len(moedas) >= 2:
                        m1_val = float(moedas[0].group(1).replace(".", "").replace(",", "."))
                        m2_val = float(moedas[1].group(1).replace(".", "").replace(",", "."))
                        if abs((q * m1_val) - m2_val) < 0.1:
                            produtos.append({
                                "codigo": cod,
                                "descricao": desc,
                                "unidade": un,
                                "quantidade": q,
                                "valor_unitario": m1_val,
                                "valor_total": m2_val
                            })
                            matched_agro = True
                            break
                if matched_agro:
                    continue

            # -----------------------------------------------------------------
            # Formato B (Padrão: Código e Descrição no início da linha)
            # Exemplo: TRT001 TRATOR COMPACTO 50CV 87019100 000 5102 UN 1 4.500,00 4.500,00 ...
            # Exemplo 2: 33401 ESTOPA 530130000005102PC 1 6,28 6,28 ...
            # -----------------------------------------------------------------
            m_padrao = re.match(
                r"^([A-Za-z0-9/\.\-]+)\s+(.+?)\s+(\d{8})\s*(\d{3})\s*(\d{4})\s*([A-Za-z]{2})\s+(\d+(?:[.,]\d+)?)\s+([\d\.]+,\d{2})\s+([\d\.]+,\d{2})",
                linha_s
            )
            if m_padrao:
                cod = m_padrao.group(1).strip()
                desc = m_padrao.group(2).strip()
                un = m_padrao.group(6).strip().upper()
                try:
                    qtd = float(m_padrao.group(7).replace(",", "."))
                    v_unit = float(m_padrao.group(8).replace(".", "").replace(",", "."))
                    v_total = float(m_padrao.group(9).replace(".", "").replace(",", "."))
                except ValueError:
                    qtd, v_unit, v_total = 1.0, 0.0, 0.0

                produtos.append({
                    "codigo": cod,
                    "descricao": desc,
                    "unidade": un,
                    "quantidade": qtd,
                    "valor_unitario": v_unit,
                    "valor_total": v_total
                })
                continue

            # -----------------------------------------------------------------
            # Formato A (WebDANFe / eGestor invertido: NCM...UN... 19,00 0,00 CODIGO DESCRICAO)
            # Exemplo: 340319000005102UN180,3180,3172,2813,730,00 19,00 0,00 CQM20246GRAXA DE POLIUREIA MP SD 400G
            # -----------------------------------------------------------------
            m_fim = re.search(r"(\d{1,2},\d{2})\s+(\d{1,2},\d{2})\s+([A-Za-z0-9/\.\-]+?)([A-ZÇÃÕÁÉÍÓÚ\s].*)$", linha_s)
            if m_fim:
                cod_cand = m_fim.group(3).strip()
                desc_cand = m_fim.group(4).strip()

                # Separa código de descrição colada (ex: CQM20246GRAXA -> CQM20246 + GRAXA)
                m_sep = re.match(r"^([A-Za-z0-9/\-]+?\d+)([A-ZÇÃÕÁÉÍÓÚ\s].+)$", cod_cand + desc_cand)
                if m_sep:
                    cod = m_sep.group(1).strip()
                    desc = m_sep.group(2).strip()
                else:
                    cod = cod_cand
                    desc = desc_cand

                parte_ini = linha_s[:m_fim.start()].strip()
                un = "UN"
                m_un = re.search(r"\d{8}\d{3}\d{4}([A-Za-z]{2})", parte_ini)
                if m_un:
                    un = m_un.group(1).upper()
                    resto = parte_ini[m_un.end():].strip()
                else:
                    resto = parte_ini

                qtd = 1.0
                v_unit = 0.0
                v_total = 0.0

                # Decodifica valores colados (quantidade, unitário e total)
                for q_len in [1, 2]:
                    cand_q = resto[:q_len]
                    if not cand_q.isdigit() or int(cand_q) == 0:
                        continue
                    q = float(cand_q)
                    sobrou = resto[q_len:]
                    v1_idx = sobrou.find(",")
                    if v1_idx == -1:
                        continue
                    int_part = sobrou[:v1_idx].replace(".", "")
                    matched = False
                    for dec_len in range(2, 6):
                        if len(sobrou) < v1_idx + 1 + dec_len:
                            continue
                        dec_part = sobrou[v1_idx + 1 : v1_idx + 1 + dec_len]
                        if not dec_part.isdigit():
                            continue
                        try:
                            u_val = float(int_part + "." + dec_part)
                        except ValueError:
                            continue
                        exp_tot = round(q * u_val, 2)
                        p1 = f"{exp_tot:.2f}".replace(".", ",")
                        p_mil = f"{exp_tot:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if exp_tot >= 1000 else p1
                        resto_apos = sobrou[v1_idx + 1 + dec_len:]
                        if p1 in resto_apos or p_mil in resto_apos:
                            qtd = q
                            v_unit = round(u_val, 2)
                            v_total = exp_tot
                            matched = True
                            break
                    if matched:
                        break

                # Fallback secundário para capturar moedas
                if v_unit == 0.0:
                    moedas = re.findall(r"\d+(?:\.\d+)?,\d{2}", resto)
                    if moedas:
                        try:
                            v_unit = float(moedas[0].replace(".", "").replace(",", "."))
                            v_total = float(moedas[1].replace(".", "").replace(",", ".")) if len(moedas) > 1 else v_unit
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
                continue

            # -----------------------------------------------------------------
            # Formato C (Genérico por palavras-chave com captura de números)
            # -----------------------------------------------------------------
            for termo in [
                "TRATOR", "COLHEITADEIRA", "PNEU", "GRAXA", "ROLAMENTO", "BUCHA",
                "ANEL", "ESTOPA", "PANO", "LIMPADOR", "OLEO", "DIESEL", "FILTRO",
                "CORREIA", "PARAFUSO", "SEMENTE", "ADUBO", "FERTILIZANTE"
            ]:
                if termo in linha_s.upper() and not any(p["descricao"] == linha_s for p in produtos):
                    # Tenta extrair código inicial e valores decimais
                    m_gen_cod = re.match(r"^([A-Za-z0-9\-]+)\s+(.+)$", linha_s)
                    c_gen = m_gen_cod.group(1) if m_gen_cod else ""
                    d_gen = m_gen_cod.group(2) if m_gen_cod else linha_s

                    # Se d_gen tiver números fiscais no final, limpa
                    d_gen = re.sub(r"\s+\d{8}.*$", "", d_gen).strip()

                    moedas = re.findall(r"\d+(?:\.\d+)?,\d{2}", linha_s)
                    u_gen = 0.0
                    t_gen = 0.0
                    if moedas:
                        try:
                            t_gen = float(moedas[-1].replace(".", "").replace(",", "."))
                            u_gen = float(moedas[-2].replace(".", "").replace(",", ".")) if len(moedas) > 1 else t_gen
                        except ValueError:
                            pass

                    produtos.append({
                        "codigo": c_gen,
                        "descricao": d_gen,
                        "unidade": "UN",
                        "quantidade": 1.0,
                        "valor_unitario": u_gen,
                        "valor_total": t_gen
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

    def _classificar_despesa_por_regras(self, produtos: List[Dict[str, Any]], texto: str) -> Dict[str, Any]:
        """Classifica a despesa de acordo com as 9 categorias exigidas na disciplina ESW424."""
        texto_analise = " ".join([str(p.get("descricao", "")) for p in produtos]) + " " + texto
        texto_analise = texto_analise.upper()

        classificacoes = []

        # 1. INVESTIMENTOS (Maior prioridade: Bens de Capital, Maquinários, Implementos e Veículos)
        termos_invest = [
            "TRATOR", "COLHEITADEIRA", "IMPLEMENTO", "PLANTADEIRA", "VEICULO",
            "CAMINHONETE", "PULVERIZADOR AUTOPROPELIDO", "MAQUINA AGRICOLA",
            "AQUISIÇÃO DE MÁQUINAS", "IMPLEMENTOS"
        ]
        if any(t in texto_analise for t in termos_invest):
            classificacoes.append({
                "categoria": "INVESTIMENTOS",
                "subcategoria": "Aquisição de Máquinas e Implementos",
                "justificativa": "Identificada aquisição de ativo fixo / bem de capital (tratores, colheitadeiras ou maquinário agrícola)."
            })

        # 2. MANUTENÇÃO E OPERAÇÃO (Peças, Lubrificantes, Combustíveis, Pneus, Componentes Mecânicos)
        termos_manutencao = [
            "GRAXA", "ROLAMENTO", "BUCHA", "ANEL", "PARAFUSO", "PEÇA", "PECAS", "PEÇAS",
            "OLEO", "LUBRIFICANTE", "DIESEL", "COMBUSTIVEL", "FILTRO", "CORREIA",
            "PNEU", "FERRAMENTA", "ESTOPA", "LIMPADOR", "SOLDA", "RETENTOR", "APOIO"
        ]
        if any(t in texto_analise for t in termos_manutencao):
            classificacoes.append({
                "categoria": "MANUTENÇÃO E OPERAÇÃO",
                "subcategoria": "Peças, Parafusos, Componentes Mecânicos e Lubrificantes",
                "justificativa": "Os produtos identificados destinam-se à manutenção, lubrificação e operação de veículos e maquinários agrícolas."
            })

        # 3. INSUMOS AGRÍCOLAS (Sementes, Fertilizantes, Defensivos, Corretivos)
        termos_insumos = [
            "SEMENTE", "FERTILIZANTE", "ADUBO", "DEFENSIVO", "HERBICIDA",
            "FUNGICIDA", "INSETICIDA", "CALCARIO", "CORRETIVO"
        ]
        if any(t in texto_analise for t in termos_insumos):
            classificacoes.append({
                "categoria": "INSUMOS AGRÍCOLAS",
                "subcategoria": "Sementes, Fertilizantes e Defensivos",
                "justificativa": "Identificada aquisição de insumos destinados ao cultivo e nutrição vegetal."
            })

        # 4. INFRAESTRUTURA E UTILIDADES (Energia Elétrica, Construções, Materiais)
        termos_infra = [
            "ENERGIA", "ELETRICA", "HIDRAULICO", "TUBOS", "CONEXOES",
            "CIMENTO", "TIJOLO", "REFORMA", "CONSTRUCAO", "ARRENDAMENTO"
        ]
        if any(t in texto_analise for t in termos_infra):
            classificacoes.append({
                "categoria": "INFRAESTRUTURA E UTILIDADES",
                "subcategoria": "Materiais de Construção e Instalações",
                "justificativa": "Identificada aquisição de materiais ou serviços para instalações, energia ou infraestrutura rural."
            })

        # 5. SERVIÇOS OPERACIONAIS (Frete, Colheita, Secagem, Armazenagem, Pulverização)
        termos_servicos = [
            "FRETE", "TRANSPORTE", "COLHEITA TERCEIRIZADA", "SECAGEM",
            "ARMAZENAGEM", "PULVERIZACAO", "APLICACAO"
        ]
        if any(t in texto_analise for t in termos_servicos):
            classificacoes.append({
                "categoria": "SERVIÇOS OPERACIONAIS",
                "subcategoria": "Frete e Serviços Operacionais Agrícolas",
                "justificativa": "Identificada contratação de frete, colheita ou serviços operacionais especializados."
            })

        # 6. ADMINISTRATIVAS (Honorários Contábeis, Jurídicos, Agronômicos, Tarifas)
        termos_adm = [
            "HONORARIOS", "CONTABIL", "ADVOCATICIO", "AGRONOMICO",
            "TARIFA", "BANCARIA", "DESPESA FINANCEIRA"
        ]
        if any(t in texto_analise for t in termos_adm):
            classificacoes.append({
                "categoria": "ADMINISTRATIVAS",
                "subcategoria": "Honorários e Serviços Administrativos",
                "justificativa": "Identificada contratação de assessoria técnica, advocatícia, contábil ou despesa administrativa."
            })

        # 7. SEGUROS E PROTEÇÃO (Seguro Agrícola, Ativos, Prestamista)
        termos_seguros = ["SEGURO", "APOLICE", "SINISTRO", "PRESTAMISTA"]
        if any(t in texto_analise for t in termos_seguros):
            classificacoes.append({
                "categoria": "SEGUROS E PROTEÇÃO",
                "subcategoria": "Seguro Agrícola ou de Ativos",
                "justificativa": "Despesa referente a contratação ou renovação de apólice de seguros."
            })

        # 8. IMPOSTOS E TAXAS (ITR, IPTU, IPVA, INCRA-CCIR)
        termos_impostos = ["ITR", "IPTU", "IPVA", "INCRA", "CCIR", "TAXA", "TRIBUTO"]
        if any(t in texto_analise for t in termos_impostos):
            classificacoes.append({
                "categoria": "IMPOSTOS E TAXAS",
                "subcategoria": "Tributos e Taxas Rurais/Urbanas",
                "justificativa": "Pagamento de impostos, certidões ou taxas oficiais governamentais."
            })

        # 9. RECURSOS HUMANOS (Salários, Diárias, Mão de Obra)
        termos_rh = ["FOLHA", "SALARIO", "ENCARGO", "DIARIA", "RESCISAO", "TEMPORARIO", "MAO DE OBRA"]
        if any(t in texto_analise for t in termos_rh):
            classificacoes.append({
                "categoria": "RECURSOS HUMANOS",
                "subcategoria": "Salários, Diárias e Encargos",
                "justificativa": "Despesa com mão de obra, contratação ou encargos trabalhistas."
            })

        if not classificacoes:
            classificacoes.append({
                "categoria": "MANUTENÇÃO E OPERAÇÃO",
                "subcategoria": "Geral de Operações",
                "justificativa": "Classificação padrão atribuída conforme contexto operacional da nota fiscal."
            })

        return {
            "categoria": classificacoes[0]["categoria"],
            "subcategoria": classificacoes[0]["subcategoria"],
            "justificativa": classificacoes[0]["justificativa"],
            "lista": classificacoes
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

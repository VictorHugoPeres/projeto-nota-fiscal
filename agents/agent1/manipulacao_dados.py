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

# Dicionário de restauração de acentuação para textos extraídos de PDFs com encoding truncado
DICIONARIO_NORMALIZACAO_FISCAL = {
    "M\ufffdQUINAS": "MÁQUINAS",
    "MQUINAS": "MÁQUINAS",
    "AGR\ufffdCOLA": "AGRÍCOLA",
    "AGRCOLA": "AGRÍCOLA",
    "OPERA\ufffd\ufffdO": "OPERAÇÃO",
    "OPERA\ufffdO": "OPERAÇÃO",
    "OPERAO": "OPERAÇÃO",
    "SERVI\ufffdOS": "SERVIÇOS",
    "SERVIOS": "SERVIÇOS",
    "DESCRI\ufffd\ufffdO": "DESCRIÇÃO",
    "DESCRI\ufffdO": "DESCRIÇÃO",
    "DESCRIO": "DESCRIÇÃO",
    "C\ufffdDIGO": "CÓDIGO",
    "CDIGO": "CÓDIGO",
    "INSCRI\ufffd\ufffdO": "INSCRIÇÃO",
    "INSCRI\ufffdO": "INSCRIÇÃO",
    "INSCRIO": "INSCRIÇÃO",
    "DESTINAT\ufffdRIO": "DESTINATÁRIO",
    "DESTINATRIO": "DESTINATÁRIO",
    "EMISS\ufffd\ufffdO": "EMISSÃO",
    "EMISS\ufffdO": "EMISSÃO",
    "EMISSO": "EMISSÃO",
    "SA\ufffdDA": "SAÍDA",
    "SADA": "SAÍDA",
    "C\ufffdLCULO": "CÁLCULO",
    "CLCULO": "CÁLCULO",
    "L\ufffdQUIDO": "LÍQUIDO",
    "LQUIDO": "LÍQUIDO",
    "INFORMA\ufffd\ufffdES": "INFORMAÇÕES",
    "INFORMAES": "INFORMAÇÕES",
    "N\ufffdMERO": "NÚMERO",
    "NMERO": "NÚMERO",
    "AUTORIZA\ufffd\ufffdO": "AUTORIZAÇÃO",
    "AUTORIZA\ufffdO": "AUTORIZAÇÃO",
    "AUTORIZAO": "AUTORIZAÇÃO",
    "RAZ\ufffd\ufffdO": "RAZÃO",
    "RAZO": "RAZÃO",
    "ENDERE\ufffdO": "ENDEREÇO",
    "ENDEREO": "ENDEREÇO",
    "MUNIC\ufffdPIO": "MUNICÍPIO",
    "MUNICPIO": "MUNICÍPIO",
    "ELETR\ufffdNICA": "ELETRÔNICA",
    "ELETRNICA": "ELETRÔNICA",
    "POLIUR\ufffdIA": "POLIUREIA",
    "C\ufffdNICOS": "CÔNICOS",
    "CNICOS": "CÔNICOS",
    "IGUA\ufffdU": "IGUAÇU",
    "IGUAU": "IGUAÇU",
    "MANUTEN\ufffd\ufffdO": "MANUTENÇÃO",
    "MANUTENO": "MANUTENÇÃO",
    "PROTE\ufffd\ufffdO": "PROTEÇÃO",
    "PROTEO": "PROTEÇÃO",
    "SAL\ufffdRIOS": "SALÁRIOS",
    "SALRIOS": "SALÁRIOS",
    "DI\ufffdRIAS": "DIÁRIAS",
    "DIRIAS": "DIÁRIAS",
    "AP\ufffdLICE": "APÓLICE",
    "APLICE": "APÓLICE",
    "COM\ufffdRCIO": "COMÉRCIO",
    "COMERCIO": "COMÉRCIO",
    "IND\ufffdSTRIA": "INDÚSTRIA",
    "INDUSTRIA": "INDÚSTRIA"
}


def normalizar_texto_fiscal(texto: str) -> str:
    """Normaliza texto corrompido por extração de PDF sem mapa ToUnicode."""
    t = texto
    for k, v in DICIONARIO_NORMALIZACAO_FISCAL.items():
        t = t.replace(k, v)
    t = t.replace("\ufffd", "").replace("\xa0", " ")
    return t


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

        # Normaliza codificação e caracteres
        return normalizar_texto_fiscal(conteudo)

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
                "razao_social": normalizar_texto_fiscal(dados_finais.get("fornecedor", {}).get("razao_social") or "NÃO IDENTIFICADO"),
                "fantasia": normalizar_texto_fiscal(dados_finais.get("fornecedor", {}).get("fantasia") or ""),
                "cnpj": dados_finais.get("fornecedor", {}).get("cnpj") or ""
            },
            "faturado": {
                "nome": normalizar_texto_fiscal(dados_finais.get("faturado", {}).get("nome") or "NÃO IDENTIFICADO"),
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
            "tipo_despesa": normalizar_texto_fiscal(dados_finais.get("tipo_despesa") or "MANUTENÇÃO E OPERAÇÃO"),
            "classificacao_despesa": dados_finais.get("classificacao_despesa") or [
                {
                    "categoria": normalizar_texto_fiscal(dados_finais.get("tipo_despesa") or "MANUTENÇÃO E OPERAÇÃO"),
                    "subcategoria": "Peças, Componentes Mecânicos e Lubrificantes",
                    "justificativa": "Classificação baseada nos itens adquiridos na nota fiscal."
                }
            ]
        }

        # Garante normalização de strings em itens de produtos
        for item in resultado["descricao_produtos"]:
            if "descricao" in item:
                item["descricao"] = normalizar_texto_fiscal(item["descricao"])

        # Garante normalização de strings na lista de classificação
        for c in resultado["classificacao_despesa"]:
            if "categoria" in c:
                c["categoria"] = normalizar_texto_fiscal(c["categoria"])
            if "subcategoria" in c:
                c["subcategoria"] = normalizar_texto_fiscal(c["subcategoria"])
            if "justificativa" in c:
                c["justificativa"] = normalizar_texto_fiscal(c["justificativa"])

        # Aliases de compatibilidade e facilidade de integração exigidos na disciplina
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
- Compra de Óleo Diesel, Combustíveis, Graxa, Rolamentos, Parafusos, Pneus -> Categoria: "MANUTENÇÃO E OPERAÇÃO"
- Aquisição de Tratores, Colheitadeiras, Implementos, Veículos -> Categoria: "INVESTIMENTOS"
- Compra de Tubos, Conexões, Material Hidráulico, Cimento -> Categoria: "INFRAESTRUTURA E UTILIDADES"
- Sementes de Soja/Milho, Adubo, Fertilizante, Herbicida -> Categoria: "INSUMOS AGRÍCOLAS"
- Frete de grãos, caminhão de transporte contratado -> Categoria: "SERVIÇOS OPERACIONAIS"

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

        conteudo_requisicao = []
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, "rb") as f:
                    pdf_bytes = f.read()
                conteudo_requisicao = [
                    {"mime_type": "application/pdf", "data": pdf_bytes},
                    "Por favor, analise cuidadosamente este documento fiscal eletrônico (DANFE em anexo), extraia todos os itens e gere o JSON estruturado de acordo com as instruções do sistema."
                ]
            except Exception:
                conteudo_requisicao = [f"Aqui está o texto da Nota Fiscal:\n\n{texto_nf}"]
        else:
            conteudo_requisicao = [f"Aqui está o texto da Nota Fiscal:\n\n{texto_nf}"]

        modelos = [
            "gemini-3.6-flash",
            "gemini-flash-latest",
            "gemini-3.8-flash",
            "gemini-3.1-pro-preview",
            "gemini-pro-latest"
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
            dados["fornecedor"]["razao_social"] = normalizar_texto_fiscal(razao)
            fantasia = re.sub(r"\s+(?:LTDA|S/A|SA|ME|EPP)\b.*", "", razao, flags=re.IGNORECASE).strip()
            dados["fornecedor"]["fantasia"] = normalizar_texto_fiscal(fantasia)

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
                dados["faturado"]["nome"] = normalizar_texto_fiscal(nome_candidato)

        cpfs = re.findall(r"\d{3}\.\d{3}\.\d{3}-\d{2}", texto)
        if cpfs:
            dados["faturado"]["cpf"] = cpfs[0]

        # 4. Data de Emissão (prioriza campo DATA DA EMISSÃO)
        match_emissao = re.search(r"DATA\s+(?:DA\s+)?EMISS[ÃA]O\s*\n?\s*(\d{2}/\d{2}/\d{4})", texto, re.IGNORECASE)
        if match_emissao:
            dados["data_emissao"] = match_emissao.group(1)
        else:
            datas = re.findall(r"\b(\d{2}/\d{2}/\d{4})\b", texto)
            if datas:
                dados["data_emissao"] = datas[0]

        # 5. Fatura / Duplicatas / Vencimento
        duplicatas = re.findall(r"(\d{3}):\s*(\d{2}/\d{2}/\d{4})\s*(?:R\$\s*)?([\d\.]+,\d{2})", texto)
        if duplicatas:
            dados["quantidade_parcelas"] = len(duplicatas)
            dados["parcelas"] = []
            for d in duplicatas:
                num_parc = int(d[0])
                venc_parc = d[1]
                val_parc = float(d[2].replace(".", "").replace(",", "."))
                dados["parcelas"].append({
                    "numero": num_parc,
                    "data_vencimento": venc_parc,
                    "valor": val_parc
                })
            dados["data_vencimento"] = duplicatas[0][1]
        else:
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

            if not dados["data_vencimento"]:
                datas = re.findall(r"\b(\d{2}/\d{2}/\d{4})\b", texto)
                if len(datas) > 1:
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

        # Garante estrutura de parcelas se não foram extraídas pelo bloco duplicatas
        if not dados["parcelas"]:
            dados["parcelas"] = [
                {
                    "numero": 1,
                    "data_vencimento": dados["data_vencimento"] or dados["data_emissao"],
                    "valor": dados["valor_total"]
                }
            ]

        return dados

    def _extrair_produtos_do_texto(self, texto: str) -> List[Dict[str, Any]]:
        """Extrai os produtos e serviços da DANFE com alta precisão e resiliência."""
        produtos = []
        linhas = texto.split("\n")

        for linha in linhas:
            linha_s = linha.strip()
            if not linha_s:
                continue

            # Ignora cabeçalhos e rodapés conhecidos
            if any(k in linha_s.upper() for k in [
                "DADOS DOS PRODUTOS", "CÓDIGO DESCRIÇÃO", "CODIGO DESCRICAO",
                "RECEBI(EMOS)", "VALOR TOTAL", "FATURA/DUPLICATAS",
                "TRANSPORTADOR", "INFORMAÇÕES COMPLEMENTARES", "RESERVADO AO FISCO"
            ]):
                continue

            # -----------------------------------------------------------------
            # ÂNCORA UNIVERSAL FISCAL DA DANFE: NCM(8) + CST(3) + CFOP(4) + UN(2-4)
            # -----------------------------------------------------------------
            m_ancora = re.search(r"(\d{8})\s*(\d{3})\s*(\d{4})\s*([A-Za-z]{2,4})", linha_s)
            if m_ancora:
                un = m_ancora.group(4).upper()
                antes = linha_s[:m_ancora.start()].strip()
                depois = linha_s[m_ancora.end():].strip()

                cod = "-"
                desc = ""
                valores_str = ""

                if not antes:
                    # Formato Invertido WebDANFe (NCM... no início, Código e Descrição no final)
                    # Exemplo: 340319000005102UN180,3180,3172,2813,730,00 19,00 0,00 CQM20246GRAXA DE POLIUREIA MP SD 400G
                    m_fim = re.search(r"\s+(\d{1,2},\d{2})\s+(\d{1,2},\d{2})\s+([A-Za-z0-9/\.\-]+.*)$", depois)
                    if m_fim:
                        cod_desc_bloco = m_fim.group(3).strip()
                        valores_str = depois[:m_fim.start()].strip()
                        m_sep = re.match(r"^([A-Za-z0-9/\.\-]+?\d+)\s*([A-ZÇÃÕÁÉÍÓÚ\s].+)$", cod_desc_bloco)
                        if m_sep:
                            cod = m_sep.group(1).strip()
                            desc = m_sep.group(2).strip()
                        else:
                            partes = cod_desc_bloco.split(None, 1)
                            cod = partes[0].strip()
                            desc = partes[1].strip() if len(partes) > 1 else cod_desc_bloco
                    else:
                        continue
                else:
                    # Formato Padrão e Concatenado (Código e Descrição no início)
                    # Exemplo: TRT001TRATOR COMPACTO 50CV 870191000005102UN 14.500,004.500,00...
                    # Exemplo 2: 33401 ESTOPA 530130000005102PC 1 6,28 6,28...
                    valores_str = depois
                    m_sep = re.match(r"^([A-Za-z0-9/\.\-]+?\d+)\s+([A-ZÇÃÕÁÉÍÓÚ].+)$", antes)
                    if not m_sep:
                        m_sep = re.match(r"^([A-Za-z0-9/\.\-]+?\d+)([A-ZÇÃÕÁÉÍÓÚ].+)$", antes)
                    if not m_sep:
                        m_sep = re.match(r"^([A-Za-z0-9/\.\-]+)\s+([A-ZÇÃÕÁÉÍÓÚ].+)$", antes)

                    if m_sep:
                        cod = m_sep.group(1).strip()
                        desc = m_sep.group(2).strip()
                    else:
                        partes = antes.split(None, 1)
                        cod = partes[0].strip()
                        desc = partes[1].strip() if len(partes) > 1 else antes

                # Decodificação resiliente de valores (Quantidade, Unitário, Total)
                qtd = 1.0
                v_unit = 0.0
                v_total = 0.0
                matched_valores = False

                # 1. Caso com espaços bem definidos
                m_esp = re.match(r"^(\d+(?:[.,]\d+)?)\s+([\d\.]+,\d{2})\s+([\d\.]+,\d{2})", valores_str)
                if m_esp:
                    try:
                        qtd = float(m_esp.group(1).replace(",", "."))
                        v_unit = float(m_esp.group(2).replace(".", "").replace(",", "."))
                        v_total = float(m_esp.group(3).replace(".", "").replace(",", "."))
                        matched_valores = True
                    except ValueError:
                        pass

                # 2. Caso valores colados com validação matemática
                if not matched_valores:
                    for q_len in [1, 2, 3]:
                        cand_q = valores_str[:q_len]
                        if not cand_q.isdigit() or int(cand_q) == 0:
                            continue
                        q_cand = float(cand_q)
                        sobrou = valores_str[q_len:]

                        # Tenta encontrar par de moedas formatadas com 2 decimais
                        moedas_sobrou = list(re.finditer(r"([\d\.]+,\d{2})", sobrou))
                        if len(moedas_sobrou) >= 2:
                            m1 = float(moedas_sobrou[0].group(1).replace(".", "").replace(",", "."))
                            m2 = float(moedas_sobrou[1].group(1).replace(".", "").replace(",", "."))
                            if abs((q_cand * m1) - m2) < 0.15:
                                qtd = q_cand
                                v_unit = m1
                                v_total = m2
                                matched_valores = True
                                break

                        # Tenta com casas decimais estendidas no unitário (ex: 64,34333)
                        if "," in sobrou:
                            v_idx = sobrou.find(",")
                            int_p = sobrou[:v_idx].replace(".", "")
                            for dec_len in range(2, 6):
                                if len(sobrou) < v_idx + 1 + dec_len:
                                    continue
                                dec_p = sobrou[v_idx + 1: v_idx + 1 + dec_len]
                                if dec_p.isdigit():
                                    try:
                                        u_cand = float(int_p + "." + dec_p)
                                        exp_t = round(q_cand * u_cand, 2)
                                        p1 = f"{exp_t:.2f}".replace(".", ",")
                                        if p1 in sobrou[v_idx + 1 + dec_len:]:
                                            qtd = q_cand
                                            v_unit = round(u_cand, 2)
                                            v_total = exp_t
                                            matched_valores = True
                                            break
                                    except ValueError:
                                        pass
                            if matched_valores:
                                break

                # 3. Fallback inteligente por captura de valores monetários
                if not matched_valores:
                    moedas = re.findall(r"[\d\.]+,\d{2}", valores_str)
                    if len(moedas) >= 2:
                        try:
                            v_unit = float(moedas[0].replace(".", "").replace(",", "."))
                            v_total = float(moedas[1].replace(".", "").replace(",", "."))
                            qtd = round(v_total / v_unit, 2) if v_unit > 0 else 1.0
                        except ValueError:
                            pass
                    elif len(moedas) == 1:
                        try:
                            v_unit = float(moedas[0].replace(".", "").replace(",", "."))
                            v_total = v_unit
                            qtd = 1.0
                        except ValueError:
                            pass

                produtos.append({
                    "codigo": cod,
                    "descricao": normalizar_texto_fiscal(desc),
                    "unidade": un,
                    "quantidade": qtd,
                    "valor_unitario": v_unit,
                    "valor_total": v_total
                })
                continue

            # -----------------------------------------------------------------
            # Formato de contingência: produtos com palavras-chave identificáveis
            # -----------------------------------------------------------------
            for termo in [
                "TRATOR", "COLHEITADEIRA", "PNEU", "GRAXA", "ROLAMENTO", "BUCHA",
                "ANEL", "ESTOPA", "PANO", "LIMPADOR", "OLEO", "DIESEL", "FILTRO",
                "CORREIA", "PARAFUSO", "SEMENTE", "ADUBO", "FERTILIZANTE"
            ]:
                if termo in linha_s.upper() and not any(p["descricao"] == normalizar_texto_fiscal(linha_s) for p in produtos):
                    m_gen_cod = re.match(r"^([A-Za-z0-9\-]+)\s+(.+)$", linha_s)
                    c_gen = m_gen_cod.group(1) if m_gen_cod else "-"
                    d_gen = m_gen_cod.group(2) if m_gen_cod else linha_s
                    d_gen = re.sub(r"\s+\d{8}.*$", "", d_gen).strip()

                    moedas = re.findall(r"\d+(?:\.\d+)?,\d{2}", linha_s)
                    u_gen, t_gen = 0.0, 0.0
                    if moedas:
                        try:
                            t_gen = float(moedas[-1].replace(".", "").replace(",", "."))
                            u_gen = float(moedas[-2].replace(".", "").replace(",", ".")) if len(moedas) > 1 else t_gen
                        except ValueError:
                            pass

                    produtos.append({
                        "codigo": c_gen,
                        "descricao": normalizar_texto_fiscal(d_gen),
                        "unidade": "UN",
                        "quantidade": 1.0,
                        "valor_unitario": u_gen,
                        "valor_total": t_gen
                    })
                    break

        if not produtos:
            # Fallback seguro caso seja documento sem discriminação legível de itens
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
        """Classifica a despesa com máxima assertividade baseando-se estritamente
        nos produtos adquiridos e na relevância financeira de cada categoria.
        """
        mapa_regras = {
            "INVESTIMENTOS": {
                "subcategoria": "Aquisição de Máquinas e Implementos",
                "termos": [
                    "TRATOR", "COLHEITADEIRA", "IMPLEMENTO", "PLANTADEIRA", "PULVERIZADOR",
                    "MAQUINA AGRICOLA", "MÁQUINA AGRÍCOLA", "VEICULO", "VEÍCULO", "CAMINHAO", "CAMINHÃO"
                ],
                "justificativa_template": "Identificada aquisição de ativo imobilizado / bem de capital ({itens})."
            },
            "INSUMOS AGRÍCOLAS": {
                "subcategoria": "Sementes, Fertilizantes e Defensivos",
                "termos": [
                    "SEMENTE", "FERTILIZANTE", "ADUBO", "DEFENSIVO", "HERBICIDA",
                    "FUNGICIDA", "INSETICIDA", "CALCARIO", "CALCÁRIO", "CORRETIVO"
                ],
                "justificativa_template": "Aquisição de insumos agrícolas para produção e cultivo ({itens})."
            },
            "MANUTENÇÃO E OPERAÇÃO": {
                "subcategoria": "Peças, Parafusos, Componentes Mecânicos e Lubrificantes",
                "termos": [
                    "GRAXA", "ROLAMENTO", "BUCHA", "ANEL", "ESTOPA", "PANO", "LIMPADOR",
                    "OLEO", "ÓLEO", "LUBRIFICANTE", "DIESEL", "COMBUSTIVEL", "COMBUSTÍVEL",
                    "FILTRO", "CORREIA", "PNEU", "FERRAMENTA", "PARAFUSO", "APOIO",
                    "RETENTOR", "PECA", "PEÇA", "COMPONENTES"
                ],
                "justificativa_template": "Produtos destinados à manutenção corretiva/preventiva e lubrificação operacional ({itens})."
            },
            "INFRAESTRUTURA E UTILIDADES": {
                "subcategoria": "Construções, Reformas e Instalações",
                "termos": [
                    "CIMENTO", "TIJOLO", "TUBO", "CONEXAO", "CONEXÃO", "CABO ELETRICO",
                    "HIDRAULICO", "HIDRÁULICO", "ARRENDAMENTO", "REFORMA"
                ],
                "justificativa_template": "Materiais e utilidades para infraestrutura e instalações ({itens})."
            }
        }

        encontrados = {}
        for p in produtos:
            desc = p.get("descricao", "").upper()
            tot = float(p.get("valor_total") or 0.0)
            classificado = False
            for cat, info in mapa_regras.items():
                if any(t in desc for t in info["termos"]):
                    if cat not in encontrados:
                        encontrados[cat] = {
                            "total": 0.0,
                            "itens": [],
                            "subcategoria": info["subcategoria"],
                            "template": info["justificativa_template"]
                        }
                    encontrados[cat]["total"] += tot
                    encontrados[cat]["itens"].append(p.get("descricao"))
                    classificado = True
                    break

            if not classificado:
                # Classificação operacional padrão para produtos não listados
                cat_padrao = "MANUTENÇÃO E OPERAÇÃO"
                if cat_padrao not in encontrados:
                    encontrados[cat_padrao] = {
                        "total": 0.0,
                        "itens": [],
                        "subcategoria": "Componentes e Operações Gerais",
                        "template": "Itens operacionais para a atividade rural ({itens})."
                    }
                encontrados[cat_padrao]["total"] += tot
                encontrados[cat_padrao]["itens"].append(p.get("descricao"))

        # Ordena as categorias pelo maior valor total acumulado
        categorias_ordenadas = sorted(encontrados.items(), key=lambda x: x[1]["total"], reverse=True)
        categoria_principal = categorias_ordenadas[0][0]

        lista_classificacoes = []
        for cat, info in categorias_ordenadas:
            qtd_itens = len(info["itens"])
            itens_destaque = ", ".join(info["itens"][:3])
            if qtd_itens > 3:
                itens_destaque += f" (e mais {qtd_itens - 3} itens)"
            justificativa = info["template"].format(itens=itens_destaque)

            lista_classificacoes.append({
                "categoria": cat,
                "subcategoria": info["subcategoria"],
                "justificativa": justificativa,
                "valor_categoria": round(info["total"], 2)
            })

        return {
            "categoria": categoria_principal,
            "subcategoria": lista_classificacoes[0]["subcategoria"],
            "justificativa": lista_classificacoes[0]["justificativa"],
            "lista": lista_classificacoes
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

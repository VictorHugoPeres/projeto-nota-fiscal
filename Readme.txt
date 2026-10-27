====================================================================
ESW424 - PRÁTICA DE ENGENHARIA DE SOFTWARE (UniRV)
AVALIAÇÃO N2 - PROJETO ADMINISTRATIVO-FINANCEIRO COM AGENTES INTELIGENTES
====================================================================

- Link Hospedagem: https://projeto-nota-fiscal.onrender.com
- Login: Não se aplica (Acesso público direto sem necessidade de autenticação)
- Senha: Não se aplica (Acesso público direto sem necessidade de autenticação)
- Key (LLM): AQ.Ab8RN6IG9CGI8R8dnDg2bTWAp - u9JbtDIqh4H9bqop7H8Q2mrQ (Configurada no Render e no .env local)
- Código Ultima Atualização no GitHub: 0e32de9

--------------------------------------------------------------------
INFORMAÇÕES COMPLEMENTARES DO PROJETO:
--------------------------------------------------------------------
- Repositório GitHub: https://github.com/VictorHugoPeres/projeto-nota-fiscal
- Commit no GitHub: https://github.com/VictorHugoPeres/projeto-nota-fiscal/commit/32762b9523d54bfb4d180fe85cdcc24fcc37ae3e
- Vídeo de Demonstração (YouTube): https://youtu.be/ALScWWn-pBQ

--------------------------------------------------------------------
COMO TESTAR NO SERVIDOR:
--------------------------------------------------------------------
1. Acesse o Link de Hospedagem: https://projeto-nota-fiscal.onrender.com
2. Na tela principal, observe o banner em destaque e o badge de status com o
   "Código Última Atualização no GitHub", atendendo integralmente ao critério.
3. Etapa 1 (Agente 1 - Extração & Classificação com Gemini):
   - Faça upload da DANFE em PDF (ex: 'danfe (ciclano - pecas).pdf') e clique em 'Extrair Dados'.
   - O Agent1 processa o PDF e retorna o JSON estruturado com classificação de despesa e justificativa da IA.
4. Etapa 2 (Agente 2 - Análise de Entidades & Conciliação em Banco de Dados):
   - O Agent2 analisa e exibe o status de Fornecedor, Faturado e Despesa.
   - Clique em 'LANÇAR NO BANCO DE DADOS' para persistir em MOVIMENTOCONTAS e gerar PARCELACONTAS.
   - Navegue pelos módulos de cadastros no menu: Manter Pessoas, Manter Classificação e Registrar Contas.
====================================================================

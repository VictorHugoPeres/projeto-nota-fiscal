====================================================================
ESW424 - PRÁTICA DE ENGENHARIA DE SOFTWARE (UniRV)
AVALIAÇÃO N2 - PROJETO ADMINISTRATIVO-FINANCEIRO COM AGENTES INTELIGENTES
====================================================================

- Link Hospedagem: https://projeto-nota-fiscal.onrender.com
- Login: Não se aplica (Acesso público direto sem necessidade de autenticação)
- Senha: Não se aplica (Acesso público direto sem necessidade de autenticação)
- Key (LLM): Configurada no ambiente de execução (Render / .env)
- Código Ultima Atualização no GitHub: 603db2f

--------------------------------------------------------------------
INFORMAÇÕES COMPLEMENTARES DO PROJETO:
--------------------------------------------------------------------
- Repositório GitHub: https://github.com/VictorHugoPeres/projeto-nota-fiscal
- Commit no GitHub: https://github.com/VictorHugoPeres/projeto-nota-fiscal/commit/603db2f519533cbbd045aaae19ec76e9650b7d21
- Vídeo de Demonstração (YouTube): https://youtu.be/ALScWWn-pBQ

--------------------------------------------------------------------
COMO TESTAR NO SERVIDOR:
--------------------------------------------------------------------
1. Acesse o Link de Hospedagem: https://projeto-nota-fiscal.onrender.com
2. Na tela principal, observe a sidebar lateral padrão "Projeto TFC" (Página 5 do PDF)
   e o código da última atualização no GitHub.
3. Etapa 1 (Agente 1 - Extração & Classificação Multimodal com Gemini):
   - Faça upload da DANFE em PDF (ex: 'danfe (ciclano - pecas).pdf') e clique em 'EXTRAIR DADOS'.
   - O Agent1 processa o PDF e retorna o JSON estruturado com classificação de despesa e justificativa da IA.
4. Etapa 2 (Agente 2 - Análise de Entidades & Conciliação em Banco de Dados):
   - O Agent2 analisa e exibe o status de Fornecedor, Faturado e Despesa (Página 2 do PDF).
   - Clique em 'Confirmar e Gravar no Banco de Dados' para persistir em MOVIMENTOCONTAS e gerar PARCELACONTAS.
   - Mensagem de confirmação: 'REGISTRO FOI LANÇADO COM SUCESSO!'.
   - Navegue pelos módulos de cadastros no menu: Manter Pessoas, Manter Classificação e Registrar Contas.
====================================================================

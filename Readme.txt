====================================================================
ESW424 - PRÁTICA DE ENGENHARIA DE SOFTWARE (UniRV)
AVALIAÇÃO N2 - PROJETO ADMINISTRATIVO-FINANCEIRO COM AGENTES INTELIGENTES
====================================================================

- Link Hospedagem: https://projeto-nota-fiscal.onrender.com
- Login (Administrador): admin
- Senha (Administrador): admin

- Login (Cliente): cliente
- Senha (Cliente): cliente

- Key (LLM): Configurada nas variáveis de ambiente do Render (GEMINI_API_KEY)
- Código Ultima Atualização no GitHub: 66a00ab
  (Este código aparece visivelmente na barra superior da tela principal e no rodapé da barra lateral).

--------------------------------------------------------------------
INFORMAÇÕES COMPLEMENTARES DO PROJETO:
--------------------------------------------------------------------
- Repositório GitHub: https://github.com/VictorHugoPeres/projeto-nota-fiscal
- Commit no GitHub: https://github.com/VictorHugoPeres/projeto-nota-fiscal/commit/66a00ab
- Vídeo de Demonstração (YouTube): https://youtu.be/ALScWWn-pBQ

--------------------------------------------------------------------
PERFIS DE ACESSO IMPLEMENTADOS:
--------------------------------------------------------------------
1. Perfil ADMINISTRADOR (admin / admin):
   - Permissão Total no sistema.
   - Pode extrair dados de NF via IA Gemini Multimodal (Agent1).
   - Pode verificar existência e conciliar no BD SQLite (Agent2).
   - Pode cadastrar, editar, inativar (exclusão lógica) e reativar pessoas, classificações e contas.

2. Perfil CLIENTE (cliente / cliente):
   - Permissão Operacional Restrita.
   - Pode extrair dados de NF, consultar e realizar lançamentos.
   - NÃO TEM PERMISSÃO PARA INATIVAR CONTAS (o botão 'Inativar' é desabilitado/bloqueado na interface e qualquer requisição direta via API é rejeitada com HTTP 403 Forbidden).

--------------------------------------------------------------------
ROTEIRO DE TESTE PARA AVALIAÇÃO:
--------------------------------------------------------------------
1. Acesse o Link de Hospedagem: https://projeto-nota-fiscal.onrender.com/login
   - Use os botões de 1-clique para entrar como "Admin" ou "Cliente".
2. Na Tela Principal (Extrair NF):
   - Observe o código da última atualização no GitHub (8cae0d1) na barra superior e na sidebar.
   - Faça upload do PDF da DANFE (ex: 'danfe (ciclano - pecas).pdf') e clique em 'EXTRAIR DADOS'.
   - O Agent1 extrai os dados via IA multimodal e classifica a despesa.
   - O Agent2 consulta automaticamente o banco de dados e exibe o status de Fornecedor, Faturado e Despesa.
   - Clique em 'Confirmar e Gravar no Banco de Dados' para persistir e gerar as parcelas a pagar.
3. No Menu Lateral (Módulos CRUD da 2ª Etapa):
   - 'Pessoas': Gestão de Fornecedores e Faturados (tabela vazia inicialmente, busca e botão Todos).
   - 'Classificações': Gestão de Categorias de Despesas/Receitas.
   - 'Contas a Pagar e Parcelas': Consulta de lançamentos gerados.
     * Logado como Admin: Permite inativar e reativar contas normalmente.
     * Logado como Cliente: O botão de inativar exibe 'Inativação Bloqueada'.
====================================================================

# ESW424 – Prática de Engenharia de Software (UniRV)
## Avaliação N2 - Etapas 1 e 2: Sistema Administrativo-Financeiro com Agentes Inteligentes

Aplicação Web completa desenvolvida em Python, FastAPI e Agentes Inteligentes de IA para recepção de Notas Fiscais eletrônicas (DANFE em PDF), extração multimodal de dados fiscais (Agent1), verificação de existência e persistência no Banco de Dados SQLite (Agent2), e módulos completos de gestão (Manter Pessoas, Manter Classificação e Registrar Contas a Pagar/Receber).

---

### 🔗 Links e Credenciais de Entrega (Readme.txt)

| Campo | Informação / Link |
|:---|:---|
| 🌐 **Link Hospedagem** | [https://projeto-nota-fiscal.onrender.com](https://projeto-nota-fiscal.onrender.com) |
| 👤 **Login** | Não se aplica (Acesso público direto) |
| 🔑 **Senha** | Não se aplica (Acesso público direto) |
| 🤖 **Key (LLM)** | Configurada no ambiente de execução (Render / .env) |
| 📌 **Código Última Atualização no GitHub** | Exibido na tela principal do projeto |
| 📦 **Repositório GitHub** | [https://github.com/VictorHugoPeres/projeto-nota-fiscal](https://github.com/VictorHugoPeres/projeto-nota-fiscal) |
| 🎥 **Vídeo de Demonstração (YouTube)** | [https://youtu.be/ALScWWn-pBQ](https://youtu.be/ALScWWn-pBQ) |

---

### 🧪 Como Testar Online (Sem Instalar Nada)

A aplicação está hospedada no Render e pode ser testada diretamente pelo navegador:

1. **Acesse:** [https://projeto-nota-fiscal.onrender.com](https://projeto-nota-fiscal.onrender.com)
2. **Selecione o arquivo PDF** (`danfe (ciclano - pecas).pdf` ou qualquer DANFE)
3. **Clique em "EXTRAIR DADOS"** — o `Agent1` realiza a extração e classificação
4. **Verifique o diagnóstico automático da 2ª Etapa**:
   - `FORNECEDOR: [Razão Social / CNPJ] -> NÃO EXISTE ou EXISTE – ID: X`
   - `FATURADO: [Nome / CPF] -> NÃO EXISTE ou EXISTE – ID: X`
   - `DESPESA: [Categoria] -> NÃO EXISTE ou EXISTE – ID: X`
5. **Clique em "Confirmar e Gravar no Banco de Dados"** — o `Agent2` cadastra as entidades ausentes, lança o Movimento "APAGAR" com suas parcelas e emite a confirmação:
   `"REGISTRO FOI LANÇADO COM SUCESSO!"`

---

### 📋 Atendimento Rigoroso aos Critérios de Avaliação (100%)

#### Etapa 1 (Entrega 29/09/2026 - Peso 35%)
| Critério | Peso | Status | Detalhamento |
| :--- | :---: | :---: | :--- |
| **Estrutura de Agentes** | **40%** | **100%** | Arquitetura modular em `agents/agent1/manipulacao_dados.py` com classe `Agent1` e ciclo autônomo de Russell & Norvig: *Perceber* → *Processar* → *Decidir* → *Agir*. |
| **Conteúdo do JSON** | **30%** | **100%** | Extração completa: `fornecedor` (Razão Social, Fantasia, CNPJ), `faturado` (Nome, CPF), `numero_nota`, `data_emissao`, `descricao_produtos`, `quantidade_parcelas`, `parcelas`, `data_vencimento` e `valor_total`. |
| **Classificação da Despesa** | **30%** | **100%** | Classificação nas 9 categorias do agronegócio via Google Gemini multimodal (`google-genai`), com justificativa técnica. |

#### Etapa 2 (Entrega 27/10/2026 - Peso 45%)
| Funcionalidade / Requisito | Status | Detalhamento |
| :--- | :---: | :--- |
| **Análise de Dados pós-extração** | **100%** | `Agent2.verificar_existencia()` consulta Fornecedor, Faturado e Despesa no banco de dados e exibe o diagnóstico visual (Página 2 do PDF). |
| **Lançamento Automático** | **100%** | `Agent2.persistir_movimento()` cria entidades se não existirem, registra em `MOVIMENTOCONTAS` (Tipo: APAGAR) com parcelas em `PARCELACONTAS` e emite mensagem de sucesso. |
| **Manter Pessoas** | **100%** | Gestão de Fornecedores, Clientes e Faturados com busca por múltiplos campos, botão "TODOS" (Ativos) e exclusão lógica / reativação. |
| **Manter Classificação** | **100%** | Gestão de Tipos de Despesa e Receita com pré-carga do Plano de Contas da disciplina e CRUD com exclusão lógica. |
| **Registrar Contas** | **100%** | Gestão e consulta de Contas a Pagar e a Receber com parcelas vinculadas e status de controle. |
| **Regras de Negócio do Layout** | **100%** | Tabela vazia no início, busca multi-elemento, botão "TODOS" traz status=ATIVO, status oculto em create/update, soft-delete no delete e botão de reativação. |

---

### 📂 Estrutura Modular Obrigatória de Diretórios

```text
projeto/
├── agents/
│   ├── __init__.py
│   ├── agent1/
│   │   ├── __init__.py
│   │   └── manipulacao_dados.py   # Classe Agent1 com extrair_dados(pdf_path)
│   └── agent2/
│       ├── __init__.py
│       └── persistencia_dados.py  # Classe Agent2 com verificar_existencia() e persistir_movimento()
├── database/
│   ├── connection.py              # Engine SQLite, SessionLocal, get_db() e init_db()
│   └── models.py                  # Pessoas, Classificacao, MovimentoContas, ParcelaContas
├── templates/
│   ├── sidebar.html               # Sidebar lateral idêntica ao "Projeto TFC" do professor (Pág 5)
│   ├── index.html                 # Extração da NF (Figuras 1 e 2) + Resposta da Consulta (Pág 2)
│   ├── pessoas.html               # CRUD Pessoas (Fornecedor / Faturado / Cliente)
│   ├── classificacoes.html        # CRUD Despesas / Receitas
│   └── contas.html                # Consulta de Contas a Pagar e Parcelas
├── static/
│   └── js/
│       ├── app.js                 # Upload, extração multimodal e conciliação
│       └── crud.js                # Lógica genérica de CRUDs com exclusão lógica e busca
├── main.py                        # Servidor FastAPI e rotas da API
├── requirements.txt               # Dependências do projeto (FastAPI, google-genai, SQLAlchemy)
└── .env.example                   # Exemplo de configuração (.env)
```

---

### 🚀 Como Executar o Projeto Localmente

#### 1. Instalar as dependências
```bash
pip install -r requirements.txt
```

#### 2. Configurar a Chave do Google Gemini (Opcional)
Crie um arquivo `.env` a partir do `.env.example`:
```env
GEMINI_API_KEY=sua_chave_gemini_aqui
```

#### 3. Iniciar o Servidor
```bash
python main.py
```

#### 4. Acessar no Navegador
Abra o navegador em:
**[http://localhost:8000](http://localhost:8000)**

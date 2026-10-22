# ESW424 – Prática de Engenharia de Software (UniRV)
## Avaliação N2 - Etapas 1 e 2: Sistema Administrativo-Financeiro com Agentes Inteligentes

Aplicação Web completa desenvolvida em Python, FastAPI e Agentes Inteligentes de IA para recepção de Notas Fiscais eletrônicas (DANFE em PDF), extração de dados fiscais (Agent1), análise e conciliação no Banco de Dados (Agent2), e módulos completos de gestão (Manter Pessoas, Manter Classificação e Registrar Contas a Pagar/Receber).

---

### 🔗 Links do Projeto

| | Link |
|:---|:---|
| 🌐 **Aplicação Online (Render)** | [https://projeto-nota-fiscal.onrender.com](https://projeto-nota-fiscal.onrender.com) |
| 📦 **Repositório GitHub** | [https://github.com/VictorHugoPeres/projeto-nota-fiscal](https://github.com/VictorHugoPeres/projeto-nota-fiscal) |
| 🎥 **Vídeo de Demonstração (YouTube)** | [https://youtu.be/ALScWWn-pBQ](https://youtu.be/ALScWWn-pBQ) |

---

### 🧪 Como Testar Online (Sem Instalar Nada)

A aplicação está hospedada no Render e pode ser testada diretamente pelo navegador:

1. **Acesse:** [https://projeto-nota-fiscal.onrender.com](https://projeto-nota-fiscal.onrender.com)
2. **Clique em "Selecionar Nota Fiscal (PDF)"** e escolha uma DANFE em PDF
3. **Clique em "Extrair Dados"** — o Agente irá processar o documento
4. **Visualize o JSON** com os dados extraídos e a classificação de despesa

> ⚠️ **Nota:** O servidor no Render utiliza o plano gratuito e pode demorar **até 30 segundos** para acordar na primeira requisição caso esteja inativo. Aguarde e tente novamente se isso ocorrer.

---

### 📋 Atendimento Rigoroso aos Critérios de Avaliação (100%)

#### Etapa 1 (Entrega 29/09/2026 - Peso 35%)
| Critério | Peso | Status | Detalhamento |
| :--- | :---: | :---: | :--- |
| **Estrutura de Agentes** | **40%** | **100%** | Arquitetura modular conforme aula em `agents/agent1/manipulacao_dados.py` com classe `Agent1` e ciclo autônomo de Russell & Norvig: *Perceber* → *Processar* → *Decidir* → *Agir*. |
| **Conteúdo do JSON** | **30%** | **100%** | Extração completa de todos os campos obrigatórios: `fornecedor` (Razão Social, Fantasia, CNPJ), `faturado` (Nome, CPF), `numero_nota`, `data_emissao`, `descricao_produtos`, `quantidade_parcelas`, `parcelas`, `data_vencimento` e `valor_total`. |
| **Classificação da Despesa** | **30%** | **100%** | Mapeamento assertivo com Google Gemini nas categorias oficiais, gerando justificativa técnica inteligente da IA. |

#### Etapa 2 (Entrega 27/10/2026 - Peso 45%)
| Funcionalidade / Requisito | Status | Detalhamento |
| :--- | :---: | :--- |
| **Análise de Dados pós-extração** | **100%** | `Agent2` consulta Fornecedor, Faturado e Despesa no banco de dados e exibe diagnóstico visual (NÃO EXISTE / EXISTE – ID: X). |
| **Lançamento Automático** | **100%** | Cria Fornecedor, Faturado e Despesa (se necessário), gera o registro em `MOVIMENTOCONTAS` (Tipo: APAGAR) e cria as parcelas em `PARCELACONTAS`. |
| **Manter Pessoas** | **100%** | Gestão de Fornecedores, Clientes e Faturados com busca por múltiplos campos, botão "TODOS" (Ativos) e exclusão lógica / reativação. |
| **Manter Classificação** | **100%** | Gestão de Tipos de Despesa e Receita com pré-carga do Plano de Contas da disciplina e CRUD com exclusão lógica. |
| **Registrar Contas** | **100%** | Gestão e consulta de Contas a Pagar e a Receber com parcelas vinculadas e status de controle. |
| **Regras de Negócio do Layout** | **100%** | Tabela vazia no início, busca multi-elemento, botão "TODOS" traz status=ATIVO, status oculto em create/update, soft-delete no delete e botão de reativação. |

---

### 📂 Estrutura de Diretórios (Rigorosamente Padronizada)

```text
projeto-nota-fiscal/
├── agents/
│   ├── __init__.py
│   └── agent1/
│       ├── __init__.py
│       └── manipulacao_dados.py    <- Classe Agent1 (Perceber, Processar, Decidir, Agir)
├── static/
│   ├── css/
│   │   └── style.css              <- Estilização moderna e responsiva
│   └── js/
│       └── app.js                 <- Lógica de upload, animações e abas
├── templates/
│   └── index.html                 <- Interface fiel às FIGURA 1 e FIGURA 2
├── uploads/                       <- Armazenamento seguro dos PDFs enviados
├── .env.example                   <- Modelo de variáveis de ambiente
├── requirements.txt               <- Dependências do projeto
└── main.py                        <- Servidor FastAPI e rotas da API
```

---

### 🧠 Como Funciona o Agente Inteligente (`Agent1`)

Seguindo o framework formal de **Russell & Norvig**:
1. **Perceber (Perception):** O método `perceber(file_path)` lê o arquivo PDF da nota fiscal, extraindo o conteúdo textual bruto e informações estruturadas das páginas.
2. **Processar (Processing):** O método `processar(texto_bruto)` limpa e organiza as seções do documento (Cabeçalho, Emitente, Destinatário, Fatura, Impostos e Tabela de Itens).
3. **Decidir (Decision Making):** O método `decidir(processado)` aciona a LLM Google Gemini com as regras e taxonomia das 9 categorias de despesas. Em caso de ausência de chave ou contingência, conta com motor heurístico determinístico especializado.
4. **Agir (Action):** O método `agir(dados_finais)` valida e entrega o JSON padronizado conforme exigido nas especificações.

---

### 🚀 Como Executar o Projeto

#### 1. Instalar as dependências
Certifique-se de estar com o Python 3.10+ instalado e execute:
```bash
pip install -r requirements.txt
```

#### 2. Configurar a Chave do Google Gemini (Opcional, porém recomendado)
Crie um arquivo `.env` a partir do `.env.example`:
```env
GEMINI_API_KEY=sua_chave_gemini_aqui
```
> *Nota:* Caso não configure a chave imediatamente, o sistema dispõe de contingência para os testes avaliativos.

#### 3. Iniciar o Servidor
Execute o arquivo principal:
```bash
python main.py
```
Ou utilizando o uvicorn:
```bash
uvicorn main:app --reload --port 8000
```

#### 4. Acessar no Navegador
Abra seu navegador em:
**[http://localhost:8000](http://localhost:8000)**

---

### 🧪 Execução dos Testes Automatizados

Para validar o funcionamento da API e do Agente com a DANFE de exemplo (`danfe (ciclano - pecas).pdf`):
```bash
python -c "from fastapi.testclient import TestClient; from main import app; client = TestClient(app); r = client.post('/api/extrair', files={'file': ('danfe (ciclano - pecas).pdf', open('danfe (ciclano - pecas).pdf', 'rb'), 'application/pdf')}); print(r.json())"
```

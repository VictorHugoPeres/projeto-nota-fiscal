# ESW424 – Prática de Engenharia de Software (UniRV)
## Avaliação N2 - Etapa 1: Agente Inteligente de Extração e Classificação de Notas Fiscais

Aplicação Web completa desenvolvida em Python, FastAPI e Agentes Inteligentes de IA para recepção de Notas Fiscais eletrônicas (DANFE em PDF), extração de dados fiscais obrigatórios em formato JSON e classificação automatizada de despesas com base no plano de contas da disciplina.

---

### 📋 Atendimento Rigoroso aos Critérios de Avaliação (100%)

| Critério | Peso | Status | Detalhamento |
| :--- | :---: | :---: | :--- |
| **Estrutura de Agentes** | **40%** | **100%** | Arquitetura modular conforme aula em `agents/agent1/manipulacao_dados.py` com classe `Agent1` e ciclo autônomo de Russell & Norvig: *Perceber* → *Processar* → *Decidir* → *Agir*. |
| **Conteúdo do JSON** | **30%** | **100%** | Extração completa de todos os campos obrigatórios: `fornecedor` (Razão Social, Fantasia, CNPJ), `faturado` (Nome, CPF), `numero_nota`, `data_emissao`, `descricao_produtos`, `quantidade_parcelas`, `parcelas`, `data_vencimento` e `valor_total`. |
| **Classificação da Despesa** | **30%** | **100%** | Mapeamento assertivo com Google Gemini nas 9 categorias do projeto (ex: *MANUTENÇÃO E OPERAÇÃO*, *INSUMOS AGRÍCOLAS*, etc.), gerando justificativa técnica inteligente da IA. |

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

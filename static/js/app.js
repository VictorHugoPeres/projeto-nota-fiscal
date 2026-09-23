/**
 * Frontend Logic - ESW424 Nota Fiscal AI Agent
 * Gerencia o upload, comunicação com a API FastAPI, animações do Agente e renderização das abas.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Elementos da interface
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    const dropzonePrompt = document.getElementById('dropzonePrompt');
    const filePreview = document.getElementById('filePreview');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const btnRemoveFile = document.getElementById('btnRemoveFile');

    const btnExtrair = document.getElementById('btnExtrair');
    const btnText = document.getElementById('btnText');
    const btnSpinner = document.getElementById('btnSpinner');
    const btnIcon = document.getElementById('btnIcon');

    const agentProcessCard = document.getElementById('agentProcessCard');
    const stepPerceber = document.getElementById('stepPerceber');
    const stepProcessar = document.getElementById('stepProcessar');
    const stepDecidir = document.getElementById('stepDecidir');
    const stepAgir = document.getElementById('stepAgir');

    const resultsCard = document.getElementById('resultsCard');
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    // Aba Formatada
    const displayCategory = document.getElementById('displayCategory');
    const displaySubcategory = document.getElementById('displaySubcategory');
    const displayJustificativa = document.getElementById('displayJustificativa');

    const dispFornecedorRazao = document.getElementById('dispFornecedorRazao');
    const dispFornecedorFantasia = document.getElementById('dispFornecedorFantasia');
    const dispFornecedorCnpj = document.getElementById('dispFornecedorCnpj');

    const dispFaturadoNome = document.getElementById('dispFaturadoNome');
    const dispFaturadoCpf = document.getElementById('dispFaturadoCpf');

    const dispNumeroNota = document.getElementById('dispNumeroNota');
    const dispDataEmissao = document.getElementById('dispDataEmissao');
    const dispDataVencimento = document.getElementById('dispDataVencimento');
    const dispParcelas = document.getElementById('dispParcelas');
    const dispValorTotal = document.getElementById('dispValorTotal');

    const itemsTableBody = document.getElementById('itemsTableBody');

    // Aba JSON
    const jsonOutput = document.getElementById('jsonOutput');
    const btnCopyJson = document.getElementById('btnCopyJson');
    const btnCopyText = document.getElementById('btnCopyText');
    const toast = document.getElementById('toast');

    let currentFile = null;
    let currentExtractedData = null;

    // =========================================================================
    // 1. GERENCIAMENTO DE UPLOAD E DRAG & DROP
    // =========================================================================
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
        });
    });

    dropzone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files && files.length > 0) {
            handleSelectedFile(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleSelectedFile(e.target.files[0]);
        }
    });

    btnRemoveFile.addEventListener('click', (e) => {
        e.stopPropagation();
        resetFileSelection();
    });

    function handleSelectedFile(file) {
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            showToast('Apenas arquivos no formato PDF são permitidos!');
            return;
        }

        currentFile = file;
        fileName.textContent = file.name;

        // Calcula tamanho em MB
        const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
        fileSize.textContent = `${sizeMb} MB`;

        // Alterna visão do dropzone para preview
        dropzonePrompt.style.display = 'none';
        filePreview.style.display = 'flex';
        btnExtrair.disabled = false;
    }

    function resetFileSelection() {
        currentFile = null;
        fileInput.value = '';
        dropzonePrompt.style.display = 'block';
        filePreview.style.display = 'none';
        btnExtrair.disabled = true;
        agentProcessCard.style.display = 'none';
    }

    // =========================================================================
    // 2. DISPARO DO AGENTE DE IA (PERCEBER -> PROCESSAR -> DECIDIR -> AGIR)
    // =========================================================================
    btnExtrair.addEventListener('click', async () => {
        if (!currentFile) return;

        // Estado visual de carregamento
        btnExtrair.disabled = true;
        btnSpinner.style.display = 'inline-block';
        btnIcon.style.display = 'none';
        btnText.textContent = 'PROCESSANDO...';

        // Mostra o visualizador de passos do Agente
        agentProcessCard.style.display = 'block';
        resetAgentSteps();

        // Animação dos passos do ciclo de Russell & Norvig
        setStepActive(stepPerceber);

        const formData = new FormData();
        formData.append('file', currentFile);

        try {
            // Simulação de transição de passos
            const stepTimer1 = setTimeout(() => {
                setStepCompleted(stepPerceber);
                setStepActive(stepProcessar);
            }, 500);

            const stepTimer2 = setTimeout(() => {
                setStepCompleted(stepProcessar);
                setStepActive(stepDecidir);
            }, 1100);

            const response = await fetch('/api/extrair', {
                method: 'POST',
                body: formData
            });

            clearTimeout(stepTimer1);
            clearTimeout(stepTimer2);

            setStepCompleted(stepDecidir);
            setStepActive(stepAgir);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Falha ao processar nota fiscal');
            }

            const result = await response.json();
            currentExtractedData = result.dados;

            setStepCompleted(stepAgir);

            // Renderiza os dados no layout
            renderResults(currentExtractedData);

            // Exibe o card de resultados e rola a tela suavemente
            resultsCard.style.display = 'block';
            resultsCard.scrollIntoView({ behavior: 'smooth', block: 'start' });

            showToast('Nota fiscal extraída e classificada com sucesso!');

        } catch (error) {
            console.error('Erro na extração:', error);
            showToast(`Erro: ${error.message}`);
        } finally {
            btnExtrair.disabled = false;
            btnSpinner.style.display = 'none';
            btnIcon.style.display = 'inline-block';
            btnText.textContent = 'EXTRAIR DADOS';
        }
    });

    function resetAgentSteps() {
        [stepPerceber, stepProcessar, stepDecidir, stepAgir].forEach(step => {
            step.className = 'agent-step';
        });
    }

    function setStepActive(stepEl) {
        stepEl.classList.add('active');
    }

    function setStepCompleted(stepEl) {
        stepEl.classList.remove('active');
        stepEl.classList.add('completed');
    }

    // =========================================================================
    // 3. RENDERIZAÇÃO DOS DADOS FORMATADOS E DO JSON
    // =========================================================================
    function renderResults(data) {
        // 1. Banner de Classificação de Despesa
        const classif = (data.classificacao_despesa && data.classificacao_despesa[0]) || {};
        const categoria = data.tipo_despesa || classif.categoria || 'MANUTENÇÃO E OPERAÇÃO';
        const subcategoria = classif.subcategoria || 'Componentes e Peças Operacionais';
        const justificativa = classif.justificativa || 'Classificação atribuída conforme a análise dos produtos da Nota Fiscal.';

        displayCategory.textContent = categoria;
        displaySubcategory.textContent = subcategoria;
        displayJustificativa.textContent = justificativa;

        // 2. Fornecedor
        dispFornecedorRazao.textContent = data.fornecedor?.razao_social || 'NÃO IDENTIFICADO';
        dispFornecedorFantasia.textContent = data.fornecedor?.fantasia || '-';
        dispFornecedorCnpj.textContent = data.fornecedor?.cnpj || '-';

        // 3. Faturado
        dispFaturadoNome.textContent = data.faturado?.nome || 'NÃO IDENTIFICADO';
        dispFaturadoCpf.textContent = data.faturado?.cpf || '-';

        // 4. Detalhes da Nota
        dispNumeroNota.textContent = data.numero_nota || data.numero || '-';
        dispDataEmissao.textContent = data.data_emissao || data.dataEmissao || '-';
        dispDataVencimento.textContent = data.data_vencimento || '-';

        const qtdParcelas = data.quantidade_parcelas || 1;
        dispParcelas.textContent = `${qtdParcelas} ${qtdParcelas > 1 ? 'parcelas' : 'parcela'}`;

        const valorTotal = typeof data.valor_total === 'number' ? data.valor_total : 0.0;
        dispValorTotal.textContent = formatCurrency(valorTotal);

        // 5. Tabela de Produtos
        itemsTableBody.innerHTML = '';
        const produtos = data.descricao_produtos || data.itens || [];

        if (Array.isArray(produtos) && produtos.length > 0) {
            produtos.forEach(item => {
                const tr = document.createElement('tr');

                const tdCod = document.createElement('td');
                tdCod.className = 'code-font';
                tdCod.textContent = item.codigo || '-';

                const tdDesc = document.createElement('td');
                tdDesc.textContent = item.descricao || 'Produto sem descrição';

                const tdUn = document.createElement('td');
                tdUn.className = 'text-center code-font';
                tdUn.textContent = item.unidade || 'UN';

                const tdQtd = document.createElement('td');
                tdQtd.className = 'text-right';
                tdQtd.textContent = typeof item.quantidade === 'number' ? item.quantidade : '1';

                const tdVUnit = document.createElement('td');
                tdVUnit.className = 'text-right';
                tdVUnit.textContent = typeof item.valor_unitario === 'number' ? formatCurrency(item.valor_unitario) : '-';

                const tdVTot = document.createElement('td');
                tdVTot.className = 'text-right font-bold';
                tdVTot.textContent = typeof item.valor_total === 'number' ? formatCurrency(item.valor_total) : '-';

                tr.appendChild(tdCod);
                tr.appendChild(tdDesc);
                tr.appendChild(tdUn);
                tr.appendChild(tdQtd);
                tr.appendChild(tdVUnit);
                tr.appendChild(tdVTot);

                itemsTableBody.appendChild(tr);
            });
        } else {
            const tr = document.createElement('tr');
            const td = document.createElement('td');
            td.colSpan = 6;
            td.className = 'text-center';
            td.textContent = 'Nenhum produto discriminado.';
            tr.appendChild(td);
            itemsTableBody.appendChild(tr);
        }

        // 6. Bloco JSON estilizado
        const jsonFormatted = JSON.stringify(data, null, 2);
        jsonOutput.innerHTML = syntaxHighlightJson(jsonFormatted);
    }

    function formatCurrency(val) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(val);
    }

    // =========================================================================
    // 4. NAVEGAÇÃO DE ABAS
    // =========================================================================
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.dataset.tab;

            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            btn.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
        });
    });

    // =========================================================================
    // 5. COPIAR JSON
    // =========================================================================
    btnCopyJson.addEventListener('click', async () => {
        if (!currentExtractedData) return;

        try {
            const jsonText = JSON.stringify(currentExtractedData, null, 2);
            await navigator.clipboard.writeText(jsonText);

            btnCopyText.textContent = 'Copiado!';
            showToast('JSON copiado para a área de transferência!');

            setTimeout(() => {
                btnCopyText.textContent = 'Copiar JSON';
            }, 2000);
        } catch (err) {
            console.error('Falha ao copiar:', err);
            showToast('Não foi possível copiar automaticamente.');
        }
    });

    // =========================================================================
    // 6. SYNTAX HIGHLIGHTING PARA O JSON
    // =========================================================================
    function syntaxHighlightJson(jsonStr) {
        jsonStr = jsonStr.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        return jsonStr.replace(
            /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
            function (match) {
                let cls = 'json-number';
                if (/^"/.test(match)) {
                    if (/:$/.test(match)) {
                        cls = 'json-key';
                    } else {
                        cls = 'json-string';
                    }
                } else if (/true|false/.test(match)) {
                    cls = 'json-boolean';
                } else if (/null/.test(match)) {
                    cls = 'json-null';
                }
                return '<span class="' + cls + '">' + match + '</span>';
            }
        );
    }

    // =========================================================================
    // 7. TOAST NOTIFICATIONS
    // =========================================================================
    let toastTimeout = null;
    function showToast(msg) {
        toast.textContent = msg;
        toast.classList.add('show');

        if (toastTimeout) clearTimeout(toastTimeout);
        toastTimeout = setTimeout(() => {
            toast.classList.remove('show');
        }, 3200);
    }
});

/**
 * Frontend JavaScript - Sistema Administrativo-Financeiro (UniRV)
 * Gerencia Upload da NF, Extração Multimodal com IA e Atividade da 2ª Etapa.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Elementos do Dropzone e Upload
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    const dropzonePrompt = document.getElementById('dropzonePrompt');
    const filePreview = document.getElementById('filePreview');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const btnRemoveFile = document.getElementById('btnRemoveFile');

    // Botão de Extração e Indicadores
    const btnExtrair = document.getElementById('btnExtrair');
    const btnText = document.getElementById('btnText');
    const btnSpinner = document.getElementById('btnSpinner');
    const btnIcon = document.getElementById('btnIcon');
    const agentProcessCard = document.getElementById('agentProcessCard');
    const stepPerceber = document.getElementById('stepPerceber');
    const stepProcessar = document.getElementById('stepProcessar');
    const stepDecidir = document.getElementById('stepDecidir');
    const stepAgir = document.getElementById('stepAgir');

    // Cards de Exibição
    const resultsCard = document.getElementById('resultsCard');
    const etapa2Section = document.getElementById('etapa2Section');

    // Abas de Dados Extraídos
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    // Campos da Aba Formatada
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
    const dispValorTotal = document.getElementById('dispValorTotal');
    const itemsTableBody = document.getElementById('itemsTableBody');

    // Aba JSON
    const jsonOutput = document.getElementById('jsonOutput');
    const btnCopyJson = document.getElementById('btnCopyJson');
    const btnCopyText = document.getElementById('btnCopyText');

    // Elementos da Atividade 2ª Etapa (Páginas 1 e 2 do PDF)
    const analiseFornNome = document.getElementById('analiseFornNome');
    const analiseFornDoc = document.getElementById('analiseFornDoc');
    const analiseFornStatusBadge = document.getElementById('analiseFornStatusBadge');

    const analiseFatNome = document.getElementById('analiseFatNome');
    const analiseFatDoc = document.getElementById('analiseFatDoc');
    const analiseFatStatusBadge = document.getElementById('analiseFatStatusBadge');

    const analiseDespDesc = document.getElementById('analiseDespDesc');
    const analiseDespStatusBadge = document.getElementById('analiseDespStatusBadge');

    const btnLancarBD = document.getElementById('btnLancarBD');
    const boxLancamentoSucesso = document.getElementById('boxLancamentoSucesso');
    const detalhesLancamentoTexto = document.getElementById('detalhesLancamentoTexto');
    const toast = document.getElementById('toast');

    let currentFile = null;
    let currentExtractedData = null;

    // =========================================================================
    // 1. UPLOAD E DRAG & DROP
    // =========================================================================
    if (dropzone) {
        dropzone.addEventListener('click', () => {
            fileInput.click();
        });

        ['dragenter', 'dragover'].forEach(name => {
            dropzone.addEventListener(name, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.add('dropzone-active');
            });
        });

        ['dragleave', 'drop'].forEach(name => {
            dropzone.addEventListener(name, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.remove('dropzone-active');
            });
        });

        dropzone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files && files.length > 0) {
                handleSelectedFile(files[0]);
            }
        });
    }

    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files.length > 0) {
                handleSelectedFile(e.target.files[0]);
            }
        });
    }

    if (btnRemoveFile) {
        btnRemoveFile.addEventListener('click', (e) => {
            e.stopPropagation();
            resetFileSelection();
        });
    }

    function handleSelectedFile(file) {
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            showToast('Apenas arquivos em formato PDF (.pdf) são aceitos.', true);
            return;
        }

        currentFile = file;
        fileName.textContent = file.name;
        const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
        fileSize.textContent = `${sizeMb} MB`;

        dropzonePrompt.classList.add('hidden');
        filePreview.classList.remove('hidden');
        btnExtrair.disabled = false;
    }

    function resetFileSelection() {
        currentFile = null;
        fileInput.value = '';
        dropzonePrompt.classList.remove('hidden');
        filePreview.classList.add('hidden');
        btnExtrair.disabled = true;
        if (agentProcessCard) agentProcessCard.classList.add('hidden');
    }

    // =========================================================================
    // 2. EXTRAÇÃO DE DADOS (ETAPA 1)
    // =========================================================================
    if (btnExtrair) {
        btnExtrair.addEventListener('click', async () => {
            if (!currentFile) return;

            btnExtrair.disabled = true;
            btnSpinner.classList.remove('hidden');
            btnIcon.classList.add('hidden');
            btnText.textContent = 'EXTRAINDO DADOS...';

            if (agentProcessCard) agentProcessCard.classList.remove('hidden');
            highlightStep(stepPerceber);

            const formData = new FormData();
            formData.append('file', currentFile);

            try {
                setTimeout(() => highlightStep(stepProcessar), 600);
                setTimeout(() => highlightStep(stepDecidir), 1200);

                const response = await fetch('/api/extrair', {
                    method: 'POST',
                    body: formData
                });

                highlightStep(stepAgir);

                if (!response.ok) {
                    const err = await response.json();
                    throw new Error(err.detail || 'Falha ao extrair dados do PDF.');
                }

                const result = await response.json();
                currentExtractedData = result.dados;

                // Renderiza Card de Resultados (Figura 2)
                renderResults(currentExtractedData);
                resultsCard.classList.remove('hidden');

                // DISPARA AUTOMATICAMENTE A ATIVIDADE DA 2ª ETAPA:
                // Consulta no Banco se Fornecedor, Faturado e Despesa existem!
                await executarVerificacaoExistencia(currentExtractedData);

                showToast('Nota fiscal extraída e entidades consultadas com sucesso!');

                // Rola para a seção da 2ª Etapa
                etapa2Section.scrollIntoView({ behavior: 'smooth', block: 'start' });

            } catch (error) {
                console.error('Erro na extração:', error);
                showToast(`Erro: ${error.message}`, true);
            } finally {
                btnExtrair.disabled = false;
                btnSpinner.classList.add('hidden');
                btnIcon.classList.remove('hidden');
                btnText.textContent = 'EXTRAIR DADOS';
            }
        });
    }

    function highlightStep(stepEl) {
        [stepPerceber, stepProcessar, stepDecidir, stepAgir].forEach(s => {
            if (s) {
                s.className = 'py-2 px-1 rounded bg-slate-800 border border-slate-700 text-slate-400';
            }
        });
        if (stepEl) {
            stepEl.className = 'py-2 px-1 rounded bg-blue-600 text-white font-bold border border-blue-400 shadow-sm';
        }
    }

    // =========================================================================
    // 3. RENDERIZAÇÃO DOS DADOS EXTRAÍDOS
    // =========================================================================
    function renderResults(data) {
        const classif = (data.classificacao_despesa && data.classificacao_despesa[0]) || {};
        const categoria = data.tipo_despesa || classif.categoria || 'MANUTENÇÃO E OPERAÇÃO';
        const subcategoria = classif.subcategoria || 'Peças e Componentes Operacionais';
        const justificativa = classif.justificativa || 'Classificação realizada com base na análise dos itens da Nota Fiscal.';

        displayCategory.textContent = categoria;
        displaySubcategory.textContent = subcategoria;
        displayJustificativa.textContent = justificativa;

        dispFornecedorRazao.textContent = data.fornecedor?.razao_social || 'NÃO IDENTIFICADO';
        dispFornecedorFantasia.textContent = data.fornecedor?.fantasia || data.fornecedor?.nome_fantasia || '-';
        dispFornecedorCnpj.textContent = data.fornecedor?.cnpj || data.fornecedor?.documento || '-';

        dispFaturadoNome.textContent = data.faturado?.nome || data.faturado?.razao_social || 'NÃO IDENTIFICADO';
        dispFaturadoCpf.textContent = data.faturado?.cpf || data.faturado?.documento || '-';

        dispNumeroNota.textContent = data.numero_nota || data.numero_documento || data.numero || '-';
        dispDataEmissao.textContent = data.data_emissao || '-';
        dispDataVencimento.textContent = data.data_vencimento || '-';

        const valorTotal = typeof data.valor_total === 'number' ? data.valor_total : 0.0;
        dispValorTotal.textContent = formatCurrency(valorTotal);

        // Itens
        itemsTableBody.innerHTML = '';
        const itens = data.descricao_produtos || data.itens || [];

        if (Array.isArray(itens) && itens.length > 0) {
            itens.forEach(item => {
                const tr = document.createElement('tr');
                tr.className = 'hover:bg-slate-50 transition';

                const codigo = typeof item === 'object' ? (item.codigo || '-') : '-';
                const desc = typeof item === 'object' ? (item.descricao || JSON.stringify(item)) : String(item);
                const un = typeof item === 'object' ? (item.unidade || 'UN') : 'UN';
                const qtd = typeof item === 'object' ? (item.quantidade || 1) : 1;
                const vUnit = typeof item === 'object' && typeof item.valor_unitario === 'number' ? formatCurrency(item.valor_unitario) : '-';
                const vTot = typeof item === 'object' && typeof item.valor_total === 'number' ? formatCurrency(item.valor_total) : '-';

                tr.innerHTML = `
                    <td class="py-2.5 px-3 font-mono text-slate-500">${codigo}</td>
                    <td class="py-2.5 px-3 font-medium text-slate-800">${desc}</td>
                    <td class="py-2.5 px-3 text-center font-mono">${un}</td>
                    <td class="py-2.5 px-3 text-right font-medium">${qtd}</td>
                    <td class="py-2.5 px-3 text-right">${vUnit}</td>
                    <td class="py-2.5 px-3 text-right font-bold text-slate-900">${vTot}</td>
                `;
                itemsTableBody.appendChild(tr);
            });
        } else {
            itemsTableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="py-4 text-center text-slate-400">Nenhum produto discriminado no PDF.</td>
                </tr>
            `;
        }

        // Bloco JSON
        const jsonFormatted = JSON.stringify(data, null, 2);
        jsonOutput.innerHTML = syntaxHighlightJson(jsonFormatted);
    }

    // =========================================================================
    // 4. ATIVIDADE 2ª ETAPA: VERIFICAÇÃO DE EXISTÊNCIA NO BANCO (PÁGINA 2 DO PDF)
    // =========================================================================
    async function executarVerificacaoExistencia(data) {
        if (!etapa2Section) return;

        try {
            const res = await fetch('/api/verificar-existencia', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (!res.ok) throw new Error('Falha ao verificar entidades no banco de dados.');

            const resData = await res.json();
            const analise = resData.analise;

            // 1. FORNECEDOR (Exatamente conforme layout da Página 2)
            analiseFornNome.textContent = analise.fornecedor.nome;
            analiseFornDoc.textContent = `CNPJ: ${analise.fornecedor.documento}`;
            if (analise.fornecedor.existe) {
                analiseFornStatusBadge.innerHTML = `
                    <span class="inline-flex items-center gap-1 px-3 py-1 rounded text-xs font-black uppercase bg-emerald-100 text-emerald-800 border border-emerald-300">
                        <span class="w-2 h-2 rounded-full bg-emerald-600"></span>
                        EXISTE – ID: ${analise.fornecedor.id}
                    </span>
                `;
            } else {
                analiseFornStatusBadge.innerHTML = `
                    <span class="inline-flex items-center gap-1 px-3 py-1 rounded text-xs font-black uppercase bg-red-100 text-red-800 border border-red-300">
                        <span class="w-2 h-2 rounded-full bg-red-600"></span>
                        NÃO EXISTE
                    </span>
                `;
            }

            // 2. FATURADO (Exatamente conforme layout da Página 2)
            analiseFatNome.textContent = analise.faturado.nome;
            analiseFatDoc.textContent = `CPF: ${analise.faturado.documento}`;
            if (analise.faturado.existe) {
                analiseFatStatusBadge.innerHTML = `
                    <span class="inline-flex items-center gap-1 px-3 py-1 rounded text-xs font-black uppercase bg-emerald-100 text-emerald-800 border border-emerald-300">
                        <span class="w-2 h-2 rounded-full bg-emerald-600"></span>
                        EXISTE – ID: ${analise.faturado.id}
                    </span>
                `;
            } else {
                analiseFatStatusBadge.innerHTML = `
                    <span class="inline-flex items-center gap-1 px-3 py-1 rounded text-xs font-black uppercase bg-red-100 text-red-800 border border-red-300">
                        <span class="w-2 h-2 rounded-full bg-red-600"></span>
                        NÃO EXISTE
                    </span>
                `;
            }

            // 3. DESPESA (Exatamente conforme layout da Página 2)
            analiseDespDesc.textContent = analise.despesa.descricao;
            if (analise.despesa.existe) {
                analiseDespStatusBadge.innerHTML = `
                    <span class="inline-flex items-center gap-1 px-3 py-1 rounded text-xs font-black uppercase bg-emerald-100 text-emerald-800 border border-emerald-300">
                        <span class="w-2 h-2 rounded-full bg-emerald-600"></span>
                        EXISTE – ID: ${analise.despesa.id}
                    </span>
                `;
            } else {
                analiseDespStatusBadge.innerHTML = `
                    <span class="inline-flex items-center gap-1 px-3 py-1 rounded text-xs font-black uppercase bg-red-100 text-red-800 border border-red-300">
                        <span class="w-2 h-2 rounded-full bg-red-600"></span>
                        NÃO EXISTE
                    </span>
                `;
            }

            // Exibe o Card da 2ª Etapa
            etapa2Section.classList.remove('hidden');
            if (boxLancamentoSucesso) boxLancamentoSucesso.classList.add('hidden');

        } catch (err) {
            console.error('Erro na verificação da Etapa 2:', err);
            showToast('Erro ao verificar entidades no banco de dados', true);
        }
    }

    // =========================================================================
    // 5. CONFIRMAR E GRAVAR NO BANCO DE DADOS (PÁGINA 2 DO PDF)
    // =========================================================================
    if (btnLancarBD) {
        btnLancarBD.addEventListener('click', async () => {
            if (!currentExtractedData) {
                showToast('Nenhum dado de nota fiscal carregado.', true);
                return;
            }

            btnLancarBD.disabled = true;
            btnLancarBD.textContent = 'GRAVANDO NO BANCO...';

            try {
                const res = await fetch('/api/persistir-movimento', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(currentExtractedData)
                });

                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail || 'Falha ao persistir movimento.');
                }

                const lancamento = await res.json();

                if (boxLancamentoSucesso) {
                    boxLancamentoSucesso.classList.remove('hidden');
                    const det = lancamento.detalhes;
                    detalhesLancamentoTexto.innerHTML = `
                        <strong>Lançamento realizado com sucesso:</strong><br>
                        &bull; Movimento <strong>#${det.movimento_id}</strong> (Tipo: <strong>${det.tipo}</strong>)<br>
                        &bull; Fornecedor: <strong>${det.fornecedor.razao_social}</strong> (ID: #${det.fornecedor.id}) ${det.fornecedor.criado_agora ? '<span class="text-xs bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded font-bold">CRIADO NOVO</span>' : '<span class="text-xs bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded">JÁ EXISTIA</span>'}<br>
                        &bull; Faturado: <strong>${det.faturado.razao_social}</strong> (ID: #${det.faturado.id}) ${det.faturado.criado_agora ? '<span class="text-xs bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded font-bold">CRIADO NOVO</span>' : '<span class="text-xs bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded">JÁ EXISTIA</span>'}<br>
                        &bull; Classificação: <strong>${det.despesa.descricao}</strong> (ID: #${det.despesa.id})<br>
                        &bull; Parcelas Geradas: <strong>${det.parcelas.join(', ')}</strong><br>
                        &bull; Valor Total: <strong>${formatCurrency(det.valor_total)}</strong>
                    `;
                    boxLancamentoSucesso.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }

                showToast('5. REGISTRO FOI LANÇADO COM SUCESSO!');

                // Atualiza o diagnóstico na tela para refletir o status atualizado no BD
                await executarVerificacaoExistencia(currentExtractedData);

            } catch (err) {
                console.error('Erro ao persistir movimento:', err);
                showToast(`Erro: ${err.message}`, true);
            } finally {
                btnLancarBD.disabled = false;
                btnLancarBD.innerHTML = `
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg>
                    Confirmar e Gravar no Banco de Dados
                `;
            }
        });
    }

    // =========================================================================
    // 6. CONTROLE DE ABAS E UTILITÁRIOS
    // =========================================================================
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.dataset.tab;
            tabBtns.forEach(b => {
                b.className = 'tab-btn px-4 py-1.5 rounded-md transition text-slate-600 hover:text-slate-900';
            });
            tabContents.forEach(c => c.classList.add('hidden'));

            btn.className = 'tab-btn px-4 py-1.5 rounded-md transition bg-white text-slate-900 shadow-sm font-bold';
            document.getElementById(target).classList.remove('hidden');
        });
    });

    if (btnCopyJson) {
        btnCopyJson.addEventListener('click', async () => {
            if (!currentExtractedData) return;
            try {
                await navigator.clipboard.writeText(JSON.stringify(currentExtractedData, null, 2));
                btnCopyText.textContent = 'Copiado!';
                showToast('JSON copiado com sucesso!');
                setTimeout(() => { btnCopyText.textContent = 'Copiar JSON'; }, 2000);
            } catch {
                showToast('Falha ao copiar JSON para a área de transferência.', true);
            }
        });
    }

    function formatCurrency(v) {
        return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v || 0);
    }

    function syntaxHighlightJson(jsonStr) {
        jsonStr = jsonStr.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        return jsonStr.replace(
            /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
            function (match) {
                let cls = 'json-number';
                if (/^"/.test(match)) {
                    cls = (/:$/.test(match)) ? 'json-key' : 'json-string';
                } else if (/true|false/.test(match)) {
                    cls = 'json-boolean';
                }
                return '<span class="' + cls + '">' + match + '</span>';
            }
        );
    }

    let toastTimer = null;
    function showToast(msg, isError = false) {
        if (!toast) return;
        toast.textContent = msg;
        toast.className = `fixed bottom-5 right-5 px-5 py-3 rounded-lg shadow-xl text-white font-semibold text-xs transition-opacity duration-300 opacity-100 z-50 ${isError ? 'bg-red-600 border border-red-500' : 'bg-slate-900 border border-slate-700'}`;
        clearTimeout(toastTimer);
        toastTimer = setTimeout(() => {
            toast.classList.remove('opacity-100');
            toast.classList.add('opacity-0');
        }, 3200);
    }
});

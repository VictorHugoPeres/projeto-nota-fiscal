/**
 * Gerenciador Genérico de CRUDs - Etapa 2 (UniRV - ESW424)
 * Atende estritamente às regras da página 4 do documento:
 * a. Trazer a tabela de registros vazia
 * b. Carregar dados através da Busca ou TODOS
 * c. TODOS carrega status = ATIVO
 * d. Indexação por coluna na tabela
 * e. Busca por mais de um elemento
 * f. Duas ações na tabela: Editar / Excluir (Lógico)
 * g. No CREATE campo STATUS oculto == ATIVO
 * h. No UPDATE campo STATUS oculto
 * i. No DELETE altera campo STATUS == INATIVO
 * j. Possibilidade de REATIVAR registro INATIVO
 */

class CrudManager {
    constructor(config) {
        this.endpoint = config.endpoint; // Ex: '/api/pessoas'
        this.tableBodyId = config.tableBodyId;
        this.searchInputId = config.searchInputId;
        this.btnBuscarId = config.btnBuscarId;
        this.btnTodosId = config.btnTodosId;
        this.btnNovoId = config.btnNovoId;
        this.modalId = config.modalId;
        this.formId = config.formId;
        this.filterInativosCheckboxId = config.filterInativosCheckboxId;
        this.renderRowCallback = config.renderRow;
        this.fillFormCallback = config.fillForm;
        this.getFormDataCallback = config.getFormData;

        this.itens = [];
        this.init();
    }

    init() {
        // Event Listeners de Busca e Ações
        const btnBuscar = document.getElementById(this.btnBuscarId);
        if (btnBuscar) {
            btnBuscar.addEventListener('click', () => this.buscar());
        }

        const searchInput = document.getElementById(this.searchInputId);
        if (searchInput) {
            searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.buscar();
                }
            });
        }

        const btnTodos = document.getElementById(this.btnTodosId);
        if (btnTodos) {
            btnTodos.addEventListener('click', () => this.carregarTodos());
        }

        const btnNovo = document.getElementById(this.btnNovoId);
        if (btnNovo) {
            btnNovo.addEventListener('click', () => this.abrirModalNovo());
        }

        const filterInativos = document.getElementById(this.filterInativosCheckboxId);
        if (filterInativos) {
            filterInativos.addEventListener('change', () => {
                const buscaVal = document.getElementById(this.searchInputId)?.value || '';
                if (buscaVal) {
                    this.buscar();
                } else {
                    this.carregarTodos();
                }
            });
        }

        // Fechar modal ao clicar fora ou no botão cancelar
        const modal = document.getElementById(this.modalId);
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) this.fecharModal();
            });
            const btnsCancelar = modal.querySelectorAll('.btn-cancelar');
            btnsCancelar.forEach(btn => {
                btn.addEventListener('click', () => this.fecharModal());
            });
        }

        // Submissão do Formulário
        const form = document.getElementById(this.formId);
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.salvar();
            });
        }
    }

    async carregarTodos() {
        const incluirInativos = document.getElementById(this.filterInativosCheckboxId)?.checked || false;
        try {
            const res = await fetch(`${this.endpoint}?carregar_todos=true&incluir_inativos=${incluirInativos}`);
            const data = await res.json();
            this.itens = data;
            this.renderizar();
        } catch (err) {
            this.mostrarToast('Erro ao carregar dados: ' + err.message, true);
        }
    }

    async buscar() {
        const termo = document.getElementById(this.searchInputId)?.value.trim() || '';
        const incluirInativos = document.getElementById(this.filterInativosCheckboxId)?.checked || false;
        if (!termo) {
            this.mostrarToast('Digite um termo para pesquisar ou clique em TODOS', true);
            return;
        }

        try {
            const res = await fetch(`${this.endpoint}?busca=${encodeURIComponent(termo)}&incluir_inativos=${incluirInativos}`);
            const data = await res.json();
            this.itens = data;
            this.renderizar();
        } catch (err) {
            this.mostrarToast('Erro na pesquisa: ' + err.message, true);
        }
    }

    renderizar() {
        const tbody = document.getElementById(this.tableBodyId);
        if (!tbody) return;

        if (!this.itens || this.itens.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="10" class="py-8 text-center text-slate-400">
                        Nenhum registro encontrado.
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = this.itens.map(item => this.renderRowCallback(item)).join('');
    }

    abrirModalNovo() {
        const form = document.getElementById(this.formId);
        if (form) {
            form.reset();
            const idInput = form.querySelector('[name="id"]');
            if (idInput) idInput.value = '';
        }
        const modal = document.getElementById(this.modalId);
        if (modal) {
            const title = modal.querySelector('.modal-title');
            if (title) title.innerText = 'Novo Registro';
            modal.style.display = 'flex';
        }
    }

    abrirModalEditar(id) {
        const item = this.itens.find(i => i.id === id);
        if (!item) return;

        const form = document.getElementById(this.formId);
        if (form && this.fillFormCallback) {
            form.reset();
            this.fillFormCallback(form, item);
        }
        const modal = document.getElementById(this.modalId);
        if (modal) {
            const title = modal.querySelector('.modal-title');
            if (title) title.innerText = 'Editar Registro #' + id;
            modal.style.display = 'flex';
        }
    }

    fecharModal() {
        const modal = document.getElementById(this.modalId);
        if (modal) modal.style.display = 'none';
    }

    async salvar() {
        const form = document.getElementById(this.formId);
        if (!form) return;

        const idInput = form.querySelector('[name="id"]');
        const id = idInput ? idInput.value : '';
        const dados = this.getFormDataCallback(form);

        const isEdicao = Boolean(id);
        const url = isEdicao ? `${this.endpoint}/${id}` : this.endpoint;
        const method = isEdicao ? 'PUT' : 'POST';

        try {
            const res = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(dados)
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || 'Falha ao salvar registro');
            }

            this.fecharModal();
            this.mostrarToast(isEdicao ? 'Registro atualizado com sucesso!' : 'Registro criado com sucesso!');
            this.carregarTodos();
        } catch (err) {
            this.mostrarToast(err.message, true);
        }
    }

    async excluirLogico(id) {
        // Verificação preventiva de permissão para cliente
        if (window.USUARIO_ATUAL && window.USUARIO_ATUAL.role === 'cliente' && this.endpoint.includes('/movimentos')) {
            this.mostrarToast('Acesso negado: Perfil de Cliente não tem permissão para inativar contas.', true);
            return;
        }

        if (!confirm('Deseja realmente inativar este registro?')) return;

        try {
            const res = await fetch(`${this.endpoint}/${id}`, { method: 'DELETE' });
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || 'Falha ao inativar registro');
            }

            this.mostrarToast('Registro inativado com sucesso!');
            this.carregarTodos();
        } catch (err) {
            this.mostrarToast(err.message, true);
        }
    }

    async reativar(id) {
        if (window.USUARIO_ATUAL && window.USUARIO_ATUAL.role === 'cliente' && this.endpoint.includes('/movimentos')) {
            this.mostrarToast('Acesso negado: Perfil de Cliente não tem permissão para reativar contas.', true);
            return;
        }

        try {
            const res = await fetch(`${this.endpoint}/${id}/reativar`, { method: 'PATCH' });
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || 'Falha ao reativar registro');
            }

            this.mostrarToast('Registro reativado com sucesso!');
            this.carregarTodos();
        } catch (err) {
            this.mostrarToast(err.message, true);
        }
    }

    /**
     * Exibe notificação flutuante com posicionamento FIXO garantido,
     * impedindo qualquer quebra de layout ou sangramento de cores na página.
     */
    mostrarToast(mensagem, isErro = false) {
        let toast = document.getElementById('toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'toast';
            document.body.appendChild(toast);
        }

        // Estilização inline explícita para NUNCA interferir no flex/grid do body
        toast.style.position = 'fixed';
        toast.style.bottom = '24px';
        toast.style.right = '24px';
        toast.style.zIndex = '99999';
        toast.style.maxWidth = '420px';
        toast.style.padding = '12px 20px';
        toast.style.borderRadius = '10px';
        toast.style.color = '#ffffff';
        toast.style.fontWeight = '600';
        toast.style.fontSize = '14px';
        toast.style.boxShadow = '0 10px 25px -5px rgba(0, 0, 0, 0.35)';
        toast.style.backgroundColor = isErro ? '#dc2626' : '#16a34a';
        toast.style.display = 'block';
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
        toast.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        toast.style.pointerEvents = 'auto';
        toast.innerText = mensagem;

        clearTimeout(this._toastTimeout);
        this._toastTimeout = setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
            setTimeout(() => {
                if (toast.style.opacity === '0') {
                    toast.style.display = 'none';
                }
            }, 300);
        }, 3800);
    }
}

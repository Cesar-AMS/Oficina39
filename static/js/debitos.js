let debitos = [];
let debitosFiltrados = [];
let paginaDebitosAtual = 1;
const DEBITOS_POR_PAGINA = 15;
let paginacaoDebitosEl;

function alertErro(mensagem) {
    if (window.ui) return window.ui.error(mensagem);
    alert(`Erro: ${mensagem}`);
}

function formatarValor(valor) {
    return (Number(valor || 0)).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function classeStatusFinanceiro(status) {
    return (status || '').toLowerCase().replace(/\s+/g, '-');
}

function normalizarBusca(valor) {
    return String(valor || '')
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase()
        .trim();
}

function soDigitos(valor) {
    return String(valor || '').replace(/\D/g, '');
}

function renderPaginacaoDebitos(lista) {
    if (!paginacaoDebitosEl) return;

    const totalItens = lista.length;
    const totalPaginas = Math.max(1, Math.ceil(totalItens / DEBITOS_POR_PAGINA));
    paginaDebitosAtual = Math.min(Math.max(1, paginaDebitosAtual), totalPaginas);

    if (!totalItens) {
        paginacaoDebitosEl.innerHTML = '';
        return;
    }

    const inicio = ((paginaDebitosAtual - 1) * DEBITOS_POR_PAGINA) + 1;
    const fim = Math.min(totalItens, paginaDebitosAtual * DEBITOS_POR_PAGINA);

    let html = `
        <div class="paginacao-info">Mostrando ${inicio}-${fim} de ${totalItens} registros</div>
        <div class="paginacao-acoes">
            <button class="paginacao-btn" data-pagina="${paginaDebitosAtual - 1}" ${paginaDebitosAtual === 1 ? 'disabled' : ''}>Anterior</button>
    `;

    for (let pagina = 1; pagina <= totalPaginas; pagina += 1) {
        html += `<button class="paginacao-btn ${pagina === paginaDebitosAtual ? 'ativo' : ''}" data-pagina="${pagina}">${pagina}</button>`;
    }

    html += `
            <button class="paginacao-btn" data-pagina="${paginaDebitosAtual + 1}" ${paginaDebitosAtual === totalPaginas ? 'disabled' : ''}>Proxima</button>
        </div>
    `;

    paginacaoDebitosEl.innerHTML = html;
    paginacaoDebitosEl.querySelectorAll('[data-pagina]').forEach((botao) => {
        botao.addEventListener('click', () => {
            const proximaPagina = Number(botao.getAttribute('data-pagina'));
            if (!Number.isFinite(proximaPagina) || proximaPagina === paginaDebitosAtual) return;
            paginaDebitosAtual = proximaPagina;
            renderTabelaDebitos(debitosFiltrados);
        });
    });
}

function filtrarDebitos(termo) {
    const texto = normalizarBusca(termo);
    const digitos = soDigitos(termo);

    if (!texto && !digitos) {
        debitosFiltrados = [...debitos];
        paginaDebitosAtual = 1;
        renderTabelaDebitos(debitosFiltrados);
        return;
    }

    debitosFiltrados = debitos.filter((ordem) => {
        const clienteNome = normalizarBusca(ordem.cliente_nome || ordem.cliente?.nome_cliente || '');
        const cpf = soDigitos(ordem.cliente?.cpf || '');
        const placa = normalizarBusca(ordem.cliente?.placa || '');
        return (
            clienteNome.includes(texto)
            || (!!digitos && cpf.includes(digitos))
            || placa.includes(texto)
        );
    });

    paginaDebitosAtual = 1;
    renderTabelaDebitos(debitosFiltrados);
}

function renderTabelaDebitos(lista) {
    const tbody = document.getElementById('tabelaDebitos');
    if (!tbody) return;

    if (!lista.length) {
        renderPaginacaoDebitos([]);
        tbody.innerHTML = `<tr><td colspan="8" class="text-center mensagem-carregando">Nenhum débito em aberto.</td></tr>`;
        return;
    }

    const inicio = (paginaDebitosAtual - 1) * DEBITOS_POR_PAGINA;
    const listaPagina = lista.slice(inicio, inicio + DEBITOS_POR_PAGINA);

    tbody.innerHTML = listaPagina.map((ordem) => `
        <tr>
            <td><strong>#${ordem.id}</strong></td>
            <td>
                <div class="cliente-bloco">
                    <span class="cliente-nome">${ordem.cliente_nome || '---'}</span>
                    <span class="cliente-detalhe">${ordem.cliente?.telefone || 'Telefone não informado'}</span>
                </div>
            </td>
            <td>${ordem.cliente?.fabricante || ''} ${ordem.cliente?.modelo || ''} ${ordem.cliente?.placa ? `- ${ordem.cliente.placa}` : ''}</td>
            <td>${formatarValor(ordem.total_cobrado ?? ordem.total_geral)}</td>
            <td>${formatarValor(ordem.total_pago)}</td>
            <td>${formatarValor(ordem.saldo_pendente)}</td>
            <td><span class="status-financeiro ${classeStatusFinanceiro(ordem.status_financeiro)}">${ordem.status_financeiro || '---'}</span></td>
            <td>
                <div class="acoes-debito">
                    <a class="btn btn-salvar btn-compact" href="/fluxo_caixa.html?ordem_id=${ordem.id}&origem=debitos">Receber</a>
                    <a class="btn btn-voltar btn-compact" href="/visualizarOS.html?id=${ordem.id}&origem=debitos">Ver OS</a>
                </div>
            </td>
        </tr>
    `).join('');
    renderPaginacaoDebitos(lista);
}

async function carregarDebitos() {
    try {
        const response = await fetch('/api/debitos/');
        const dados = await response.json();
        if (!response.ok) throw new Error(dados.erro || 'Erro ao carregar débitos.');
        debitos = Array.isArray(dados) ? dados : [];
        debitosFiltrados = [...debitos];
        paginaDebitosAtual = 1;
        renderTabelaDebitos(debitosFiltrados);
    } catch (error) {
        alertErro(error.message);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const campoBusca = document.getElementById('buscaDebitos');
    paginacaoDebitosEl = document.getElementById('paginacaoDebitos');
    if (campoBusca) {
        campoBusca.addEventListener('input', (event) => filtrarDebitos(event.target.value || ''));
    }
    carregarDebitos();
});


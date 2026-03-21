let debitos = [];
let debitosFiltrados = [];

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

function filtrarDebitos(termo) {
    const texto = normalizarBusca(termo);
    const digitos = soDigitos(termo);

    if (!texto && !digitos) {
        debitosFiltrados = [...debitos];
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

    renderTabelaDebitos(debitosFiltrados);
}

function renderTabelaDebitos(lista) {
    const tbody = document.getElementById('tabelaDebitos');
    if (!tbody) return;

    if (!lista.length) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center mensagem-carregando">Nenhum débito em aberto.</td></tr>`;
        return;
    }

    tbody.innerHTML = lista.map((ordem) => `
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
}

async function carregarDebitos() {
    try {
        const response = await fetch('/api/debitos/');
        const dados = await response.json();
        if (!response.ok) throw new Error(dados.erro || 'Erro ao carregar débitos.');
        debitos = Array.isArray(dados) ? dados : [];
        debitosFiltrados = [...debitos];
        renderTabelaDebitos(debitosFiltrados);
    } catch (error) {
        alertErro(error.message);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const campoBusca = document.getElementById('buscaDebitos');
    if (campoBusca) {
        campoBusca.addEventListener('input', (event) => filtrarDebitos(event.target.value || ''));
    }
    carregarDebitos();
});


let debitos = [];
let debitoSelecionado = null;

function alertErro(mensagem) {
    if (window.ui) return window.ui.error(mensagem);
    alert(`Erro: ${mensagem}`);
}

function alertSucesso(mensagem) {
    if (window.ui) return window.ui.success(mensagem);
    alert(`Sucesso: ${mensagem}`);
}

function formatarValor(valor) {
    return (Number(valor || 0)).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function classeStatusFinanceiro(status) {
    return (status || '').toLowerCase().replace(/\s+/g, '-');
}

function atualizarResumoDebitos() {
    const quantidade = debitos.length;
    const saldo = debitos.reduce((acc, item) => acc + (Number(item.saldo_pendente || 0)), 0);
    document.getElementById('resumoQuantidade').textContent = String(quantidade);
    document.getElementById('resumoSaldo').textContent = formatarValor(saldo);
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
                    <button class="btn btn-salvar btn-compact" onclick="abrirModalDebito(${ordem.id})">💵 Receber</button>
                    <a class="btn btn-voltar btn-compact" href="/visualizarOS.html?id=${ordem.id}&origem=debitos">👁 Ver OS</a>
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
        atualizarResumoDebitos();
        renderTabelaDebitos(debitos);
    } catch (error) {
        alertErro(error.message);
    }
}

function recalcularResumoModalDebito() {
    const linhas = document.querySelectorAll('#corpoPagamentosDebito tr');
    const totalLancado = Array.from(linhas).reduce((acc, linha) => {
        const valor = parseFloat(linha.querySelector('.input-valor-pagamento')?.value) || 0;
        return acc + valor;
    }, 0);
    const saldoBase = Number(debitoSelecionado?.saldo_pendente || 0);
    const saldoApos = Math.max(0, saldoBase - totalLancado);
    document.getElementById('totalLancadoDebito').textContent = formatarValor(totalLancado);
    document.getElementById('saldoAposDebito').textContent = formatarValor(saldoApos);
}

function adicionarLinhaPagamentoDebito(dados = {}) {
    const tbody = document.getElementById('corpoPagamentosDebito');
    if (!tbody) return;
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td>
            <select class="select-forma-pagamento">
                <option value="">Selecione</option>
                <option value="Pix">Pix</option>
                <option value="Cartão">Cartão</option>
                <option value="Dinheiro">Dinheiro</option>
                <option value="Boleto">Boleto</option>
            </select>
        </td>
        <td><input type="number" class="input-valor-pagamento" step="0.01" min="0.01" placeholder="0,00"></td>
        <td><input type="text" class="input-observacao-pagamento" placeholder="Observação opcional"></td>
        <td><button type="button" class="btn btn-cancelar btn-compact" onclick="removerLinhaPagamentoDebito(this)">✕</button></td>
    `;
    tbody.appendChild(tr);

    const select = tr.querySelector('.select-forma-pagamento');
    const valor = tr.querySelector('.input-valor-pagamento');
    const observacao = tr.querySelector('.input-observacao-pagamento');
    if (dados.forma_pagamento) select.value = dados.forma_pagamento;
    if (dados.valor) valor.value = dados.valor;
    if (dados.observacao) observacao.value = dados.observacao;

    valor.addEventListener('input', recalcularResumoModalDebito);
    valor.addEventListener('wheel', (e) => {
        e.preventDefault();
        valor.blur();
    }, { passive: false });
    select.focus();
    recalcularResumoModalDebito();
}

function removerLinhaPagamentoDebito(botao) {
    const tr = botao.closest('tr');
    tr?.remove();
    recalcularResumoModalDebito();
}

function abrirModalDebito(ordemId) {
    debitoSelecionado = debitos.find((item) => item.id === ordemId) || null;
    if (!debitoSelecionado) {
        alertErro('Débito não encontrado.');
        return;
    }

    document.getElementById('debitoOsNumero').textContent = `#${debitoSelecionado.id}`;
    document.getElementById('debitoClienteNome').textContent = debitoSelecionado.cliente_nome || '---';
    document.getElementById('debitoSaldoPendente').textContent = formatarValor(debitoSelecionado.saldo_pendente);
    document.getElementById('corpoPagamentosDebito').innerHTML = '';
    adicionarLinhaPagamentoDebito({ valor: Number(debitoSelecionado.saldo_pendente || 0).toFixed(2) });
    document.getElementById('modalPagamentoDebito').style.display = 'flex';
}

function fecharModalDebito() {
    document.getElementById('modalPagamentoDebito').style.display = 'none';
    debitoSelecionado = null;
}

async function salvarPagamentosDebito() {
    if (!debitoSelecionado) return;

    const pagamentos = Array.from(document.querySelectorAll('#corpoPagamentosDebito tr')).map((linha) => ({
        forma_pagamento: linha.querySelector('.select-forma-pagamento')?.value || '',
        valor: parseFloat(linha.querySelector('.input-valor-pagamento')?.value) || 0,
        observacao: linha.querySelector('.input-observacao-pagamento')?.value || ''
    })).filter((item) => item.forma_pagamento && item.valor > 0);

    if (!pagamentos.length) {
        alertErro('Informe pelo menos um pagamento válido.');
        return;
    }

    try {
        const response = await fetch(`/api/debitos/${debitoSelecionado.id}/pagamentos`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pagamentos })
        });
        const dados = await response.json();
        if (!response.ok) throw new Error(dados.erro || 'Erro ao registrar pagamento.');
        alertSucesso('Pagamento registrado com sucesso.');
        fecharModalDebito();
        carregarDebitos();
    } catch (error) {
        alertErro(error.message);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    carregarDebitos();
});

window.abrirModalDebito = abrirModalDebito;
window.fecharModalDebito = fecharModalDebito;
window.adicionarLinhaPagamentoDebito = adicionarLinhaPagamentoDebito;
window.removerLinhaPagamentoDebito = removerLinhaPagamentoDebito;
window.salvarPagamentosDebito = salvarPagamentosDebito;

function alertErro(mensagem) {
    if (window.ui) return window.ui.error(mensagem);
    alert(`Erro: ${mensagem}`);
}

function alertSucesso(mensagem) {
    if (window.ui) return window.ui.success(mensagem);
    alert(`Sucesso: ${mensagem}`);
}

let relatorioSelecionado = null;
let profissionaisCadastrados = [];

function formatarMoeda(valor) {
    return 'R$ ' + (Number(valor || 0)).toFixed(2).replace('.', ',');
}

function formatarDataBR(valor) {
    if (!valor) return '-';
    const texto = String(valor).trim();
    if (/^\d{4}-\d{2}-\d{2}$/.test(texto)) {
        const [ano, mes, dia] = texto.split('-');
        return `${dia}/${mes}/${ano}`;
    }
    return texto;
}

function formatarPeriodo(intervalo) {
    if (!intervalo) return '-';
    return `${formatarDataBR(intervalo.inicio)} até ${formatarDataBR(intervalo.fim)}`;
}

function preencherTabela(idTabela, servicos) {
    const tbody = document.getElementById(idTabela);
    if (!tbody) return;

    if (!servicos || servicos.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="sem-dados">Nenhum serviço no período.</td></tr>`;
        return;
    }

    tbody.innerHTML = servicos.map((item) => `
        <tr>
            <td>#${item.ordem_id || '-'}</td>
            <td>${item.data_referencia || '-'}</td>
            <td>${item.cliente || '-'}</td>
            <td>${item.descricao_servico || '-'}</td>
            <td>${formatarMoeda(item.valor_servico || 0)}</td>
        </tr>
    `).join('');
}

function nomePeriodo(chave) {
    return chave || '-';
}

function emojiPeriodo(chave) {
    return chave ? '📅' : '📊';
}

function preencherPeriodo(bloco, periodoSelecionado, intervaloCustom = null) {
    const resumo = bloco?.resumo || {};
    const intervalo = intervaloCustom || bloco?.intervalo || {};

    document.getElementById('periodoSelecionado').textContent = nomePeriodo(periodoSelecionado);
    document.getElementById('tituloPeriodoSelecionado').textContent = `Resultado ${nomePeriodo(periodoSelecionado)}`;
    document.getElementById('periodoQtd').textContent = Number(resumo.quantidade_servicos || 0);
    document.getElementById('periodoTotal').textContent = formatarMoeda(resumo.valor_total || 0);
    document.getElementById('periodoMedia').textContent = formatarMoeda(resumo.media_por_servico || 0);
    document.getElementById('periodoIntervalo').textContent = formatarPeriodo(intervalo);
    preencherTabela('periodoTabela', bloco?.servicos || []);
}

function preencherSelectProfissionais(lista) {
    const select = document.getElementById('profissionalBusca');
    if (!select) return;
    const opcoes = ['<option value="">Selecione um profissional cadastrado</option>'];
    (lista || []).forEach((item) => {
        const nome = (item?.profissional || '').trim();
        if (!nome) return;
        opcoes.push(`<option value="${nome}">${nome}</option>`);
    });
    select.innerHTML = opcoes.join('');
}

async function carregarSugestoesProfissionais(termo = '') {
    try {
        const response = await fetch(`/api/relatorios/producao-profissionais/profissionais?termo=${encodeURIComponent(termo)}`);
        const dados = await response.json();
        if (!response.ok) throw new Error(dados?.erro || 'Falha ao carregar profissionais.');

        profissionaisCadastrados = Array.isArray(dados) ? dados : [];
        preencherSelectProfissionais(profissionaisCadastrados);
    } catch (error) {
        profissionaisCadastrados = [];
        preencherSelectProfissionais([]);
        console.error(error);
    }
}

async function buscarResumoProfissional() {
    const profissional = (document.getElementById('profissionalBusca')?.value || '').trim();
    const dataInicio = document.getElementById('dataInicio')?.value || '';
    const dataFim = document.getElementById('dataFim')?.value || '';

    if (!profissionaisCadastrados.length) {
        alertErro('Não há profissionais cadastrados/ativos. Cadastre ao menos um profissional para gerar relatório.');
        return;
    }
    if (!profissional) {
        alertErro('Selecione um profissional cadastrado para pesquisar.');
        return;
    }
    const profissionalValido = profissionaisCadastrados.some((p) => (p.profissional || '').trim() === profissional);
    if (!profissionalValido) {
        alertErro('Profissional inválido. Selecione um profissional cadastrado.');
        return;
    }
    if (!dataInicio || !dataFim) {
        alertErro('Informe data início e data fim.');
        return;
    }

    const dtInicio = new Date(`${dataInicio}T00:00:00`);
    const dtFim = new Date(`${dataFim}T00:00:00`);
    if (dtFim < dtInicio) {
        alertErro('Data fim deve ser maior ou igual à data início.');
        return;
    }
    const diffDias = Math.floor((dtFim - dtInicio) / (1000 * 60 * 60 * 24)) + 1;
    if (diffDias > 31) {
        alertErro('O período máximo permitido é de 31 dias.');
        return;
    }

    const periodoSelecionado = `${formatarDataBR(dataInicio)} até ${formatarDataBR(dataFim)}`;
    const params = new URLSearchParams();
    params.set('profissional', profissional);
    params.set('data_inicio', dataInicio);
    params.set('data_fim', dataFim);

    try {
        const response = await fetch(`/api/relatorios/producao-profissionais/resumo-profissional-periodo?${params.toString()}`);
        const dados = await response.json();
        if (!response.ok) {
            throw new Error(dados.erro || 'Falha ao consultar produção.');
        }

        document.getElementById('profissionalSelecionado').textContent = dados.profissional || '-';
        const blocoSelecionado = { resumo: dados.resumo || {}, servicos: dados.servicos || [] };
        preencherPeriodo(
            blocoSelecionado,
            periodoSelecionado,
            { inicio: dados.periodo?.inicio, fim: dados.periodo?.fim }
        );
        relatorioSelecionado = {
            profissional: dados.profissional || '-',
            periodo: periodoSelecionado,
            dataReferencia: dataFim || '',
            dataInicio: dataInicio,
            dataFim: dataFim,
            bloco: blocoSelecionado || { resumo: {}, intervalo: {}, servicos: [] },
            intervalo: { inicio: dados.periodo?.inicio, fim: dados.periodo?.fim }
        };
    } catch (error) {
        alertErro(error.message);
    }
}

function baixarRelatorioSelecionado() {
    if (!profissionaisCadastrados.length) {
        alertErro('Não há profissionais cadastrados/ativos. Cadastre ao menos um profissional para gerar relatório.');
        return;
    }
    if (!relatorioSelecionado) {
        alertErro('Pesquise um profissional antes de fazer download.');
        return;
    }

    const { profissional, dataInicio, dataFim } = relatorioSelecionado;
    if (!profissional || !dataInicio || !dataFim) {
        alertErro('Período/profissional inválido para exportação.');
        return;
    }

    const params = new URLSearchParams();
    params.set('profissional', profissional);
    params.set('data_inicio', dataInicio);
    params.set('data_fim', dataFim);

    fetch(`/api/relatorios/producao-profissionais/exportar-excel-profissional?${params.toString()}`)
        .then(async (response) => {
            if (!response.ok) {
                const erro = await response.json().catch(() => ({}));
                throw new Error(erro.erro || 'Falha ao exportar Excel do profissional.');
            }
            return response.blob();
        })
        .then((blob) => {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            const nomeArq = `producao_profissional_${profissional.replace(/\s+/g, '_')}_${dataFim.replace(/-/g, '_')}.xlsx`;
            a.href = url;
            a.download = nomeArq;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
            alertSucesso('Excel baixado com sucesso.');
        })
        .catch((error) => alertErro(error.message));
}

function valorMesContabil() {
    return (document.getElementById('mesContabil')?.value || '').trim();
}

function setTexto(id, valor) {
    const el = document.getElementById(id);
    if (el) el.textContent = valor;
}

function renderTabelaPagamentos(lista) {
    const tbody = document.getElementById('contabTabelaPagamentos');
    if (!tbody) return;
    if (!lista || lista.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="sem-dados">Sem dados.</td></tr>';
        return;
    }
    tbody.innerHTML = lista.map((item) => `
        <tr>
            <td>${item.forma_pagamento || 'Não informado'}</td>
            <td>${Number(item.quantidade || 0)}</td>
            <td>${formatarMoeda(item.valor_total || 0)}</td>
        </tr>
    `).join('');
}

function renderTabelaOperacional(idTabela, colunas, linhas) {
    const tbody = document.getElementById(idTabela);
    if (!tbody) return;
    if (!linhas || linhas.length === 0) {
        tbody.innerHTML = `<tr><td colspan="${colunas}" class="sem-dados">Sem dados.</td></tr>`;
        return;
    }
    tbody.innerHTML = linhas.join('');
}

function valorData(id) {
    return (document.getElementById(id)?.value || '').trim();
}

async function carregarRelatorioOperacional() {
    const dataInicio = valorData('opDataInicio');
    const dataFim = valorData('opDataFim');
    if (!dataInicio || !dataFim) {
        alertErro('Informe data início e data fim para o relatório operacional.');
        return;
    }
    if (new Date(`${dataFim}T00:00:00`) < new Date(`${dataInicio}T00:00:00`)) {
        alertErro('Data fim deve ser maior ou igual à data início.');
        return;
    }

    const params = new URLSearchParams();
    params.set('data_inicio', dataInicio);
    params.set('data_fim', dataFim);

    try {
        const response = await fetch(`/api/relatorios/operacional-servicos-pecas-saidas?${params.toString()}`);
        const dados = await response.json();
        if (!response.ok) throw new Error(dados.erro || 'Falha ao carregar relatório operacional.');

        const resumo = dados.resumo || {};
        setTexto('opQtdServicos', String(resumo.quantidade_servicos || 0));
        setTexto('opTotalServicos', formatarMoeda(resumo.valor_servicos || 0));
        setTexto('opQtdPecas', String(resumo.quantidade_pecas || 0));
        setTexto('opTotalPecas', formatarMoeda(resumo.valor_pecas || 0));
        setTexto('opQtdSaidas', String(resumo.quantidade_saidas || 0));
        setTexto('opTotalSaidas', formatarMoeda(resumo.valor_saidas || 0));
        setTexto('opPeriodo', `${formatarDataBR(dados.periodo?.inicio)} até ${formatarDataBR(dados.periodo?.fim)}`);

        renderTabelaOperacional('opTabelaServicos', 5, (dados.servicos || []).map((item) => `
            <tr>
                <td>#${item.ordem_id || '-'}</td>
                <td>${item.data_referencia || '-'}</td>
                <td>${item.profissional || '-'}</td>
                <td>${item.descricao || '-'}</td>
                <td>${formatarMoeda(item.valor || 0)}</td>
            </tr>
        `));

        renderTabelaOperacional('opTabelaPecas', 5, (dados.pecas || []).map((item) => `
            <tr>
                <td>#${item.ordem_id || '-'}</td>
                <td>${item.data_referencia || '-'}</td>
                <td>${item.descricao || '-'}</td>
                <td>${Number(item.quantidade || 0)}</td>
                <td>${formatarMoeda(item.valor_total || 0)}</td>
            </tr>
        `));

        renderTabelaOperacional('opTabelaSaidas', 4, (dados.saidas || []).map((item) => `
            <tr>
                <td>${item.data_referencia || '-'}</td>
                <td>${item.categoria || '-'}</td>
                <td>${item.descricao || '-'}</td>
                <td>${formatarMoeda(item.valor || 0)}</td>
            </tr>
        `));
    } catch (error) {
        alertErro(error.message);
    }
}

async function baixarExcelOperacional() {
    const dataInicio = valorData('opDataInicio');
    const dataFim = valorData('opDataFim');
    if (!dataInicio || !dataFim) {
        alertErro('Informe data início e data fim para download.');
        return;
    }
    const params = new URLSearchParams();
    params.set('data_inicio', dataInicio);
    params.set('data_fim', dataFim);
    try {
        const response = await fetch(`/api/relatorios/operacional-servicos-pecas-saidas/exportar-excel?${params.toString()}`);
        if (!response.ok) {
            const erro = await response.json().catch(() => ({}));
            throw new Error(erro.erro || 'Falha ao exportar Excel operacional.');
        }
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `operacional_servicos_pecas_saidas_${dataInicio.replace(/-/g, '_')}_${dataFim.replace(/-/g, '_')}.xlsx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        alertSucesso('Excel baixado com sucesso.');
    } catch (error) {
        alertErro(error.message);
    }
}

async function carregarContabilidadeGeral() {
    const mes = valorMesContabil();
    const query = mes ? `?mes=${encodeURIComponent(mes)}` : '';
    try {
        const response = await fetch(`/api/relatorios/contabilidade-geral${query}`);
        const dados = await response.json();
        if (!response.ok) throw new Error(dados.erro || 'Falha ao carregar contabilidade.');

        setTexto('contabFaturamento', formatarMoeda(dados.faturamento_bruto || 0));
        setTexto('contabSaidas', formatarMoeda(dados.total_saidas || 0));
        setTexto('contabSaldo', formatarMoeda(dados.saldo_operacional || 0));
        setTexto('contabOs', String(dados.quantidade_os || 0));
        setTexto('contabTicket', formatarMoeda(dados.ticket_medio || 0));
        setTexto('contabPeriodo', `${formatarDataBR(dados.periodo?.inicio)} até ${formatarDataBR(dados.periodo?.fim)}`);
        renderTabelaPagamentos(dados.pagamentos || []);
    } catch (error) {
        alertErro(error.message);
    }
}

async function baixarExcelContabilidade() {
    const mes = valorMesContabil();
    const query = mes ? `?mes=${encodeURIComponent(mes)}` : '';
    try {
        const response = await fetch(`/api/relatorios/producao-profissionais/exportar-excel${query}`);
        if (!response.ok) {
            const erro = await response.json().catch(() => ({}));
            throw new Error(erro.erro || 'Falha ao exportar Excel.');
        }
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        const mesArq = mes || new Date().toISOString().slice(0, 7);
        a.href = url;
        a.download = `contabilidade_geral_${mesArq.replace('-', '_')}.xlsx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        alertSucesso('Excel baixado com sucesso.');
    } catch (error) {
        alertErro(error.message);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const hoje = new Date().toISOString().split('T')[0];
    const mesAtual = hoje.slice(0, 7);
    const dataFim = document.getElementById('dataFim');
    const dataInicio = document.getElementById('dataInicio');
    const mesContabil = document.getElementById('mesContabil');
    const opDataInicio = document.getElementById('opDataInicio');
    const opDataFim = document.getElementById('opDataFim');
    if (dataFim) dataFim.value = hoje;
    if (dataInicio) dataInicio.value = hoje;
    if (mesContabil) mesContabil.value = mesAtual;
    if (opDataInicio) opDataInicio.value = hoje;
    if (opDataFim) opDataFim.value = hoje;

    carregarSugestoesProfissionais('');
    carregarContabilidadeGeral();
    carregarRelatorioOperacional();
});

window.buscarResumoProfissional = buscarResumoProfissional;
window.baixarRelatorioSelecionado = baixarRelatorioSelecionado;
window.carregarContabilidadeGeral = carregarContabilidadeGeral;
window.baixarExcelContabilidade = baixarExcelContabilidade;
window.carregarRelatorioOperacional = carregarRelatorioOperacional;
window.baixarExcelOperacional = baixarExcelOperacional;

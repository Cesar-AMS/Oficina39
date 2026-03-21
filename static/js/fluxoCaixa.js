const PERIODO_CAIXA = 'dia';
const paramsCaixa = new URLSearchParams(window.location.search);
let ordemPendenteParaAbrir = paramsCaixa.get('ordem_id');
const origemFluxoCaixa = (paramsCaixa.get('origem') || '').trim();
let ordemPdv = null;
let formasPagamentoPdv = [];
let ultimoResumoOperacaoPdv = null;
let whatsappOrcamentoConfiguradoPdv = '';
let movimentacoesCaixaDia = [];
let filtroMovimentacaoCaixa = 'todas';

function alternarAbaFluxo(nomeAba) {
    document.querySelectorAll('.fluxo-tab').forEach((aba) => {
        aba.classList.toggle('active', aba.dataset.tab === nomeAba);
    });
    document.querySelectorAll('.fluxo-tab-panel').forEach((painel) => {
        painel.classList.toggle('active', painel.id === `fluxoTab${nomeAba.charAt(0).toUpperCase()}${nomeAba.slice(1)}`);
    });
}

function alertErro(mensagem) {
    if (window.ui) return window.ui.error(mensagem);
    alert(`Erro: ${mensagem}`);
}

function alertSucesso(mensagem) {
    if (window.ui) return window.ui.success(mensagem);
    alert(`Sucesso: ${mensagem}`);
}

function obterUrlRetornoFluxo() {
    if (origemFluxoCaixa === 'nova_os') return '/nova-os';
    if (origemFluxoCaixa === 'consultar_os') return '/consultarOS.html';
    if (origemFluxoCaixa === 'debitos') return '/debitos.html';
    return '/fluxo_caixa.html';
}

function formatarValor(valor) {
    return 'R$ ' + (Number(valor || 0)).toFixed(2).replace('.', ',');
}

function normalizarWhatsapp(valor) {
    return String(valor || '').replace(/\D/g, '');
}

function setTexto(id, valor) {
    const el = document.getElementById(id);
    if (el) el.textContent = valor;
}

function setValor(id, valor) {
    const el = document.getElementById(id);
    if (el) el.value = valor ?? '';
}

function escaparHtml(texto) {
    return String(texto ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

async function carregarWhatsappPdv() {
    try {
        const response = await fetch('/api/config/contador');
        const dados = await response.json().catch(() => ({}));
        if (!response.ok) return;
        const numero = normalizarWhatsapp(dados?.whatsapp_orcamento || '');
        if (numero) {
            whatsappOrcamentoConfiguradoPdv = numero;
        }
    } catch {
        // Sem bloqueio do fluxo se a configuração não carregar.
    }
}

function montarMensagemRecebimentoPdv(ordem, totaisOperacao) {
    const cliente = ordem?.cliente || {};
    const valorBruto = Number(ordem?.total_geral || 0);
    const descontoValor = Number(totaisOperacao?.descontoValor || 0);
    const valorFinal = Number(totaisOperacao?.totalFinal || 0);
    const pagoAgora = Number(totaisOperacao?.valorRecebido || 0);
    const saldoDebito = Number(ordem?.saldo_pendente || 0);
    const situacao = ordem?.status_financeiro || situacaoAposOperacao(saldoDebito);
    const vencimento = ordem?.debito_vencimento || '';
    const formas = formasPagamentoPdv.length
        ? formasPagamentoPdv.map((item) => `${item.forma_pagamento}: ${formatarValor(item.valor)}`).join(' | ')
        : 'Não informado';

    return [
        `Recebimento da OS #${ordem?.id || '---'}`,
        `Cliente: ${ordem?.cliente_nome || cliente?.nome_cliente || '---'}`,
        `Telefone do cliente: ${cliente?.telefone || 'não informado'}`,
        `Valor bruto: ${formatarValor(valorBruto)}`,
        `Desconto aplicado: ${formatarValor(descontoValor)}`,
        `Valor final da venda: ${formatarValor(valorFinal)}`,
        `Pago nesta operação: ${formatarValor(pagoAgora)}`,
        `Saldo para débito: ${formatarValor(saldoDebito)}`,
        `Situação final: ${situacao}`,
        `Formas usadas: ${formas}`,
        saldoDebito > 0.009 && vencimento ? `Vencimento do débito: ${vencimento}` : ''
    ].filter(Boolean).join('\n\n');
}

function abrirWhatsappRecebimentoPdv(ordem, totaisOperacao) {
    const numeroWhatsapp = normalizarWhatsapp(whatsappOrcamentoConfiguradoPdv);
    if (!numeroWhatsapp) return false;
    const mensagem = encodeURIComponent(montarMensagemRecebimentoPdv(ordem, totaisOperacao));
    const url = `https://wa.me/${numeroWhatsapp}?text=${mensagem}`;
    window.open(url, '_blank', 'noopener');
    return true;
}

function obterDescontoPercentualPdv() {
    const campo = document.getElementById('pdvDescontoPercentual');
    if (!campo) return Number(ordemPdv?.desconto_percentual || 0);
    return Math.min(100, Math.max(0, lerValorMonetario(campo.value || ordemPdv?.desconto_percentual || 0)));
}

function lerValorMonetario(valor) {
    if (valor == null) return 0;
    const texto = String(valor).replace(/\s/g, '');
    const normalizado = texto.includes(',')
        ? texto.replace(/\./g, '').replace(',', '.')
        : texto;
    return arredondarMoeda(parseFloat(normalizado) || 0);
}

function formatarCampoMonetario(id) {
    const campo = document.getElementById(id);
    if (!campo) return;
    const valor = lerValorMonetario(campo.value);
    campo.value = valor ? valor.toFixed(2).replace('.', ',') : '';
}

function arredondarMoeda(valor) {
    return Math.round((Number(valor || 0) + Number.EPSILON) * 100) / 100;
}

function ehFormaReceberDepois(forma) {
    return String(forma || '').trim().toLowerCase() === 'receber depois';
}

function obterTotaisPdv() {
    const totalBruto = Number(ordemPdv?.total_geral || 0);
    const pagoAntes = Number(ordemPdv?.total_pago || 0);
    const descontoPercentual = obterDescontoPercentualPdv();
    const descontoValor = arredondarMoeda(totalBruto * (descontoPercentual / 100));
    const totalFinal = arredondarMoeda(Math.max(0, totalBruto - descontoValor));
    const saldoBase = arredondarMoeda(Math.max(0, totalFinal - pagoAntes));
    const totalFormas = obterTotalFormasPdv();
    const totalReceberDepois = arredondarMoeda(
        formasPagamentoPdv
            .filter((item) => ehFormaReceberDepois(item.forma_pagamento))
            .reduce((acc, item) => acc + lerValorMonetario(item.valor), 0)
    );
    const valorRecebido = arredondarMoeda(Math.max(0, totalFormas - totalReceberDepois));
    const faltaDistribuir = arredondarMoeda(Math.max(0, saldoBase - totalFormas));
    const saldoApos = arredondarMoeda(Math.max(0, totalReceberDepois + faltaDistribuir));
    return {
        totalBruto,
        pagoAntes,
        descontoPercentual,
        descontoValor,
        totalFinal,
        saldoBase,
        valorRecebido,
        totalFormas,
        totalReceberDepois,
        faltaDistribuir,
        saldoApos
    };
}

function limparResumoOperacaoConcluidaPdv() {
    ultimoResumoOperacaoPdv = null;
}

function atualizarModoRecebimentoUiPdv() {
    const debitoWrap = document.getElementById('pdvDebitoFuturoWrap');
    const debitoAviso = document.getElementById('pdvDebitoAviso');
    const totais = obterTotaisPdv();
    const possuiDebito = totais.totalReceberDepois > 0.009;
    if (debitoWrap) debitoWrap.hidden = !possuiDebito;
    if (debitoAviso) debitoAviso.hidden = !(totais.valorRecebido <= 0.009 && possuiDebito);
}

function exibirCardPdv(exibir) {
    const card = document.getElementById('pdvCard');
    if (card) card.style.display = 'block';
    document.querySelectorAll('.pdv-tab').forEach((aba) => {
        if (aba.dataset.tab !== 'dados') {
            aba.disabled = !exibir;
        }
    });
}

function alternarAbaPdv(nomeAba) {
    if (!ordemPdv && nomeAba !== 'dados') {
        alertErro('Carregue uma OS primeiro para liberar as demais etapas do recebimento.');
        nomeAba = 'dados';
    }
    document.querySelectorAll('.pdv-tab').forEach((aba) => {
        aba.classList.toggle('active', aba.dataset.tab === nomeAba);
    });
    document.querySelectorAll('.pdv-tab-panel').forEach((painel) => {
        painel.classList.toggle('active', painel.id === `pdvTab${nomeAba.charAt(0).toUpperCase()}${nomeAba.slice(1)}`);
    });
}

function irParaEtapaPdv(nomeAba) {
    alternarAbaPdv(nomeAba);
}

function irParaProximaEtapaPdv(nomeAba) {
    if (!ordemPdv && nomeAba !== 'dados') {
        alertErro('Carregue uma OS primeiro para continuar.');
        return;
    }
    if (nomeAba === 'resumo') {
        try {
            validarEtapaPagamentoPdv();
        } catch (error) {
            alertErro(error.message);
            return;
        }
    }
    alternarAbaPdv(nomeAba);
}

function validarEtapaPagamentoPdv() {
    validarRegrasPdv();
}

function atualizarResumoTopo(dados) {
    const entradas = Array.isArray(dados?.entradas) ? dados.entradas : [];
    const saidas = Array.isArray(dados?.saidas) ? dados.saidas : [];
    const totalEntradas = entradas.reduce((acc, item) => acc + (Number(item.total || 0)), 0);
    const totalSaidas = saidas.reduce((acc, item) => acc + (Number(item.valor || 0)), 0);
    const saldo = totalEntradas - totalSaidas;
    setTexto('totalEntradas', formatarValor(totalEntradas));
    setTexto('totalSaidas', formatarValor(totalSaidas));
    setTexto('saldo', formatarValor(saldo));
    const elSaldo = document.getElementById('saldo');
    if (elSaldo) {
        elSaldo.className = 'valor ' + (saldo >= 0 ? 'valor-positivo' : 'valor-negativo');
    }
}

function normalizarTextoMovimentacao(valor, fallback = '---') {
    const texto = String(valor ?? '').trim();
    return texto || fallback;
}

function montarMovimentacoesDia(dados) {
    const entradas = (Array.isArray(dados?.entradas) ? dados.entradas : []).map((item) => ({
        horario: item.hora || '--:--',
        tipo: 'Entrada',
        origem: normalizarTextoMovimentacao(item.origem, 'Recebimento'),
        forma: normalizarTextoMovimentacao(item.forma_pagamento),
        valor: Number(item.total || 0),
        observacao: normalizarTextoMovimentacao(item.observacao || item.cliente_nome, 'Sem observação'),
        dataHora: item.data_hora_iso || ''
    }));

    const saidas = (Array.isArray(dados?.saidas) ? dados.saidas : []).map((item) => ({
        horario: item.hora || '--:--',
        tipo: 'Saída',
        origem: normalizarTextoMovimentacao(item.origem, 'Saída manual'),
        forma: normalizarTextoMovimentacao(item.forma_pagamento, '---'),
        valor: Number(item.valor || 0),
        observacao: normalizarTextoMovimentacao(item.observacao || item.descricao, 'Sem observação'),
        dataHora: item.data_hora_iso || ''
    }));

    return [...entradas, ...saidas].sort((a, b) => String(b.dataHora).localeCompare(String(a.dataHora)));
}

function renderMovimentacoesDia() {
    const tbody = document.getElementById('caixaMovimentacoesBody');
    if (!tbody) return;

    const lista = movimentacoesCaixaDia.filter((item) => {
        if (filtroMovimentacaoCaixa === 'entradas') return item.tipo === 'Entrada';
        if (filtroMovimentacaoCaixa === 'saidas') return item.tipo === 'Saída';
        return true;
    });

    if (!lista.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="mensagem-carregando">Nenhuma movimentação no filtro selecionado.</td></tr>';
        return;
    }

    tbody.innerHTML = lista.map((item) => `
        <tr>
            <td>${item.horario}</td>
            <td><span class="caixa-tipo-badge ${item.tipo === 'Entrada' ? 'entrada' : 'saida'}">${item.tipo}</span></td>
            <td>${escaparHtml(item.origem)}</td>
            <td>${escaparHtml(item.forma)}</td>
            <td class="${item.tipo === 'Entrada' ? 'valor-positivo' : 'valor-negativo'}">${formatarValor(item.valor)}</td>
            <td>${escaparHtml(item.observacao)}</td>
        </tr>
    `).join('');
}

function aplicarFiltroMovimentacao(filtro) {
    filtroMovimentacaoCaixa = filtro;
    document.querySelectorAll('.caixa-filtro-btn').forEach((btn) => {
        btn.classList.toggle('active', btn.dataset.filtro === filtro);
    });
    renderMovimentacoesDia();
}

function atualizarEstadoDebitoPdv() {
    const vencimento = document.getElementById('pdvDebitoVencimento');
    const observacao = document.getElementById('pdvDebitoObservacao');
    const totais = obterTotaisPdv();
    const habilitado = totais.saldoApos > 0.009;
    if (vencimento) vencimento.disabled = !habilitado;
    if (observacao) observacao.disabled = !habilitado;
}

async function carregarCaixaDia() {
    try {
        const response = await fetch(`/api/fluxo/periodo?periodo=${PERIODO_CAIXA}`);
        if (!response.ok) throw new Error(`Erro HTTP ${response.status}`);
        const dados = await response.json();
        atualizarResumoTopo(dados);
        movimentacoesCaixaDia = montarMovimentacoesDia(dados);
        renderMovimentacoesDia();

        if (ordemPendenteParaAbrir) {
            alternarAbaFluxo('os');
            await carregarOrdemNoPdv(ordemPendenteParaAbrir);
            ordemPendenteParaAbrir = null;
        }
    } catch (error) {
        alertErro(`Falha ao carregar dados: ${error.message}`);
    }
}

function atualizarDadosOsPdv() {
    if (!ordemPdv) {
        setValor('pdvOsNumeroField', '');
        setValor('pdvClienteNomeField', '');
        setValor('pdvTelefoneField', '');
        setValor('pdvTotalOrdemField', formatarValor(0));
        setValor('pdvTotalPagoField', formatarValor(0));
        setValor('pdvStatusFinanceiroField', '');
        setValor('pdvDescontoPercentual', '');
        setValor('pdvTotalFinalVendaField', formatarValor(0));
        setValor('pdvSaldoRestanteField', formatarValor(0));
        setValor('pdvResumoValorBruto', formatarValor(0));
        setValor('pdvResumoDescontoAplicado', formatarValor(0));
        setValor('pdvResumoValorFinal', formatarValor(0));
        setValor('pdvResumoPagoOperacao', formatarValor(0));
        setValor('pdvResumoSaldoDebito', formatarValor(0));
        setValor('pdvResumoVencimento', '');
        setValor('pdvResumoSituacao', '');
        setValor('pdvResumoDebitoObservacao', '');
        setTexto('pdvResumoTopoTotalFinal', formatarValor(0));
        setTexto('pdvResumoTopoPagoAgora', formatarValor(0));
        setTexto('pdvResumoTopoSaldoApos', formatarValor(0));
        setTexto('pdvResumoFormasUsadas', 'Nenhuma forma informada.');
        atualizarModoRecebimentoUiPdv();
        return;
    }

    setValor('pdvOsNumeroField', `#${ordemPdv.id}`);
    setValor('pdvClienteNomeField', ordemPdv.cliente_nome || ordemPdv.cliente?.nome_cliente || '');
    setValor('pdvTelefoneField', ordemPdv.cliente?.telefone || '');
    setValor('pdvTotalOrdemField', formatarValor(ordemPdv.total_geral || 0));
    setValor('pdvTotalPagoField', formatarValor(ordemPdv.total_pago || 0));
    setValor('pdvStatusFinanceiroField', ordemPdv.status_financeiro || '');
    setValor('pdvDescontoPercentual', Number(ordemPdv.desconto_percentual || 0) ? Number(ordemPdv.desconto_percentual || 0).toFixed(2).replace('.', ',') : '');
    atualizarModoRecebimentoUiPdv();
    atualizarResumoOperacaoPdv();
}

function obterTotalFormasPdv() {
    return formasPagamentoPdv.reduce((acc, item) => acc + lerValorMonetario(item.valor), 0);
}

function situacaoAposOperacao(saldoApos) {
    if (saldoApos <= 0.009) return 'Quitado';
    const totais = obterTotaisPdv();
    if (totais.valorRecebido > 0) return 'Parcial';
    return 'Pendente';
}

function atualizarResumoOperacaoPdv() {
    const totais = obterTotaisPdv();
    const possuiDebitoResumo = totais.totalReceberDepois > 0.009;
    const resumoDebitoWrap = document.getElementById('pdvResumoDebitoWrap');
    if (resumoDebitoWrap) resumoDebitoWrap.hidden = !possuiDebitoResumo;

    setValor('pdvTotalFinalVendaField', formatarValor(totais.totalFinal));
    setValor('pdvSaldoRestanteField', formatarValor(totais.saldoApos));
    setValor('pdvResumoValorBruto', formatarValor(totais.totalBruto));
    setValor('pdvResumoDescontoAplicado', formatarValor(totais.descontoValor));
    setValor('pdvResumoValorFinal', formatarValor(totais.totalFinal));
    setValor('pdvResumoPagoOperacao', formatarValor(totais.valorRecebido));
    setValor('pdvResumoSituacao', situacaoAposOperacao(totais.saldoApos));
    setValor('pdvDebitoValorGerado', formatarValor(totais.totalReceberDepois));
    setTexto('pdvTotalDistribuido', formatarValor(totais.totalFormas));
    setTexto('pdvTotalRecebidoAgora', formatarValor(totais.valorRecebido));
    setTexto('pdvTotalReceberDepois', formatarValor(totais.totalReceberDepois));
    setTexto('pdvFaltaDistribuir', formatarValor(totais.faltaDistribuir));
    const diferencaEl = document.getElementById('pdvFaltaDistribuir');
    if (diferencaEl) {
        diferencaEl.classList.toggle('valor-positivo', totais.faltaDistribuir <= 0.009);
        diferencaEl.classList.toggle('valor-pendente', totais.faltaDistribuir > 0.009);
    }
    setTexto('pdvResumoTopoTotalFinal', formatarValor(totais.totalFinal));
    setTexto('pdvResumoTopoPagoAgora', formatarValor(totais.valorRecebido));
    setTexto('pdvResumoTopoSaldoApos', formatarValor(totais.totalReceberDepois));
    setTexto('pdvResumoFormasUsadas', resumoFormasPagamentoPdv());
    setValor('pdvResumoVencimento', possuiDebitoResumo ? (document.getElementById('pdvDebitoVencimento')?.value || '').trim() : '');
    setValor('pdvResumoDebitoObservacao', possuiDebitoResumo ? (document.getElementById('pdvDebitoObservacao')?.value || '').trim() : '');
    atualizarEstadoDebitoPdv();
    atualizarModoRecebimentoUiPdv();
}

function aplicarResumoOperacaoConcluidaPdv() {
    if (!ultimoResumoOperacaoPdv) return;
    const possuiDebitoResumo = Number(ultimoResumoOperacaoPdv.saldoApos || 0) > 0.009;
    const resumoDebitoWrap = document.getElementById('pdvResumoDebitoWrap');
    if (resumoDebitoWrap) resumoDebitoWrap.hidden = !possuiDebitoResumo;

    setValor('pdvTotalFinalVendaField', formatarValor(ultimoResumoOperacaoPdv.totalFinal));
    setValor('pdvSaldoRestanteField', formatarValor(ultimoResumoOperacaoPdv.saldoApos));
    setValor('pdvResumoValorBruto', formatarValor(ultimoResumoOperacaoPdv.totalBruto));
    setValor('pdvResumoDescontoAplicado', formatarValor(ultimoResumoOperacaoPdv.descontoValor));
    setValor('pdvResumoValorFinal', formatarValor(ultimoResumoOperacaoPdv.totalFinal));
    setValor('pdvResumoPagoOperacao', formatarValor(ultimoResumoOperacaoPdv.pagoAgora));
    setValor('pdvResumoSituacao', ultimoResumoOperacaoPdv.situacao);
    setValor('pdvDebitoValorGerado', formatarValor(ultimoResumoOperacaoPdv.saldoApos));
    setTexto('pdvTotalDistribuido', formatarValor(obterTotalFormasPdv()));
    setTexto('pdvTotalRecebidoAgora', formatarValor(ultimoResumoOperacaoPdv.pagoAgora));
    setTexto('pdvTotalReceberDepois', formatarValor(ultimoResumoOperacaoPdv.saldoApos));
    setTexto('pdvFaltaDistribuir', formatarValor(0));
    const diferencaEl = document.getElementById('pdvFaltaDistribuir');
    if (diferencaEl) {
        diferencaEl.classList.add('valor-positivo');
        diferencaEl.classList.remove('valor-pendente');
    }
    setTexto('pdvResumoTopoTotalFinal', formatarValor(ultimoResumoOperacaoPdv.totalFinal));
    setTexto('pdvResumoTopoPagoAgora', formatarValor(ultimoResumoOperacaoPdv.pagoAgora));
    setTexto('pdvResumoTopoSaldoApos', formatarValor(ultimoResumoOperacaoPdv.saldoApos));
    setTexto('pdvResumoFormasUsadas', ultimoResumoOperacaoPdv.formas || 'Nenhuma forma informada.');
    setValor('pdvResumoVencimento', possuiDebitoResumo ? (ultimoResumoOperacaoPdv.vencimento || '') : '');
    setValor('pdvResumoDebitoObservacao', possuiDebitoResumo ? (ultimoResumoOperacaoPdv.debitoObservacao || '') : '');
    atualizarModoRecebimentoUiPdv();
}

function resumoFormasPagamentoPdv() {
    if (!formasPagamentoPdv.length) return 'Nenhuma forma informada.';
    return formasPagamentoPdv
        .map((item) => `${item.forma_pagamento} - ${formatarValor(item.valor)}`)
        .join(' | ');
}

function renderFormasPagamentoPdv() {
    const lista = document.getElementById('pdvFormasResumoLista');
    if (!lista) {
        atualizarResumoOperacaoPdv();
        return;
    }

    if (!formasPagamentoPdv.length) {
        lista.innerHTML = '<div class="pdv-forma-vazia">Nenhuma forma adicionada ainda.</div>';
    } else {
        lista.innerHTML = formasPagamentoPdv.map((item, index) => `
            <div class="pdv-forma-item">
                <div class="pdv-forma-col pdv-forma-col-forma">
                    <strong>${item.forma_pagamento}</strong>
                </div>
                <div class="pdv-forma-col pdv-forma-col-valor">
                    <span>${formatarValor(item.valor)}</span>
                </div>
                <div class="pdv-forma-col pdv-forma-col-obs">
                    <small class="pdv-forma-observacao">${item.observacao || 'Sem observação'}</small>
                </div>
                <div class="pdv-forma-col pdv-forma-col-acao">
                    <button type="button" class="btn btn-cancelar btn-compact pdv-forma-btn-excluir" onclick="removerFormaPagamentoPdv(${index})">Excluir</button>
                </div>
            </div>
        `).join('');
    }

    atualizarResumoOperacaoPdv();
}

async function carregarOrdemNoPdv(ordemId) {
    try {
        const response = await fetch(`/api/ordens/${ordemId}`);
        const dados = await response.json();
        if (!response.ok) throw new Error(dados.erro || 'Erro ao carregar OS.');

        ordemPdv = dados;
        limparResumoOperacaoConcluidaPdv();
        formasPagamentoPdv = [];
        exibirCardPdv(true);
        atualizarDadosOsPdv();
        cancelarRecebimentoPdv();
        alternarAbaFluxo('os');
        alternarAbaPdv('dados');
        document.getElementById('pdvCard').scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (error) {
        alertErro(error.message);
    }
}

function adicionarFormaPagamentoPdv() {
    if (!ordemPdv) {
        alertErro('Carregue uma OS antes de adicionar formas de pagamento.');
        return;
    }
    limparResumoOperacaoConcluidaPdv();

    const forma = (document.getElementById('pdvFormaPagamento')?.value || '').trim();
    let valor = lerValorMonetario(document.getElementById('pdvValorForma')?.value);
    const observacao = (document.getElementById('pdvObservacaoForma')?.value || '').trim();
    const totais = obterTotaisPdv();
    const restante = arredondarMoeda(Math.max(0, totais.saldoBase - totais.totalFormas));

    if (valor <= 0 && restante > 0) {
        valor = restante;
    }

    if (!forma) {
        alertErro('Selecione a forma de pagamento.');
        return;
    }
    if (valor <= 0) {
        alertErro('Informe um valor válido para a forma de pagamento.');
        return;
    }

    formasPagamentoPdv.push({
        forma_pagamento: forma,
        valor,
        observacao
    });

    setValor('pdvFormaPagamento', '');
    setValor('pdvValorForma', '');
    setValor('pdvObservacaoForma', '');
    renderFormasPagamentoPdv();
}

function removerFormaPagamentoPdv(index) {
    limparResumoOperacaoConcluidaPdv();
    formasPagamentoPdv.splice(index, 1);
    renderFormasPagamentoPdv();
}

function cancelarRecebimentoPdv(opcoes = {}) {
    formasPagamentoPdv = [];
    setValor('pdvFormaPagamento', '');
    setValor('pdvValorForma', '');
    setValor('pdvObservacaoForma', '');
    setValor('pdvDebitoObservacao', ordemPdv?.debito_observacao || '');
    const vencimento = document.getElementById('pdvDebitoVencimento');
    if (vencimento) vencimento.value = ordemPdv?.debito_vencimento || '';
    setValor('pdvDescontoPercentual', Number(ordemPdv?.desconto_percentual || 0) ? Number(ordemPdv.desconto_percentual || 0).toFixed(2).replace('.', ',') : '');
    atualizarModoRecebimentoUiPdv();
    if (!opcoes.preservarResumo) {
        limparResumoOperacaoConcluidaPdv();
    }
    renderFormasPagamentoPdv();
}

function limparPdv() {
    ordemPdv = null;
    formasPagamentoPdv = [];
    limparResumoOperacaoConcluidaPdv();
    cancelarRecebimentoPdv();
    exibirCardPdv(false);
    atualizarDadosOsPdv();
    alternarAbaFluxo('caixa');
    alternarAbaPdv('dados');
}

function validarRegrasPdv() {
    if (!ordemPdv) {
        throw new Error('Carregue uma OS no PDV.');
    }

    const totais = obterTotaisPdv();
    const debitoVencimento = (document.getElementById('pdvDebitoVencimento')?.value || '').trim();

    if (!formasPagamentoPdv.length) throw new Error('Adicione pelo menos uma forma de pagamento.');
    if (totais.totalFormas - totais.saldoBase > 0.009) throw new Error('A soma das formas não pode ultrapassar o valor total da venda.');
    if (Math.abs(totais.faltaDistribuir) > 0.009) throw new Error('Distribua todo o valor da venda antes de avançar.');
    if (totais.totalReceberDepois > 0.009 && !debitoVencimento) throw new Error('Informe a data de vencimento do débito.');
}

async function salvarFaturamentoPdv() {
    try {
        validarRegrasPdv();

        const totaisOperacao = obterTotaisPdv();
        const payload = {
            pagamentos: formasPagamentoPdv.map((item) => ({
                forma_pagamento: item.forma_pagamento,
                valor: item.valor,
                observacao: item.observacao
            })),
            desconto_percentual: obterDescontoPercentualPdv(),
            debito_vencimento: (document.getElementById('pdvDebitoVencimento')?.value || '').trim(),
            debito_observacao: (document.getElementById('pdvDebitoObservacao')?.value || '').trim()
        };

        const response = await fetch(`/api/ordens/${ordemPdv.id}/faturamento`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const dados = await response.json();
        if (!response.ok) throw new Error(dados.erro || 'Erro ao faturar OS.');

        alertSucesso(Number(dados.saldo_pendente || 0) > 0.009
            ? 'Recebimento parcial registrado e débito atualizado.'
            : 'Recebimento concluído e OS quitada.');

        abrirWhatsappRecebimentoPdv(dados, totaisOperacao);
        await carregarCaixaDia();
        window.location.assign(obterUrlRetornoFluxo());
    } catch (error) {
        alertErro(error.message);
    }
}

function abrirModalSaida() {
    const modal = document.getElementById('modalSaida');
    if (!modal) return;
    modal.style.display = 'flex';
    setValor('saidaData', new Date().toISOString().split('T')[0]);
    setValor('saidaDescricao', '');
    setValor('saidaValor', '');
    setValor('saidaCategoria', '');
}

function fecharModalSaida() {
    const modal = document.getElementById('modalSaida');
    if (modal) modal.style.display = 'none';
}

let expressaoCalculadora = '';

function abrirModalCalculadora() {
    const modal = document.getElementById('modalCalculadora');
    if (!modal) return;
    modal.style.display = 'flex';
    if (!expressaoCalculadora) {
        atualizarDisplayCalculadora('0');
    }
}

function fecharModalCalculadora() {
    const modal = document.getElementById('modalCalculadora');
    if (modal) modal.style.display = 'none';
}

function atualizarDisplayCalculadora(valor) {
    const display = document.getElementById('calcDisplay');
    if (display) display.value = valor;
}

function obterUltimoNumeroCalculadora() {
    const partes = expressaoCalculadora.split(/[\+\-\*\/%]/);
    return partes[partes.length - 1] || '';
}

function adicionarCalculadora(valor) {
    if (valor === '.') {
        const ultimoNumero = obterUltimoNumeroCalculadora();
        if (ultimoNumero.includes('.')) return;
        if (!ultimoNumero) {
            expressaoCalculadora += '0.';
            atualizarDisplayCalculadora(expressaoCalculadora);
            return;
        }
    }

    expressaoCalculadora = expressaoCalculadora === '0' && valor !== '.' ? valor : (expressaoCalculadora + valor);
    atualizarDisplayCalculadora(expressaoCalculadora || '0');
}

function limparCalculadora() {
    expressaoCalculadora = '';
    atualizarDisplayCalculadora('0');
}

function apagarUltimoCalculadora() {
    if (!expressaoCalculadora) return;
    expressaoCalculadora = expressaoCalculadora.slice(0, -1);
    atualizarDisplayCalculadora(expressaoCalculadora || '0');
}

function calcularExpressao() {
    if (!expressaoCalculadora) return;
    try {
        const permitido = /^[0-9+\-*/%.() ]+$/;
        if (!permitido.test(expressaoCalculadora)) throw new Error('Expressao invalida');
        const resultado = Function(`"use strict"; return (${expressaoCalculadora});`)();
        if (!Number.isFinite(resultado)) throw new Error('Resultado invalido');
        expressaoCalculadora = Number(resultado.toFixed(2)).toString();
        atualizarDisplayCalculadora(expressaoCalculadora);
    } catch {
        expressaoCalculadora = '';
        atualizarDisplayCalculadora('Erro');
    }
}

async function salvarSaida() {
    const descricao = (document.getElementById('saidaDescricao')?.value || '').trim();
    const valor = (document.getElementById('saidaValor')?.value || '').replace(',', '.');
    const data = document.getElementById('saidaData')?.value || new Date().toISOString().split('T')[0];
    const categoria = document.getElementById('saidaCategoria')?.value || 'Outros';

    if (!descricao) {
        alertErro('Descrição é obrigatória.');
        return;
    }
    const valorNumerico = parseFloat(valor);
    if (!Number.isFinite(valorNumerico) || valorNumerico <= 0) {
        alertErro('Valor inválido.');
        return;
    }

    try {
        const response = await fetch('/api/fluxo/saidas', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
            body: JSON.stringify({ descricao, valor: valorNumerico, data, categoria })
        });
        const dados = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(dados.erro || 'Erro ao registrar saída.');
        alertSucesso('Saída registrada com sucesso.');
        fecharModalSaida();
        carregarCaixaDia();
    } catch (error) {
        alertErro(error.message);
    }
}

async function excluirSaida(id) {
    const confirmado = window.ui?.confirmAsync
        ? await window.ui.confirmAsync('Confirma excluir esta saída?')
        : (window.ui ? window.ui.confirm('Confirma excluir esta saída?') : confirm('Confirma excluir esta saída?'));
    if (!confirmado) return;

    try {
        const response = await fetch(`/api/fluxo/saidas/${id}`, { method: 'DELETE' });
        const dados = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(dados.erro || 'Erro ao excluir saída.');
        alertSucesso('Saída excluída.');
        carregarCaixaDia();
    } catch (error) {
        alertErro(error.message);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    exibirCardPdv(false);
    alternarAbaFluxo('os');
    alternarAbaPdv('dados');
    atualizarModoRecebimentoUiPdv();
    carregarWhatsappPdv();
    carregarCaixaDia();
    document.getElementById('pdvValorForma')?.addEventListener('blur', () => formatarCampoMonetario('pdvValorForma'));
    document.getElementById('pdvValorForma')?.addEventListener('wheel', (e) => {
        e.preventDefault();
        e.target.blur();
    }, { passive: false });
    document.getElementById('pdvDescontoPercentual')?.addEventListener('input', atualizarResumoOperacaoPdv);
    document.getElementById('pdvDescontoPercentual')?.addEventListener('change', atualizarResumoOperacaoPdv);
    document.getElementById('pdvDescontoPercentual')?.addEventListener('blur', () => {
        formatarCampoMonetario('pdvDescontoPercentual');
        atualizarResumoOperacaoPdv();
    });
    document.getElementById('pdvDescontoPercentual')?.addEventListener('wheel', (e) => {
        e.preventDefault();
        e.target.blur();
    }, { passive: false });
    document.getElementById('pdvFormaPagamento')?.addEventListener('change', () => {
        const campoValor = document.getElementById('pdvValorForma');
        if (!campoValor) return;
        const totais = obterTotaisPdv();
        const restante = arredondarMoeda(Math.max(0, totais.saldoBase - totais.totalFormas));
        if (!campoValor.value && restante > 0) {
            campoValor.value = restante.toFixed(2).replace('.', ',');
        }
    });
    document.getElementById('pdvDebitoVencimento')?.addEventListener('change', atualizarResumoOperacaoPdv);
    document.getElementById('pdvDebitoObservacao')?.addEventListener('input', atualizarResumoOperacaoPdv);
});

window.alternarAbaPdv = alternarAbaPdv;
window.alternarAbaFluxo = alternarAbaFluxo;
window.irParaEtapaPdv = irParaEtapaPdv;
window.irParaProximaEtapaPdv = irParaProximaEtapaPdv;
window.adicionarFormaPagamentoPdv = adicionarFormaPagamentoPdv;
window.removerFormaPagamentoPdv = removerFormaPagamentoPdv;
window.salvarFaturamentoPdv = salvarFaturamentoPdv;
window.cancelarRecebimentoPdv = cancelarRecebimentoPdv;
window.limparPdv = limparPdv;
window.abrirModalSaida = abrirModalSaida;
window.fecharModalSaida = fecharModalSaida;
window.salvarSaida = salvarSaida;
window.excluirSaida = excluirSaida;
window.aplicarFiltroMovimentacao = aplicarFiltroMovimentacao;
window.abrirModalCalculadora = abrirModalCalculadora;
window.fecharModalCalculadora = fecharModalCalculadora;
window.adicionarCalculadora = adicionarCalculadora;
window.limparCalculadora = limparCalculadora;
window.apagarUltimoCalculadora = apagarUltimoCalculadora;
window.calcularExpressao = calcularExpressao;

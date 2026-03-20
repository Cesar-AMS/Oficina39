const PERIODO_CAIXA = 'dia';
const paramsCaixa = new URLSearchParams(window.location.search);
let ordemPendenteParaAbrir = paramsCaixa.get('ordem_id');
let ordemPdv = null;
let formasPagamentoPdv = [];
let ordensEncontradasPdv = [];
let buscouOrdensPdv = false;
let ultimoResumoOperacaoPdv = null;
let modoRecebimentoPdv = 'total';

const STATUS_PDV_PRIORITARIOS = new Set(['Concluído', 'Garantia', 'Finalizado']);

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

function formatarValor(valor) {
    return 'R$ ' + (Number(valor || 0)).toFixed(2).replace('.', ',');
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

function obterDescontoPercentualPdv() {
    const campo = document.getElementById('pdvDescontoPercentual');
    return Math.min(100, Math.max(0, lerValorMonetario(campo?.value)));
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

function obterValorRecebidoCampoPdv() {
    const campo = document.getElementById('pdvValorRecebidoAgora');
    return lerValorMonetario(campo?.value);
}

function arredondarMoeda(valor) {
    return Math.round((Number(valor || 0) + Number.EPSILON) * 100) / 100;
}

function ordemElegivelParaPdv(ordem) {
    const saldo = Number(ordem?.saldo_pendente ?? ordem?.total_geral ?? 0);
    const status = String(ordem?.status || '').trim();
    if (saldo > 0.009) return true;
    return STATUS_PDV_PRIORITARIOS.has(status);
}

function ordenarResultadosPdv(ordens) {
    return [...ordens].sort((a, b) => {
        const aElegivel = ordemElegivelParaPdv(a) ? 1 : 0;
        const bElegivel = ordemElegivelParaPdv(b) ? 1 : 0;
        if (aElegivel !== bElegivel) return bElegivel - aElegivel;
        return Number(b.id || 0) - Number(a.id || 0);
    });
}

function obterTotaisPdv() {
    const totalBruto = Number(ordemPdv?.total_geral || 0);
    const pagoAntes = Number(ordemPdv?.total_pago || 0);
    const descontoPercentual = obterDescontoPercentualPdv();
    const descontoValor = arredondarMoeda(totalBruto * (descontoPercentual / 100));
    const totalFinal = arredondarMoeda(Math.max(0, totalBruto - descontoValor));
    const saldoBase = arredondarMoeda(Math.max(0, totalFinal - pagoAntes));
    const valorRecebido = obterValorRecebidoCampoPdv();
    const totalFormas = obterTotalFormasPdv();
    const saldoApos = arredondarMoeda(Math.max(0, saldoBase - valorRecebido));
    return {
        totalBruto,
        pagoAntes,
        descontoPercentual,
        descontoValor,
        totalFinal,
        saldoBase,
        valorRecebido,
        totalFormas,
        saldoApos
    };
}

function limparResumoOperacaoConcluidaPdv() {
    ultimoResumoOperacaoPdv = null;
}

function atualizarModoRecebimentoUiPdv() {
    const ajuda = document.getElementById('pdvModoRecebimentoAjuda');
    const totalBtn = document.getElementById('pdvModoTotalBtn');
    const parcialBtn = document.getElementById('pdvModoParcialBtn');
    const parcialBox = document.getElementById('pdvParcialBox');
    const btnPreencherTotal = document.getElementById('pdvBtnPreencherTotal');

    if (totalBtn) totalBtn.classList.toggle('active', modoRecebimentoPdv === 'total');
    if (parcialBtn) parcialBtn.classList.toggle('active', modoRecebimentoPdv === 'parcial');
    if (parcialBox) parcialBox.hidden = modoRecebimentoPdv !== 'parcial';
    if (btnPreencherTotal) btnPreencherTotal.hidden = modoRecebimentoPdv === 'parcial';

    if (ajuda) {
        ajuda.textContent = modoRecebimentoPdv === 'total'
            ? 'Receba o valor total agora e distribua como quiser nas formas de pagamento.'
            : 'Informe apenas o valor que entrou agora. O restante seguirá automaticamente para Débitos.';
    }
}

function sincronizarModoRecebimentoPdv() {
    if (!ordemPdv) {
        modoRecebimentoPdv = 'total';
        atualizarModoRecebimentoUiPdv();
        return;
    }
    const totais = obterTotaisPdv();
    if (totais.valorRecebido > 0 && totais.valorRecebido + 0.009 < totais.saldoBase) {
        modoRecebimentoPdv = 'parcial';
    } else if (totais.saldoBase <= 0.009 || totais.valorRecebido >= totais.saldoBase - 0.009) {
        modoRecebimentoPdv = 'total';
    }
    atualizarModoRecebimentoUiPdv();
}

function selecionarModoRecebimentoPdv(modo) {
    if (!ordemPdv) {
        alertErro('Carregue uma OS antes de definir o tipo de recebimento.');
        return;
    }

    modoRecebimentoPdv = modo === 'parcial' ? 'parcial' : 'total';
    limparResumoOperacaoConcluidaPdv();

    if (modoRecebimentoPdv === 'total') {
        const totais = obterTotaisPdv();
        setValor('pdvValorRecebidoAgora', totais.saldoBase.toFixed(2));
    } else {
        setValor('pdvValorRecebidoAgora', '');
    }

    atualizarModoRecebimentoUiPdv();
    atualizarResumoOperacaoPdv();
}

function exibirCardPdv(exibir) {
    const card = document.getElementById('pdvCard');
    if (card) card.style.display = 'block';
    document.querySelectorAll('.pdv-tab').forEach((aba) => {
        if (aba.dataset.tab !== 'busca') {
            aba.disabled = !exibir;
        }
    });
}

function renderResultadosBuscaPdv() {
    const wrap = document.getElementById('pdvBuscaResultadosWrap');
    const tbody = document.getElementById('corpoBuscaOsPdv');
    if (!wrap || !tbody) return;

    wrap.hidden = !buscouOrdensPdv;
    if (!buscouOrdensPdv) return;

    if (!ordensEncontradasPdv.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center mensagem-carregando">Nenhuma OS elegível para recebimento encontrada para este cliente.</td></tr>';
        return;
    }

    tbody.innerHTML = ordensEncontradasPdv.map((ordem) => `
        <tr>
            <td>#${ordem.id}</td>
            <td>${escaparHtml(ordem.cliente_nome || ordem.cliente?.nome_cliente || '---')}</td>
            <td>${escaparHtml(ordem.cliente?.cpf || '---')}</td>
            <td>${escaparHtml(ordem.status || '---')}</td>
            <td>${formatarValor(ordem.saldo_pendente || ordem.total_geral || 0)}</td>
            <td><button type="button" class="btn btn-salvar btn-compact" onclick="selecionarOrdemBuscaPdv(${ordem.id})">Selecionar</button></td>
        </tr>
    `).join('');
}

function alternarAbaPdv(nomeAba) {
    if (!ordemPdv && nomeAba !== 'busca') {
        alertErro('Carregue uma OS primeiro para liberar as demais etapas do recebimento.');
        nomeAba = 'busca';
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
    if (!ordemPdv && nomeAba !== 'busca') {
        alertErro('Carregue uma OS primeiro para continuar.');
        return;
    }
    alternarAbaPdv(nomeAba);
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

function atualizarEstadoDebitoPdv() {
    const gerarDebito = document.getElementById('pdvGerarDebito');
    const vencimento = document.getElementById('pdvDebitoVencimento');
    const observacao = document.getElementById('pdvDebitoObservacao');
    const totais = obterTotaisPdv();
    const temRestante = totais.saldoApos > 0.009;
    const habilitado = temRestante && !!gerarDebito?.checked;

    if (gerarDebito) {
        if (!temRestante) {
            gerarDebito.checked = false;
            gerarDebito.disabled = true;
        } else {
            gerarDebito.checked = true;
            gerarDebito.disabled = true;
        }
    }
    if (vencimento) vencimento.disabled = !habilitado;
    if (observacao) observacao.disabled = !habilitado;
}

async function carregarCaixaDia() {
    try {
        const response = await fetch(`/api/fluxo/periodo?periodo=${PERIODO_CAIXA}`);
        if (!response.ok) throw new Error(`Erro HTTP ${response.status}`);
        const dados = await response.json();
        atualizarResumoTopo(dados);

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
        setValor('pdvDescontoPercentual', '');
        setValor('pdvDescontoValor', formatarValor(0));
        setValor('pdvTotalFinalField', formatarValor(0));
        setValor('pdvSaldoPendenteField', formatarValor(0));
        setValor('pdvStatusFinanceiroField', '');
        modoRecebimentoPdv = 'total';
        atualizarModoRecebimentoUiPdv();
        return;
    }

    setValor('pdvOsNumeroField', `#${ordemPdv.id}`);
    setValor('pdvClienteNomeField', ordemPdv.cliente_nome || ordemPdv.cliente?.nome_cliente || '');
    setValor('pdvTelefoneField', ordemPdv.cliente?.telefone || '');
    setValor('pdvTotalOrdemField', formatarValor(ordemPdv.total_geral || 0));
    setValor('pdvTotalPagoField', formatarValor(ordemPdv.total_pago || 0));
    setValor('pdvDescontoPercentual', Number(ordemPdv.desconto_percentual || 0).toFixed(2));
    setValor('pdvDescontoValor', formatarValor(ordemPdv.desconto_valor || 0));
    setValor('pdvTotalFinalField', formatarValor(ordemPdv.total_cobrado || ordemPdv.total_geral || 0));
    setValor('pdvSaldoPendenteField', formatarValor(ordemPdv.saldo_pendente || 0));
    setValor('pdvStatusFinanceiroField', ordemPdv.status_financeiro || '');
    modoRecebimentoPdv = 'total';
    atualizarModoRecebimentoUiPdv();
    atualizarResumoOperacaoPdv();
}

function obterTotalFormasPdv() {
    return formasPagamentoPdv.reduce((acc, item) => acc + lerValorMonetario(item.valor), 0);
}

function situacaoAposOperacao(saldoApos) {
    if (saldoApos <= 0.009) return 'Quitado';
    const pagoAgora = obterValorRecebidoCampoPdv();
    if (pagoAgora > 0) return 'Parcial';
    return 'Em aberto';
}

function atualizarResumoOperacaoPdv() {
    const totais = obterTotaisPdv();
    const valorRestante = totais.saldoApos;

    setValor('pdvDescontoValor', formatarValor(totais.descontoValor));
    setValor('pdvTotalFinalField', formatarValor(totais.totalFinal));
    setValor('pdvSaldoPendenteField', formatarValor(totais.saldoBase));
    setValor('pdvTotalFormas', formatarValor(totais.totalFormas));
    setValor('pdvDiferencaFormas', formatarValor(valorRestante));
    setValor('pdvResumoTotalOs', formatarValor(totais.totalBruto));
    setValor('pdvResumoDesconto', formatarValor(totais.descontoValor));
    setValor('pdvResumoTotalFinal', formatarValor(totais.totalFinal));
    setValor('pdvResumoPagoAntes', formatarValor(totais.pagoAntes));
    setValor('pdvResumoPagoAgora', formatarValor(totais.valorRecebido));
    setValor('pdvResumoSaldoApos', formatarValor(totais.saldoApos));
    setValor('pdvResumoSituacao', situacaoAposOperacao(totais.saldoApos));
    setValor('pdvValorRestante', formatarValor(totais.saldoApos));
    setValor('pdvResumoRecebidoInformado', formatarValor(totais.valorRecebido));
    setValor('pdvDebitoValorGerado', formatarValor(totais.saldoApos));
    setTexto('pdvPainelSaldoPendente', formatarValor(totais.saldoBase));
    setTexto('pdvPainelRecebidoAgora', formatarValor(totais.valorRecebido));
    setTexto('pdvPainelDiferenca', formatarValor(valorRestante));
    setTexto('pdvParcialReceberAgora', formatarValor(totais.valorRecebido));
    setTexto('pdvParcialVaiDebitos', formatarValor(valorRestante));
    setTexto('pdvResumoTopoTotalFinal', formatarValor(totais.totalFinal));
    setTexto('pdvResumoTopoPagoAgora', formatarValor(totais.valorRecebido));
    setTexto('pdvResumoTopoSaldoApos', formatarValor(totais.saldoApos));
    sincronizarModoRecebimentoPdv();
    atualizarEstadoDebitoPdv();
}

function aplicarResumoOperacaoConcluidaPdv() {
    if (!ultimoResumoOperacaoPdv) return;

    setValor('pdvResumoTotalOs', formatarValor(ultimoResumoOperacaoPdv.totalBruto));
    setValor('pdvResumoDesconto', formatarValor(ultimoResumoOperacaoPdv.descontoValor));
    setValor('pdvResumoTotalFinal', formatarValor(ultimoResumoOperacaoPdv.totalFinal));
    setValor('pdvResumoPagoAntes', formatarValor(ultimoResumoOperacaoPdv.pagoAntes));
    setValor('pdvResumoPagoAgora', formatarValor(ultimoResumoOperacaoPdv.pagoAgora));
    setValor('pdvResumoSaldoApos', formatarValor(ultimoResumoOperacaoPdv.saldoApos));
    setValor('pdvResumoSituacao', ultimoResumoOperacaoPdv.situacao);
    setValor('pdvValorRestante', formatarValor(ultimoResumoOperacaoPdv.saldoApos));
    setValor('pdvResumoRecebidoInformado', formatarValor(ultimoResumoOperacaoPdv.pagoAgora));
    setValor('pdvDebitoValorGerado', formatarValor(ultimoResumoOperacaoPdv.saldoApos));
    setTexto('pdvResumoTopoTotalFinal', formatarValor(ultimoResumoOperacaoPdv.totalFinal));
    setTexto('pdvResumoTopoPagoAgora', formatarValor(ultimoResumoOperacaoPdv.pagoAgora));
    setTexto('pdvResumoTopoSaldoApos', formatarValor(ultimoResumoOperacaoPdv.saldoApos));
}

function renderFormasPagamentoPdv() {
    const tbody = document.getElementById('corpoPagamentosPdv');
    if (!tbody) {
        atualizarResumoOperacaoPdv();
        return;
    }

    if (!formasPagamentoPdv.length) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center mensagem-carregando">Nenhuma forma adicionada.</td></tr>';
    } else {
        tbody.innerHTML = formasPagamentoPdv.map((item, index) => `
            <tr>
                <td>${item.forma_pagamento}</td>
                <td>${formatarValor(item.valor)}</td>
                <td>${item.observacao || '---'}</td>
                <td><button type="button" class="btn btn-cancelar btn-compact" onclick="removerFormaPagamentoPdv(${index})">Excluir</button></td>
            </tr>
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
        ordensEncontradasPdv = [dados];
        buscouOrdensPdv = true;
        exibirCardPdv(true);
        atualizarDadosOsPdv();
        cancelarRecebimentoPdv();
        renderResultadosBuscaPdv();
        setValor('pdvBuscaCliente', dados.cliente_nome || dados.cliente?.nome_cliente || dados.cliente?.cpf || '');
        alternarAbaFluxo('os');
        alternarAbaPdv('dados');
        document.getElementById('pdvCard').scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (error) {
        alertErro(error.message);
    }
}

async function buscarOrdemPdv() {
    const termo = (document.getElementById('pdvBuscaCliente')?.value || '').trim();
    if (!termo) {
        alertErro('Informe o nome ou CPF do cliente.');
        return;
    }
    try {
        buscouOrdensPdv = true;
        const response = await fetch(`/api/ordens/busca?cliente=${encodeURIComponent(termo)}`);
        const dados = await response.json();
        if (!response.ok) throw new Error(dados.erro || 'Erro ao buscar OS.');

        const ordens = Array.isArray(dados) ? dados : [];
        ordensEncontradasPdv = ordenarResultadosPdv(ordens.filter(ordemElegivelParaPdv));
        renderResultadosBuscaPdv();

        if (!ordensEncontradasPdv.length) {
            ordemPdv = null;
            exibirCardPdv(false);
            atualizarDadosOsPdv();
            return;
        }

        if (ordensEncontradasPdv.length === 1) {
            await carregarOrdemNoPdv(ordensEncontradasPdv[0].id);
        }
    } catch (error) {
        alertErro(error.message);
    }
}

async function selecionarOrdemBuscaPdv(ordemId) {
    await carregarOrdemNoPdv(ordemId);
}

function preencherValorTotalRecebido() {
    if (!ordemPdv) return;
    selecionarModoRecebimentoPdv('total');
}

function limparValorRecebido() {
    limparResumoOperacaoConcluidaPdv();
    setValor('pdvValorRecebidoAgora', '');
    atualizarResumoOperacaoPdv();
}

function adicionarFormaPagamentoPdv() {
    if (!ordemPdv) {
        alertErro('Carregue uma OS antes de adicionar formas de pagamento.');
        return;
    }
    limparResumoOperacaoConcluidaPdv();

    const forma = (document.getElementById('pdvFormaPagamento')?.value || '').trim();
    const valor = lerValorMonetario(document.getElementById('pdvValorForma')?.value);
    const observacao = (document.getElementById('pdvObservacaoForma')?.value || '').trim();

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
    setValor('pdvValorRecebidoAgora', '');
    setValor('pdvFormaPagamento', '');
    setValor('pdvValorForma', '');
    setValor('pdvObservacaoForma', '');
    setValor('pdvDebitoObservacao', ordemPdv?.debito_observacao || '');
    const vencimento = document.getElementById('pdvDebitoVencimento');
    if (vencimento) vencimento.value = '';
    modoRecebimentoPdv = 'total';
    atualizarModoRecebimentoUiPdv();
    if (!opcoes.preservarResumo) {
        limparResumoOperacaoConcluidaPdv();
    }
    renderFormasPagamentoPdv();
}

function limparPdv() {
    ordemPdv = null;
    formasPagamentoPdv = [];
    ordensEncontradasPdv = [];
    buscouOrdensPdv = false;
    limparResumoOperacaoConcluidaPdv();
    setValor('pdvBuscaCliente', '');
    cancelarRecebimentoPdv();
    exibirCardPdv(false);
    atualizarDadosOsPdv();
    renderResultadosBuscaPdv();
    alternarAbaFluxo('caixa');
    alternarAbaPdv('busca');
}

function validarRegrasPdv() {
    if (!ordemPdv) {
        throw new Error('Carregue uma OS no PDV.');
    }

    const valorRecebido = obterValorRecebidoCampoPdv();
    const totais = obterTotaisPdv();
    const gerarDebito = document.getElementById('pdvGerarDebito')?.checked;
    const debitoVencimento = (document.getElementById('pdvDebitoVencimento')?.value || '').trim();

    if (valorRecebido < 0) throw new Error('O valor recebido agora não pode ser negativo.');
    if (totais.valorRecebido - totais.saldoBase > 0.009) throw new Error('O valor recebido agora não pode ser maior que o saldo pendente.');
    if (Math.abs(totais.totalFormas - totais.valorRecebido) > 0.009) throw new Error('A soma das formas de pagamento deve ser igual ao valor recebido agora.');
    if (totais.saldoApos > 0.009 && !gerarDebito) throw new Error('O valor restante precisa gerar débito automaticamente.');
    if (totais.saldoApos > 0.009 && !debitoVencimento) throw new Error('Informe a data de vencimento do débito.');
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

        ordemPdv = dados;
        ultimoResumoOperacaoPdv = {
            totalBruto: totaisOperacao.totalBruto,
            descontoValor: totaisOperacao.descontoValor,
            totalFinal: totaisOperacao.totalFinal,
            pagoAntes: totaisOperacao.pagoAntes,
            pagoAgora: totaisOperacao.valorRecebido,
            saldoApos: Number(dados.saldo_pendente || 0),
            situacao: dados.status_financeiro || situacaoAposOperacao(Number(dados.saldo_pendente || 0))
        };
        cancelarRecebimentoPdv({ preservarResumo: true });
        atualizarDadosOsPdv();
        aplicarResumoOperacaoConcluidaPdv();
        await carregarCaixaDia();
        alternarAbaPdv('resumo');
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
    alternarAbaFluxo(ordemPendenteParaAbrir ? 'os' : 'caixa');
    alternarAbaPdv('busca');
    atualizarModoRecebimentoUiPdv();
    carregarCaixaDia();

    const campoRecebidoAgora = document.getElementById('pdvValorRecebidoAgora');
    ['input', 'change', 'keyup'].forEach((evento) => campoRecebidoAgora?.addEventListener(evento, () => {
        limparResumoOperacaoConcluidaPdv();
        atualizarResumoOperacaoPdv();
    }));
    campoRecebidoAgora?.addEventListener('blur', () => formatarCampoMonetario('pdvValorRecebidoAgora'));
    document.getElementById('pdvDescontoPercentual')?.addEventListener('input', () => {
        limparResumoOperacaoConcluidaPdv();
        atualizarResumoOperacaoPdv();
    });
    document.getElementById('pdvValorForma')?.addEventListener('blur', () => formatarCampoMonetario('pdvValorForma'));
    renderResultadosBuscaPdv();
    document.getElementById('pdvBuscaCliente')?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            buscarOrdemPdv();
        }
    });
    document.getElementById('pdvValorRecebidoAgora')?.addEventListener('wheel', (e) => {
        e.preventDefault();
        e.target.blur();
    }, { passive: false });
    document.getElementById('pdvValorForma')?.addEventListener('wheel', (e) => {
        e.preventDefault();
        e.target.blur();
    }, { passive: false });
    document.getElementById('pdvGerarDebito')?.addEventListener('change', atualizarEstadoDebitoPdv);
});

window.alternarAbaPdv = alternarAbaPdv;
window.alternarAbaFluxo = alternarAbaFluxo;
window.irParaEtapaPdv = irParaEtapaPdv;
window.irParaProximaEtapaPdv = irParaProximaEtapaPdv;
window.buscarOrdemPdv = buscarOrdemPdv;
window.selecionarOrdemBuscaPdv = selecionarOrdemBuscaPdv;
window.preencherValorTotalRecebido = preencherValorTotalRecebido;
window.limparValorRecebido = limparValorRecebido;
window.selecionarModoRecebimentoPdv = selecionarModoRecebimentoPdv;
window.adicionarFormaPagamentoPdv = adicionarFormaPagamentoPdv;
window.removerFormaPagamentoPdv = removerFormaPagamentoPdv;
window.salvarFaturamentoPdv = salvarFaturamentoPdv;
window.cancelarRecebimentoPdv = cancelarRecebimentoPdv;
window.limparPdv = limparPdv;
window.abrirModalSaida = abrirModalSaida;
window.fecharModalSaida = fecharModalSaida;
window.salvarSaida = salvarSaida;
window.excluirSaida = excluirSaida;
window.abrirModalCalculadora = abrirModalCalculadora;
window.fecharModalCalculadora = fecharModalCalculadora;
window.adicionarCalculadora = adicionarCalculadora;
window.limparCalculadora = limparCalculadora;
window.apagarUltimoCalculadora = apagarUltimoCalculadora;
window.calcularExpressao = calcularExpressao;

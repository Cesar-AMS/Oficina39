// ===========================================
// ordemServico.js - VERSÃO PADRONIZADA
// ===========================================

let clienteSelecionado = null;
let contadorServicos = 0;
let contadorPecas = 0;
let sugestoesClientes = [];
let timerBuscaCliente = null;
let profissionaisDisponiveis = [];
let whatsappOrcamentoConfigurado = '5511992092341';

function alertErro(mensagem) {
    if (window.ui) return window.ui.error(mensagem);
    alert(`Erro: ${mensagem}`);
}

function alertSucesso(mensagem) {
    if (window.ui) return window.ui.success(mensagem);
    alert(`Sucesso: ${mensagem}`);
}

// ===========================================
// FUNÇÕES AUXILIARES
// ===========================================

function formatarValor(valor) {
    return 'R$ ' + (valor || 0).toFixed(2).replace('.', ',');
}

function formatarStatusExibicao(status) {
    return status === 'Concluído' ? 'Finalizado' : (status || '---');
}

function calcularValorVendaPeca(valorCusto, percentualLucro) {
    const custo = parseFloat(valorCusto) || 0;
    const lucro = parseFloat(percentualLucro) || 0;
    return custo * (1 + (lucro / 100));
}

function normalizarWhatsapp(valor) {
    return String(valor || '').replace(/\D/g, '');
}

function preencherDadosCliente(encontrado) {
    if (!encontrado) return;
    clienteSelecionado = encontrado;

    document.getElementById("nome_cliente").value = encontrado.nome_cliente || '';
    document.getElementById("cpf").value = encontrado.cpf || '';
    document.getElementById("endereco").value = encontrado.endereco || '';
    document.getElementById("cidade").value = encontrado.cidade || '';
    document.getElementById("estado").value = encontrado.estado || '';
    document.getElementById("cep").value = encontrado.cep || '';
    document.getElementById("telefone").value = encontrado.telefone || '';
    document.getElementById("email").value = encontrado.email || '';

    document.getElementById("placa").value = encontrado.placa || '';
    document.getElementById("fabricante").value = encontrado.fabricante || '';
    document.getElementById("modelo").value = encontrado.modelo || '';
    document.getElementById("ano").value = encontrado.ano || '';
    document.getElementById("motor").value = encontrado.motor || '';
    document.getElementById("combustivel").value = encontrado.combustivel || '';
    document.getElementById("cor").value = encontrado.cor || '';
    document.getElementById("tanque").value = encontrado.tanque || '';
    document.getElementById("km").value = encontrado.km || '';
    document.getElementById("direcao").value = encontrado.direcao || '';
    document.getElementById("ar").value = encontrado.ar || '';

    const inputBusca = document.getElementById("buscaCliente");
    if (inputBusca) inputBusca.style.borderColor = "#2c7a4d";
}

function esconderSugestoesCliente() {
    const box = document.getElementById('sugestoesCliente');
    if (!box) return;
    box.style.display = 'none';
    box.innerHTML = '';
}

function renderSugestoesCliente(lista) {
    const box = document.getElementById('sugestoesCliente');
    if (!box) return;

    if (!lista.length) {
        esconderSugestoesCliente();
        janelaExistente?.close();
        return;
    }

    box.innerHTML = lista.map((c, idx) => `
        <div class="sugestao-item" data-idx="${idx}">
            <div>${c.nome_cliente || '---'}</div>
            <div class="sugestao-cpf">${c.cpf || 'CPF não informado'}</div>
        </div>
    `).join('');
    box.style.display = 'block';

    box.querySelectorAll('.sugestao-item').forEach((item) => {
        item.addEventListener('click', () => {
            const idx = Number(item.getAttribute('data-idx'));
            const cliente = sugestoesClientes[idx];
            if (!cliente) return;
            const buscaInput = document.getElementById('buscaCliente');
            if (buscaInput) buscaInput.value = cliente.nome_cliente || cliente.cpf || '';
            preencherDadosCliente(cliente);
            esconderSugestoesCliente();
        });
    });
}

async function buscarSugestoesCliente(termo) {
    if (!termo || termo.length < 2) {
        sugestoesClientes = [];
        esconderSugestoesCliente();
        return;
    }

    try {
        const response = await fetch(`/api/clientes/busca?termo=${encodeURIComponent(termo)}`);
        const resultados = await response.json();
        sugestoesClientes = Array.isArray(resultados) ? resultados : [];
        renderSugestoesCliente(sugestoesClientes);
    } catch (error) {
        console.error(error);
        sugestoesClientes = [];
        esconderSugestoesCliente();
    }
}

function preencherSelectProfissionais(lista) {
    const select = document.getElementById('profissional_responsavel');
    if (!select) return;

    const opcoes = ['<option value="">Selecione um profissional cadastrado</option>'];
    lista.forEach((p) => {
        const nome = (p?.nome || '').trim();
        if (!nome) return;
        opcoes.push(`<option value="${nome}">${nome}</option>`);
    });
    select.innerHTML = opcoes.join('');
}

async function carregarProfissionais() {
    try {
        const response = await fetch('/api/profissionais/?ativos=1');
        const dados = await response.json();
        profissionaisDisponiveis = Array.isArray(dados) ? dados : [];
        preencherSelectProfissionais(profissionaisDisponiveis);
    } catch (error) {
        profissionaisDisponiveis = [];
        preencherSelectProfissionais([]);
        console.error('Erro ao carregar profissionais:', error);
    }
}

async function carregarWhatsappOrcamento() {
    try {
        const config = await fetch('/api/config/contador').then((r) => r.json());
        const numero = normalizarWhatsapp(config?.whatsapp_orcamento || '');
        if (numero) {
            whatsappOrcamentoConfigurado = numero;
        }
    } catch (error) {
        console.error('Erro ao carregar WhatsApp do orçamento:', error);
    }
}

// ===========================================
// FUNÇÃO DE CÁLCULO (SERÁ CHAMADA DE VÁRIAS FORMAS)
// ===========================================

window.calcularTotais = function() {
    // Calcular serviços
    let totalServicos = 0;
    document.querySelectorAll('#corpo-servicos .valor-servico').forEach(input => {
        let valor = parseFloat(input.value);
        if (!isNaN(valor) && valor > 0) {
            totalServicos += valor;
        }
    });
    
    // Calcular peças
    let totalPecas = 0;
    document.querySelectorAll('#corpo-pecas .total-peca').forEach(span => {
        let valorTexto = span.textContent.replace('R$ ', '').replace(',', '.');
        let valor = parseFloat(valorTexto);
        if (!isNaN(valor) && valor > 0) {
            totalPecas += valor;
        }
    });
    
    // Atualizar DOM
    const totalServicosEl = document.getElementById('total-servicos');
    const totalPecasEl = document.getElementById('total-pecas');
    const totalGeralEl = document.getElementById('total-geral');
    
    if (totalServicosEl) totalServicosEl.textContent = formatarValor(totalServicos);
    if (totalPecasEl) totalPecasEl.textContent = formatarValor(totalPecas);
    if (totalGeralEl) totalGeralEl.textContent = formatarValor(totalServicos + totalPecas);
};

// ===========================================
// FUNÇÃO PARA ATUALIZAR TOTAL DE UMA PEÇA
// ===========================================

window.calcularTotalPeca = function(elemento) {
    const linha = elemento.closest('tr');
    const qtd = parseFloat(linha.querySelector('.qtd-peca').value) || 0;
    const valorCusto = parseFloat(linha.querySelector('.valor-custo-peca').value) || 0;
    const percentualLucro = parseFloat(linha.querySelector('.lucro-peca').value) || 0;
    const valorVenda = calcularValorVendaPeca(valorCusto, percentualLucro);
    const total = qtd * valorVenda;

    const valorUnitarioCampo = linha.querySelector('.valor-unitario-peca');
    if (valorUnitarioCampo) {
        valorUnitarioCampo.value = valorVenda.toFixed(2);
    }
    linha.querySelector('.total-peca').textContent = formatarValor(total);
    window.calcularTotais();
};

// ===========================================
// FUNÇÃO PARA ADICIONAR EVENTOS A UMA LINHA DE SERVIÇO
// ===========================================

function adicionarEventosServico(linha) {
    const valorInput = linha.querySelector('.valor-servico');
    if (valorInput) {
        valorInput.addEventListener('input', window.calcularTotais);
        valorInput.addEventListener('change', window.calcularTotais);
        valorInput.addEventListener('keyup', window.calcularTotais);
    }
}

// ===========================================
// FUNÇÃO PARA ADICIONAR EVENTOS A UMA LINHA DE PEÇA
// ===========================================

function adicionarEventosPeca(linha) {
    const qtdInput = linha.querySelector('.qtd-peca');
    const valorCustoInput = linha.querySelector('.valor-custo-peca');
    const lucroInput = linha.querySelector('.lucro-peca');
    
    if (qtdInput) {
        qtdInput.addEventListener('input', function() { window.calcularTotalPeca(this); });
        qtdInput.addEventListener('change', function() { window.calcularTotalPeca(this); });
        qtdInput.addEventListener('keyup', function() { window.calcularTotalPeca(this); });
    }

    if (valorCustoInput) {
        valorCustoInput.addEventListener('input', function() { window.calcularTotalPeca(this); });
        valorCustoInput.addEventListener('change', function() { window.calcularTotalPeca(this); });
        valorCustoInput.addEventListener('keyup', function() { window.calcularTotalPeca(this); });
    }

    if (lucroInput) {
        lucroInput.addEventListener('input', function() { window.calcularTotalPeca(this); });
        lucroInput.addEventListener('change', function() { window.calcularTotalPeca(this); });
        lucroInput.addEventListener('keyup', function() { window.calcularTotalPeca(this); });
    }

    linha.querySelectorAll('input[type="number"]').forEach((input) => {
        input.addEventListener('wheel', function(e) {
            e.preventDefault();
            input.blur();
        }, { passive: false });
    });
}

// ===========================================
// FUNÇÕES DE SERVIÇOS
// ===========================================

window.adicionarServico = function() {
    contadorServicos++;
    const codigo = String.fromCharCode(64 + contadorServicos);
    
    const tbody = document.getElementById('corpo-servicos');
    if (!tbody) {
        alertErro('Tabela de serviços não encontrada.');
        return;
    }
    
    const novaLinha = document.createElement('tr');
    novaLinha.id = `servico-${contadorServicos}`;
    novaLinha.innerHTML = `
        <td><input type="text" class="codigo-servico" value="${codigo}" readonly style="width:60px"></td>
        <td><input type="text" class="descricao-servico" placeholder="Descrição do serviço" style="width:100%"></td>
        <td><input type="number" class="valor-servico" placeholder="0,00" step="0.01" style="width:100%"></td>
        <td><button type="button" class="btn-remover" onclick="window.removerServico(this)">Excluir</button></td>
    `;
    tbody.appendChild(novaLinha);
    
    adicionarEventosServico(novaLinha);
};

window.removerServico = async function(botao) {
    const confirmado = window.ui?.confirmAsync
        ? await window.ui.confirmAsync('Confirma remover este serviço?')
        : (window.ui ? window.ui.confirm('Confirma remover este serviço?') : confirm('Confirma remover este serviço?'));
    if (!confirmado) return;

    const linha = botao.closest('tr');
    linha.remove();
    window.calcularTotais();
};

// ===========================================
// FUNÇÕES DE PEÇAS
// ===========================================

window.adicionarPeca = function() {
    contadorPecas++;
    
    const tbody = document.getElementById('corpo-pecas');
    if (!tbody) {
        alertErro('Tabela de peças não encontrada.');
        return;
    }
    
    // Pega o último código de serviço para gerar código da peça
    const ultimoServico = document.querySelector('#corpo-servicos tr:last-child .codigo-servico');
    const codigoServico = ultimoServico ? ultimoServico.value : 'A';
    
    const novaLinha = document.createElement('tr');
    novaLinha.id = `peca-${contadorPecas}`;
    novaLinha.innerHTML = `
        <td><input type="text" class="codigo-peca" value="${codigoServico}.${contadorPecas}" readonly style="width:80px"></td>
        <td><input type="text" class="descricao-peca" placeholder="Descrição da peça" style="width:100%"></td>
        <td><input type="number" class="qtd-peca" placeholder="Qtd" step="0.01" value="1" style="width:80px"></td>
        <td><input type="number" class="valor-custo-peca" placeholder="Custo" step="0.01" style="width:110px"></td>
        <td><input type="number" class="lucro-peca" placeholder="%" step="0.01" value="0" style="width:85px"></td>
        <td><input type="number" class="valor-unitario-peca" placeholder="Venda" step="0.01" style="width:110px" readonly></td>
        <td><span class="total-peca">R$ 0,00</span></td>
        <td><button type="button" class="btn-remover" onclick="window.removerPeca(this)">Excluir</button></td>
    `;
    tbody.appendChild(novaLinha);
    
    adicionarEventosPeca(novaLinha);
};

window.removerPeca = async function(botao) {
    const confirmado = window.ui?.confirmAsync
        ? await window.ui.confirmAsync('Confirma remover esta peça?')
        : (window.ui ? window.ui.confirm('Confirma remover esta peça?') : confirm('Confirma remover esta peça?'));
    if (!confirmado) return;

    const linha = botao.closest('tr');
    linha.remove();
    window.calcularTotais();
};

// ===========================================
// FUNÇÃO PARA VERIFICAR CAMPOS EXISTENTES
// ===========================================

function verificarCamposExistentes() {
    // Adicionar eventos a serviços existentes (se houver)
    document.querySelectorAll('#corpo-servicos tr').forEach(linha => {
        adicionarEventosServico(linha);
    });
    
    // Adicionar eventos a peças existentes (se houver)
    document.querySelectorAll('#corpo-pecas tr').forEach(linha => {
        adicionarEventosPeca(linha);
    });
}

// ===========================================
// FUNÇÃO DE BUSCA DE CLIENTE
// ===========================================

window.buscarCliente = async function() {
    const termo = document.getElementById("buscaCliente").value.trim();
    
    if (!termo) {
        alertErro('Digite o nome ou CPF do cliente.');
        return;
    }

    try {
        const clienteSugerido = sugestoesClientes.find((c) => {
            const nome = (c.nome_cliente || '').toLowerCase();
            const cpf = (c.cpf || '').toLowerCase();
            const buscado = termo.toLowerCase();
            return nome === buscado || cpf === buscado;
        });
        if (clienteSugerido) {
            preencherDadosCliente(clienteSugerido);
            esconderSugestoesCliente();
            return;
        }

        const response = await fetch(`/api/clientes/busca?termo=${encodeURIComponent(termo)}`);
        const resultados = await response.json();

        if (resultados.length === 0) {
            alertErro('Cliente não encontrado.');
            return;
        }

        const encontrado = resultados[0];
        preencherDadosCliente(encontrado);
        esconderSugestoesCliente();
        
    } catch (error) {
        alertErro('Falha ao buscar cliente.');
        console.error(error);
    }
};

// ===========================================
// FUNÇÃO DE COLETA DE DADOS
// ===========================================

function coletarDadosOrdem() {
    if (!clienteSelecionado) {
        alertErro('Selecione um cliente primeiro.');
        return null;
    }

    const profissionalResponsavel = document.getElementById('profissional_responsavel')?.value?.trim() || '';
    if (!profissionalResponsavel) {
        alertErro('Selecione um profissional cadastrado.');
        return null;
    }

    const profissionalValido = profissionaisDisponiveis.some((p) => (p?.nome || '').trim() === profissionalResponsavel);
    if (!profissionalValido) {
        alertErro('Profissional inválido. Selecione um profissional cadastrado.');
        return null;
    }
    
    // Coletar serviços
    const servicos = [];
    document.querySelectorAll('#corpo-servicos tr').forEach(linha => {
        const descricao = linha.querySelector('.descricao-servico')?.value;
        if (descricao && descricao.trim() !== '') {
            servicos.push({
                codigo_servico: linha.querySelector('.codigo-servico')?.value || '',
                descricao_servico: descricao,
                valor_servico: parseFloat(linha.querySelector('.valor-servico')?.value) || 0
            });
        }
    });
    
    // Coletar peças
    const pecas = [];
    document.querySelectorAll('#corpo-pecas tr').forEach(linha => {
        const descricao = linha.querySelector('.descricao-peca')?.value;
        if (descricao && descricao.trim() !== '') {
            pecas.push({
                codigo_peca: linha.querySelector('.codigo-peca')?.value || '',
                descricao_peca: descricao,
                quantidade: parseFloat(linha.querySelector('.qtd-peca')?.value) || 0,
                valor_custo: parseFloat(linha.querySelector('.valor-custo-peca')?.value) || 0,
                percentual_lucro: parseFloat(linha.querySelector('.lucro-peca')?.value) || 0,
                valor_unitario: parseFloat(linha.querySelector('.valor-unitario-peca')?.value) || 0
            });
        }
    });
    
    if (servicos.length === 0 && pecas.length === 0) {
        alertErro('Adicione pelo menos um serviço ou peça.');
        return null;
    }
    
    return {
        cliente_id: clienteSelecionado.id,
        diagnostico: document.getElementById('diagnostico')?.value || '',
        profissional_responsavel: profissionalResponsavel,
        assinatura_cliente: document.getElementById('assinatura_cliente')?.value || '',
        servicos: servicos,
        pecas: pecas
    };
}

// ===========================================
// FUNÇÃO SALVAR ORDEM
// ===========================================

window.salvarOrdem = async function() {
    const dados = coletarDadosOrdem();
    if (!dados) return;

    const resultado = await criarOrdemNoServidor(dados);
    if (!resultado) return;

    alertSucesso('Ordem salva com sucesso.');
    window.location.assign('/nova-os');
};

// ===========================================
// FUNÇÃO SALVAR E IMPRIMIR - GERA PDF DIRETO
// ===========================================

function montarMensagemOrcamento(resultado, dados) {
    const cliente = clienteSelecionado || {};
    const telefoneCliente = cliente.telefone || 'não informado';
    const servicosResumo = (dados.servicos || []).map((s) => `- ${s.descricao_servico}: ${formatarValor(s.valor_servico)}`).join('\n');
    const pecasResumo = (dados.pecas || []).map((p) => `- ${p.descricao_peca}: ${formatarValor((p.quantidade || 0) * (p.valor_unitario || 0))}`).join('\n');

    return [
        `Olá! Orçamento da OS #${resultado.id}`,
        `Cliente: ${cliente.nome_cliente || '---'}`,
        `Telefone do cliente: ${telefoneCliente}`,
        `Veículo: ${(cliente.fabricante || '')} ${(cliente.modelo || '')} - ${cliente.placa || '---'}`.trim(),
        `Profissional: ${dados.profissional_responsavel || '---'}`,
        dados.servicos?.length ? `Serviços:\n${servicosResumo}` : 'Serviços: não informados',
        dados.pecas?.length ? `Peças:\n${pecasResumo}` : 'Peças: não informadas',
        `Total: ${formatarValor(resultado.total_geral || 0)}`
    ].join('\n\n');
}

function abrirPreviewOrcamento(ordemId, resultado = null, dados = null) {
    const numeroWhatsapp = normalizarWhatsapp(whatsappOrcamentoConfigurado);
    const mensagem = resultado && dados ? encodeURIComponent(montarMensagemOrcamento(resultado, dados)) : '';
    const query = new URLSearchParams({ id: String(ordemId) });

    if (numeroWhatsapp) query.set('phone', numeroWhatsapp);
    if (mensagem) query.set('text', mensagem);

    const urlPdf = `/preview-orcamento.html?${query.toString()}`;
    window.location.assign(urlPdf);
    return true;
}

window.enviarOrcamentoWhatsapp = async function() {
    const dados = coletarDadosOrdem();
    if (!dados) {
        return;
    }

    const resultado = await criarOrdemNoServidor(dados);
    if (!resultado) {
        return;
    }

    abrirPreviewOrcamento(resultado.id, resultado, dados);
};

window.finalizarNoCaixa = async function() {
    const dados = coletarDadosOrdem();
    if (!dados) return;

    const resultado = await criarOrdemNoServidor(dados);
    if (!resultado) return;

    window.location.assign(`/fluxo_caixa.html?ordem_id=${resultado.id}&origem=nova_os`);
};

window.salvarEImprimir = async function() {
    const dados = coletarDadosOrdem();
    if (!dados) return;

    const resultado = await criarOrdemNoServidor(dados);
    if (!resultado) return;

    abrirPdfOrdem(resultado.id);
    alertSucesso('Ordem salva e PDF gerado.');
    window.location.assign('/nova-os');
};

function abrirPdfOrdem(ordemId) {
    const urlPdf = `/api/export/gerar-pdf/${ordemId}`;
    try {
        const link = document.createElement('a');
        link.href = urlPdf;
        link.target = '_blank';
        link.rel = 'noopener';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    } catch (e) {
        console.warn('Falha ao abrir PDF em nova janela:', e);
        alertErro('Nao foi possivel abrir o PDF automaticamente. Verifique bloqueio de popup.');
    }
}

async function criarOrdemNoServidor(dados) {
    try {
        const response = await fetch('/api/ordens/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });

        const resultado = await response.json();
        if (!response.ok) {
            alertErro(resultado.erro || 'Erro desconhecido.');
            return null;
        }

        return resultado;
    } catch (error) {
        alertErro('Falha ao salvar ordem.');
        console.error(error);
        return null;
    }
}
// ===========================================
// FUNÇÃO CANCELAR
// ===========================================

window.cancelar = async function() {
    const confirmado = window.ui?.confirmAsync
        ? await window.ui.confirmAsync('Confirma cancelar esta operação?')
        : (window.ui ? window.ui.confirm('Confirma cancelar esta operação?') : confirm('Confirma cancelar esta operação?'));
    if (!confirmado) return;
    window.location.assign('/');
};

function limparFormularioNovaOrdem() {
    clienteSelecionado = null;
    sugestoesClientes = [];
    esconderSugestoesCliente();

    const idsCamposClienteVeiculo = [
        'buscaCliente', 'nome_cliente', 'cpf', 'endereco', 'cidade', 'estado', 'cep',
        'telefone', 'email', 'placa', 'fabricante', 'modelo', 'ano', 'motor',
        'combustivel', 'cor', 'tanque', 'km', 'direcao', 'ar', 'diagnostico',
        'assinatura_cliente'
    ];
    idsCamposClienteVeiculo.forEach((id) => {
        const el = document.getElementById(id);
        if (!el) return;
        if (el.tagName === 'SELECT') {
            el.selectedIndex = 0;
        } else {
            el.value = '';
        }
    });
    const buscaInput = document.getElementById('buscaCliente');
    if (buscaInput) buscaInput.style.borderColor = '';

    const profissionalSelect = document.getElementById('profissional_responsavel');
    if (profissionalSelect) profissionalSelect.selectedIndex = 0;

    const tbodyServicos = document.getElementById('corpo-servicos');
    const tbodyPecas = document.getElementById('corpo-pecas');
    if (tbodyServicos) tbodyServicos.innerHTML = '';
    if (tbodyPecas) tbodyPecas.innerHTML = '';

    contadorServicos = 0;
    contadorPecas = 0;
    window.calcularTotais();
    window.scrollTo({ top: 0, behavior: 'smooth' });
    buscaInput?.focus();
}

// ===========================================
// TIMER PARA ATUALIZAÇÃO CONTÍNUA
// ===========================================

setInterval(function() {
    window.calcularTotais();
}, 500);

// ===========================================
// INICIALIZAÇÃO
// ===========================================

document.addEventListener('DOMContentLoaded', function() {
    carregarProfissionais();
    carregarWhatsappOrcamento();
    verificarCamposExistentes();

    const buscaInput = document.getElementById('buscaCliente');
    if (buscaInput) {
        buscaInput.addEventListener('input', () => {
            const termo = buscaInput.value.trim();
            if (timerBuscaCliente) clearTimeout(timerBuscaCliente);
            timerBuscaCliente = setTimeout(() => {
                buscarSugestoesCliente(termo);
            }, 220);
        });
    }

    document.addEventListener('click', (event) => {
        const input = document.getElementById('buscaCliente');
        const box = document.getElementById('sugestoesCliente');
        if (!input || !box) return;
        const clicouDentro = input.contains(event.target) || box.contains(event.target);
        if (!clicouDentro) esconderSugestoesCliente();
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === 'F2') {
            e.preventDefault();
            document.getElementById('buscaCliente')?.focus();
            return;
        }
        if (e.key === 'F4') {
            e.preventDefault();
            window.adicionarServico();
            return;
        }
        if (e.key === 'F6') {
            e.preventDefault();
            window.enviarOrcamentoWhatsapp();
            return;
        }
        if (e.key === 's' && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            window.salvarOrdem();
        }
    });
});



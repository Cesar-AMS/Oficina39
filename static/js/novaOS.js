// ===========================================
// ordemServico.js - VERSÃƒO PADRONIZADA
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
// FUNÃ‡Ã•ES AUXILIARES
// ===========================================

function formatarValor(valor) {
    return 'R$ ' + (valor || 0).toFixed(2).replace('.', ',');
}

function formatarStatusExibicao(status) {
    return status === 'ConcluÃ­do' ? 'Finalizado' : (status || '---');
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
            <div class="sugestao-cpf">${c.cpf || 'CPF nÃ£o informado'}</div>
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
        console.error('Erro ao carregar WhatsApp do orÃ§amento:', error);
    }
}

// ===========================================
// FUNÃ‡ÃƒO DE CÃLCULO (SERÃ CHAMADA DE VÃRIAS FORMAS)
// ===========================================

window.calcularTotais = function() {
    // Calcular serviÃ§os
    let totalServicos = 0;
    document.querySelectorAll('#corpo-servicos .valor-servico').forEach(input => {
        let valor = parseFloat(input.value);
        if (!isNaN(valor) && valor > 0) {
            totalServicos += valor;
        }
    });
    
    // Calcular peÃ§as
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
// FUNÃ‡ÃƒO PARA ATUALIZAR TOTAL DE UMA PEÃ‡A
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
// FUNÃ‡ÃƒO PARA ADICIONAR EVENTOS A UMA LINHA DE SERVIÃ‡O
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
// FUNÃ‡ÃƒO PARA ADICIONAR EVENTOS A UMA LINHA DE PEÃ‡A
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
// FUNÃ‡Ã•ES DE SERVIÃ‡OS
// ===========================================

window.adicionarServico = function() {
    contadorServicos++;
    const codigo = String.fromCharCode(64 + contadorServicos);
    
    const tbody = document.getElementById('corpo-servicos');
    if (!tbody) {
        alertErro('Tabela de serviÃ§os nÃ£o encontrada.');
        return;
    }
    
    const novaLinha = document.createElement('tr');
    novaLinha.id = `servico-${contadorServicos}`;
    novaLinha.innerHTML = `
        <td><input type="text" class="codigo-servico" value="${codigo}" readonly style="width:60px"></td>
        <td><input type="text" class="descricao-servico" placeholder="DescriÃ§Ã£o do serviÃ§o" style="width:100%"></td>
        <td><input type="number" class="valor-servico" placeholder="0,00" step="0.01" style="width:100%"></td>
        <td><button type="button" class="btn-remover" onclick="window.removerServico(this)">Excluir</button></td>
    `;
    tbody.appendChild(novaLinha);
    
    adicionarEventosServico(novaLinha);
};

window.removerServico = async function(botao) {
    const confirmado = window.ui?.confirmAsync
        ? await window.ui.confirmAsync('Confirma remover este serviÃ§o?')
        : (window.ui ? window.ui.confirm('Confirma remover este serviÃ§o?') : confirm('Confirma remover este serviÃ§o?'));
    if (!confirmado) return;

    const linha = botao.closest('tr');
    linha.remove();
    window.calcularTotais();
};

// ===========================================
// FUNÃ‡Ã•ES DE PEÃ‡AS
// ===========================================

window.adicionarPeca = function() {
    contadorPecas++;
    
    const tbody = document.getElementById('corpo-pecas');
    if (!tbody) {
        alertErro('Tabela de peÃ§as nÃ£o encontrada.');
        return;
    }
    
    // Pega o Ãºltimo cÃ³digo de serviÃ§o para gerar cÃ³digo da peÃ§a
    const ultimoServico = document.querySelector('#corpo-servicos tr:last-child .codigo-servico');
    const codigoServico = ultimoServico ? ultimoServico.value : 'A';
    
    const novaLinha = document.createElement('tr');
    novaLinha.id = `peca-${contadorPecas}`;
    novaLinha.innerHTML = `
        <td><input type="text" class="codigo-peca" value="${codigoServico}.${contadorPecas}" readonly style="width:80px"></td>
        <td><input type="text" class="descricao-peca" placeholder="DescriÃ§Ã£o da peÃ§a" style="width:100%"></td>
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
        ? await window.ui.confirmAsync('Confirma remover esta peÃ§a?')
        : (window.ui ? window.ui.confirm('Confirma remover esta peÃ§a?') : confirm('Confirma remover esta peÃ§a?'));
    if (!confirmado) return;

    const linha = botao.closest('tr');
    linha.remove();
    window.calcularTotais();
};

// ===========================================
// FUNÃ‡ÃƒO PARA VERIFICAR CAMPOS EXISTENTES
// ===========================================

function verificarCamposExistentes() {
    // Adicionar eventos a serviÃ§os existentes (se houver)
    document.querySelectorAll('#corpo-servicos tr').forEach(linha => {
        adicionarEventosServico(linha);
    });
    
    // Adicionar eventos a peÃ§as existentes (se houver)
    document.querySelectorAll('#corpo-pecas tr').forEach(linha => {
        adicionarEventosPeca(linha);
    });
}

// ===========================================
// FUNÃ‡ÃƒO DE BUSCA DE CLIENTE
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
            alertErro('Cliente nÃ£o encontrado.');
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
// FUNÃ‡ÃƒO DE COLETA DE DADOS
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
        alertErro('Profissional invÃ¡lido. Selecione um profissional cadastrado.');
        return null;
    }
    
    // Coletar serviÃ§os
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
    
    // Coletar peÃ§as
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
        alertErro('Adicione pelo menos um serviÃ§o ou peÃ§a.');
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
// FUNÃ‡ÃƒO SALVAR ORDEM
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
// FUNÃ‡ÃƒO SALVAR E IMPRIMIR - GERA PDF DIRETO
// ===========================================

function montarMensagemOrcamento(resultado, dados) {
    const cliente = clienteSelecionado || {};
    const telefoneCliente = cliente.telefone || 'nÃ£o informado';
    const servicosResumo = (dados.servicos || []).map((s) => `- ${s.descricao_servico}: ${formatarValor(s.valor_servico)}`).join('%0A');
    const pecasResumo = (dados.pecas || []).map((p) => `- ${p.descricao_peca}: ${formatarValor((p.quantidade || 0) * (p.valor_unitario || 0))}`).join('%0A');

    return [
        `OlÃ¡! OrÃ§amento da OS #${resultado.id}`,
        `Cliente: ${cliente.nome_cliente || '---'}`,
        `Telefone do cliente: ${telefoneCliente}`,
        `VeÃ­culo: ${(cliente.fabricante || '')} ${(cliente.modelo || '')} - ${cliente.placa || '---'}`.trim(),
        `Profissional: ${dados.profissional_responsavel || '---'}`,
        dados.servicos?.length ? `ServiÃ§os:%0A${servicosResumo}` : 'ServiÃ§os: nÃ£o informados',
        dados.pecas?.length ? `PeÃ§as:%0A${pecasResumo}` : 'PeÃ§as: nÃ£o informadas',
        `Total: ${formatarValor(resultado.total_geral || 0)}`
    ].join('%0A%0A');
}

function abrirWhatsappOrcamento(resultado, dados, janelaExistente = null) {
    const numeroWhatsapp = normalizarWhatsapp(whatsappOrcamentoConfigurado);
    if (!numeroWhatsapp) {
        alertErro('Configure o WhatsApp da oficina em ConfiguraÃ§Ãµes antes de enviar orÃ§amento.');
        return;
    }
    const mensagem = montarMensagemOrcamento(resultado, dados);
    const url = `https://wa.me/${numeroWhatsapp}?text=${mensagem}`;
    const janela = janelaExistente || window.open('about:blank', '_blank', 'noopener');
    if (janela) {
        janela.location.replace(url);
        return;
    }
    window.location.assign(url);
}

function abrirPreviewOrcamento(ordemId) {
    const urlPdf = `/api/export/gerar-pdf/${ordemId}?inline=1`;
    window.location.assign(urlPdf);
    return true;
}

function prepararJanelaWhatsappOrcamento() {
    const janela = window.open('about:blank', '_blank', 'noopener');
    if (janela) {
        janela.document.title = 'WhatsApp';
        janela.document.body.innerHTML = '<p style="font-family: Arial, sans-serif; padding: 24px;">Preparando envio do orcamento no WhatsApp...</p>';
    }
    return janela;
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

    abrirPreviewOrcamento(resultado.id);
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
// FUNÃ‡ÃƒO CANCELAR
// ===========================================

window.cancelar = async function() {
    const confirmado = window.ui?.confirmAsync
        ? await window.ui.confirmAsync('Confirma cancelar esta operaÃ§Ã£o?')
        : (window.ui ? window.ui.confirm('Confirma cancelar esta operaÃ§Ã£o?') : confirm('Confirma cancelar esta operaÃ§Ã£o?'));
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
// TIMER PARA ATUALIZAÃ‡ÃƒO CONTÃNUA
// ===========================================

setInterval(function() {
    window.calcularTotais();
}, 500);

// ===========================================
// INICIALIZAÃ‡ÃƒO
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



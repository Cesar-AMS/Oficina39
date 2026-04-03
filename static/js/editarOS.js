// editarOS.js

const params = new URLSearchParams(window.location.search);
const id = params.get("id");

let contadorServicos = 0;
let contadorPecas = 0;

function alertErro(mensagem) {
    if (window.ui) return window.ui.error(mensagem);
    alert(`Erro: ${mensagem}`);
}

function alertSucesso(mensagem) {
    if (window.ui) return window.ui.success(mensagem);
    alert(`Sucesso: ${mensagem}`);
}

// ===========================================
// FUNÇÕES DE FORMATAÇÃO
// ===========================================

function formatarValor(valor) {
    if (!valor && valor !== 0) return 'R$ 0,00';
    return 'R$ ' + valor.toFixed(2).replace('.', ',');
}

function parseDecimalBr(valor) {
    if (valor === null || valor === undefined) return 0;
    if (typeof valor === 'number') return Number.isFinite(valor) ? valor : 0;

    let texto = String(valor).trim();
    if (!texto) return 0;

    texto = texto.replace(/\s+/g, '').replace('R$', '').replace('r$', '');

    if (texto.includes(',') && texto.includes('.')) {
        texto = texto.replace(/\./g, '').replace(',', '.');
    } else if (texto.includes(',')) {
        texto = texto.replace(',', '.');
    }

    const numero = Number(texto);
    return Number.isFinite(numero) ? numero : 0;
}

function arredondarDecimal(valor, casas = 2) {
    const fator = 10 ** casas;
    return Math.round((Number(valor || 0) + Number.EPSILON) * fator) / fator;
}

function formatarDecimalCampo(valor, casas = 2) {
    const numero = parseDecimalBr(valor);
    return numero.toLocaleString('pt-BR', {
        minimumFractionDigits: casas,
        maximumFractionDigits: casas
    });
}

function formatarQuantidadeCampo(valor) {
    const numero = parseDecimalBr(valor);
    if (Number.isInteger(numero)) {
        return numero.toLocaleString('pt-BR', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        });
    }
    return numero.toLocaleString('pt-BR', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    });
}

function calcularValorVendaPeca(valorCusto, percentualLucro) {
    const custo = parseDecimalBr(valorCusto);
    const lucro = parseDecimalBr(percentualLucro);
    return arredondarDecimal(custo * (1 + (lucro / 100)));
}

function formatarData(data) {
    if (!data) return '';
    try {
        const date = new Date(data);
        return date.toLocaleDateString('pt-BR') + ' ' + date.toLocaleTimeString('pt-BR');
    } catch {
        return data;
    }
}

function elementoVisivelParaEnter(el) {
    if (!el || el.disabled || el.hidden) return false;
    const style = window.getComputedStyle(el);
    return style.display !== 'none' && style.visibility !== 'hidden';
}

function focarProximoCampoEdicao(atual) {
    const campos = Array.from(document.querySelectorAll(
        'input:not([type="hidden"]), select, textarea, button'
    )).filter((el) => elementoVisivelParaEnter(el) && !el.readOnly);
    const indice = campos.indexOf(atual);
    if (indice === -1) return false;
    for (let i = indice + 1; i < campos.length; i += 1) {
        const proximo = campos[i];
        if (!elementoVisivelParaEnter(proximo) || proximo.readOnly) continue;
        proximo.focus();
        if (typeof proximo.select === 'function' && proximo.tagName === 'INPUT') {
            proximo.select();
        }
        return true;
    }
    return false;
}

function configurarEnterEditarOs() {
    document.addEventListener('keydown', function(e) {
        if (e.key !== 'Enter') return;
        const alvo = e.target;
        if (!(alvo instanceof HTMLElement)) return;
        if (alvo.tagName === 'TEXTAREA' || alvo.tagName === 'BUTTON') return;
        if (alvo.matches('.valor-servico, .qtd-peca, .valor-custo-peca, .lucro-peca')) {
            e.preventDefault();
            if (typeof alvo.blur === 'function') alvo.blur();
            focarProximoCampoEdicao(alvo);
            return;
        }
        if (alvo.matches('input, select')) {
            e.preventDefault();
            focarProximoCampoEdicao(alvo);
        }
    });
}

function aplicarMascaraDecimalAoSair(input, casas = 2, callback = null) {
    if (!input) return;
    input.addEventListener('blur', () => {
        input.value = formatarDecimalCampo(input.value, casas);
        if (typeof callback === 'function') callback(input);
    });
}

function aplicarMascaraQuantidadeAoSair(input, callback = null) {
    if (!input) return;
    input.addEventListener('blur', () => {
        input.value = formatarQuantidadeCampo(input.value);
        if (typeof callback === 'function') callback(input);
    });
}

function adicionarEventosServico(linha) {
    const valorInput = linha.querySelector('.valor-servico');
    if (valorInput) {
        aplicarMascaraDecimalAoSair(valorInput, 2, () => calcularTotais());
    }
}

function adicionarEventosPeca(linha) {
    const qtdInput = linha.querySelector('.qtd-peca');
    const valorCustoInput = linha.querySelector('.valor-custo-peca');
    const lucroInput = linha.querySelector('.lucro-peca');

    if (qtdInput) {
        aplicarMascaraQuantidadeAoSair(qtdInput, (input) => calcularTotalPeca(input));
    }

    if (valorCustoInput) {
        aplicarMascaraDecimalAoSair(valorCustoInput, 2, (input) => calcularTotalPeca(input));
    }

    if (lucroInput) {
        aplicarMascaraDecimalAoSair(lucroInput, 2, (input) => calcularTotalPeca(input));
    }
}

// ===========================================
// CARREGAR DADOS DA ORDEM
// ===========================================

async function carregarOrdem() {
    if (!id) {
        alertErro('ID da ordem não informado.');
        window.location.assign("/consultarOS.html");
        return;
    }

    try {
        const response = await fetch(`/api/ordens/${id}`);
        
        if (!response.ok) {
            alertErro('Ordem não encontrada.');
            window.location.assign("/consultarOS.html");
            return;
        }

        const ordem = await response.json();
        preencherCampos(ordem);
        
    } catch (error) {
        console.error('Erro:', error);
        alertErro('Falha ao carregar ordem.');
        window.location.assign("/consultarOS.html");
    }
}

function preencherCampos(ordem) {
    document.getElementById('ordemId').textContent = ordem.id;
    
    // Dados do cliente (readonly)
    const cliente = ordem.cliente || {};
    document.getElementById('nome_cliente').value = cliente.nome_cliente || '';
    document.getElementById('cpf').value = cliente.cpf || '';
    document.getElementById('endereco').value = cliente.endereco || '';
    
    // Dados do veículo (readonly)
    document.getElementById('placa').value = cliente.placa || '';
    document.getElementById('fabricante').value = cliente.fabricante || '';
    document.getElementById('modelo').value = cliente.modelo || '';
    document.getElementById('ano').value = cliente.ano || '';
    document.getElementById('motor').value = cliente.motor || '';
    document.getElementById('combustivel').value = cliente.combustivel || '';
    document.getElementById('cor').value = cliente.cor || '';
    document.getElementById('tanque').value = cliente.tanque || '';
    document.getElementById('km').value = cliente.km || '';
    document.getElementById('direcao').value = cliente.direcao || '';
    document.getElementById('ar').value = cliente.ar || '';
    
    // Diagnóstico
    document.getElementById('diagnostico').value = ordem.diagnostico || '';
    document.getElementById('profissional_responsavel').value = ordem.profissional_responsavel || '';
    
    // Assinatura
    document.getElementById('assinatura_cliente').value = ordem.assinatura_cliente || '';
    
    // Datas
    document.getElementById('data_entrada').value = formatarData(ordem.data_entrada);
    document.getElementById('data_emissao').value = formatarData(ordem.data_emissao);
    document.getElementById('data_retirada').value = ordem.data_retirada ? 
        ordem.data_retirada.split('T')[0] : '';
    
    // Status
    document.getElementById('status').value = ordem.status || 'Aguardando';
    const bloqueada = ordem.status === 'Concluído' || ordem.status === 'Garantia';
    if (bloqueada) {
        const aviso = document.getElementById('avisoEdicaoBloqueada');
        const btnSalvar = document.getElementById('btnSalvarEdicao');
        if (aviso) aviso.style.display = 'block';
        if (btnSalvar) {
            btnSalvar.disabled = true;
            btnSalvar.title = 'Reabra a ordem na consulta para editar.';
        }
    }
    
    // Serviços
    if (ordem.servicos && ordem.servicos.length > 0) {
        ordem.servicos.forEach(servico => {
            adicionarServico(servico);
        });
    } else {
        adicionarServico(); // Adiciona uma linha vazia
    }
    
    // Peças
    if (ordem.pecas && ordem.pecas.length > 0) {
        ordem.pecas.forEach(peca => {
            adicionarPeca(peca);
        });
    } else {
        adicionarPeca(); // Adiciona uma linha vazia
    }
    
    calcularTotais();
}

// ===========================================
// FUNÇÕES DE SERVIÇOS
// ===========================================

function adicionarServico(dados = null) {
    contadorServicos++;
    const codigo = dados ? dados.codigo_servico : String.fromCharCode(64 + contadorServicos);
    const descricao = dados ? dados.descricao_servico : '';
    const valor = dados ? dados.valor_servico : 0;
    
    const tbody = document.getElementById('corpo-servicos');
    const novaLinha = document.createElement('tr');
    novaLinha.id = `servico-${contadorServicos}`;
    novaLinha.innerHTML = `
        <td><input type="text" class="codigo-servico" value="${codigo}" style="width: 60px;"></td>
        <td><input type="text" class="descricao-servico" value="${descricao.replace(/"/g, '&quot;')}" placeholder="Descrição" style="width: 100%;"></td>
        <td><input type="text" inputmode="decimal" class="valor-servico" value="${formatarDecimalCampo(valor)}" placeholder="0,00" onchange="calcularTotais()" style="width: 100%;"></td>
        <td><button type="button" class="btn-remover" onclick="removerServico(${contadorServicos})">Excluir</button></td>
    `;
    tbody.appendChild(novaLinha);
    adicionarEventosServico(novaLinha);
}

async function removerServico(id) {
    const confirmado = window.ui?.confirmAsync
        ? await window.ui.confirmAsync('Confirma remover este serviço?')
        : (window.ui ? window.ui.confirm('Confirma remover este serviço?') : confirm('Confirma remover este serviço?'));
    if (!confirmado) return;
    document.getElementById(`servico-${id}`).remove();
    calcularTotais();
}

// ===========================================
// FUNÇÕES DE PEÇAS
// ===========================================

function adicionarPeca(dados = null) {
    contadorPecas++;
    
    let codigo = dados ? dados.codigo_peca : '';
    if (!codigo) {
        const ultimoServico = document.querySelector('.codigo-servico:last-child');
        const codigoServico = ultimoServico ? ultimoServico.value : 'A';
        codigo = `${codigoServico}.${contadorPecas}`;
    }
    
    const descricao = dados ? dados.descricao_peca : '';
    const quantidade = dados ? dados.quantidade : 1;
    const valorCusto = dados ? (dados.valor_custo || 0) : 0;
    const lucro = dados ? (dados.percentual_lucro || 0) : 0;
    const valor = dados ? dados.valor_unitario : calcularValorVendaPeca(valorCusto, lucro);
    
    const tbody = document.getElementById('corpo-pecas');
    const novaLinha = document.createElement('tr');
    novaLinha.id = `peca-${contadorPecas}`;
    novaLinha.innerHTML = `
        <td><input type="text" class="codigo-peca" value="${codigo}" style="width: 80px;"></td>
        <td><input type="text" class="descricao-peca" value="${descricao.replace(/"/g, '&quot;')}" placeholder="Descrição" style="width: 100%;"></td>
        <td><input type="text" inputmode="decimal" class="qtd-peca" value="${formatarQuantidadeCampo(quantidade)}" onchange="calcularTotalPeca(this)" style="width: 80px;"></td>
        <td><input type="text" inputmode="decimal" class="valor-custo-peca" value="${formatarDecimalCampo(valorCusto)}" onchange="calcularTotalPeca(this)" style="width: 100px;"></td>
        <td><input type="text" inputmode="decimal" class="lucro-peca" value="${formatarDecimalCampo(lucro)}" onchange="calcularTotalPeca(this)" style="width: 80px;"></td>
        <td><input type="text" inputmode="decimal" class="valor-unitario-peca" value="${formatarDecimalCampo(valor)}" readonly style="width: 100px;"></td>
        <td><span class="total-peca">${formatarValor(arredondarDecimal(parseDecimalBr(quantidade) * parseDecimalBr(valor)))}</span></td>
        <td><button type="button" class="btn-remover" onclick="removerPeca(${contadorPecas})">Excluir</button></td>
    `;
    tbody.appendChild(novaLinha);
    adicionarEventosPeca(novaLinha);
}

async function removerPeca(id) {
    const confirmado = window.ui?.confirmAsync
        ? await window.ui.confirmAsync('Confirma remover esta peça?')
        : (window.ui ? window.ui.confirm('Confirma remover esta peça?') : confirm('Confirma remover esta peça?'));
    if (!confirmado) return;
    document.getElementById(`peca-${id}`).remove();
    calcularTotais();
}

function calcularTotalPeca(elemento) {
    const linha = elemento.closest('tr');
    const qtd = parseDecimalBr(linha.querySelector('.qtd-peca').value);
    const valorCusto = parseDecimalBr(linha.querySelector('.valor-custo-peca').value);
    const percentualLucro = parseDecimalBr(linha.querySelector('.lucro-peca').value);
    const valor = calcularValorVendaPeca(valorCusto, percentualLucro);
    const total = arredondarDecimal(qtd * valor);
    
    linha.querySelector('.valor-unitario-peca').value = formatarDecimalCampo(valor);
    linha.querySelector('.total-peca').textContent = formatarValor(total);
    calcularTotais();
}

// ===========================================
// FUNÇÕES DE CÁLCULO
// ===========================================

function calcularTotais() {
    let totalServicos = 0;
    document.querySelectorAll('.valor-servico').forEach(input => {
        totalServicos += parseDecimalBr(input.value);
    });
    
    let totalPecas = 0;
    document.querySelectorAll('.total-peca').forEach(span => {
        totalPecas += parseDecimalBr(span.textContent);
    });
    
    document.getElementById('total-servicos').textContent = formatarValor(totalServicos);
    document.getElementById('total-pecas').textContent = formatarValor(totalPecas);
    document.getElementById('total-geral').textContent = formatarValor(totalServicos + totalPecas);
}

// ===========================================
// SALVAR ALTERAÇÕES
// ===========================================

function validarCampos() {
    const profissional = document.getElementById('profissional_responsavel')?.value?.trim();
    if (!profissional) {
        alertErro('Informe o profissional responsável pelo serviço.');
        return false;
    }

    // Verificar se há pelo menos um serviço ou peça
    const temServico = Array.from(document.querySelectorAll('.descricao-servico')).some(
        input => input.value.trim() !== ''
    );
    const temPeca = Array.from(document.querySelectorAll('.descricao-peca')).some(
        input => input.value.trim() !== ''
    );
    
    if (!temServico && !temPeca) {
        alertErro('Adicione pelo menos um serviço ou uma peça.');
        return false;
    }
    
    return true;
}

function coletarDados() {
    // Serviços
    const servicos = [];
    document.querySelectorAll('#corpo-servicos tr').forEach(linha => {
        const codigo = linha.querySelector('.codigo-servico')?.value;
        const descricao = linha.querySelector('.descricao-servico')?.value;
        const valor = parseDecimalBr(linha.querySelector('.valor-servico')?.value);
        
        if (descricao && descricao.trim() !== '') {
            servicos.push({
                codigo_servico: codigo,
                descricao_servico: descricao,
                valor_servico: valor
            });
        }
    });
    
    // Peças
    const pecas = [];
    document.querySelectorAll('#corpo-pecas tr').forEach(linha => {
        const codigo = linha.querySelector('.codigo-peca')?.value;
        const descricao = linha.querySelector('.descricao-peca')?.value;
        const quantidade = parseDecimalBr(linha.querySelector('.qtd-peca')?.value);
        const valor = parseDecimalBr(linha.querySelector('.valor-unitario-peca')?.value);
        
        if (descricao && descricao.trim() !== '') {
            pecas.push({
                codigo_peca: codigo,
                descricao_peca: descricao,
                quantidade: quantidade,
                valor_custo: parseDecimalBr(linha.querySelector('.valor-custo-peca')?.value),
                percentual_lucro: parseDecimalBr(linha.querySelector('.lucro-peca')?.value),
                valor_unitario: valor
            });
        }
    });
    
    return {
        diagnostico: document.getElementById('diagnostico').value,
        profissional_responsavel: document.getElementById('profissional_responsavel').value,
        assinatura_cliente: document.getElementById('assinatura_cliente').value,
        data_retirada: document.getElementById('data_retirada').value,
        status: document.getElementById('status').value,
        servicos: servicos,
        pecas: pecas
    };
}

async function salvar() {
    const statusAtual = document.getElementById('status')?.value;
    if (statusAtual === 'Concluído' || statusAtual === 'Garantia') {
        alertErro('Ordem concluída está bloqueada. Reabra na tela de consulta antes de editar.');
        return;
    }

    if (!validarCampos()) return;
    
    const confirmado = window.ui?.confirmAsync
        ? await window.ui.confirmAsync('Confirma salvar as alterações?')
        : (window.ui ? window.ui.confirm('Confirma salvar as alterações?') : confirm('Confirma salvar as alterações?'));
    if (!confirmado) return;
    
    const dados = coletarDados();
    
    try {
        const response = await fetch(`/api/ordens/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });
        
        const resultado = await response.json();
        
        if (response.ok) {
            alertSucesso('Ordem atualizada com sucesso.');
            window.location.assign(`/visualizarOS.html?id=${id}`);
        } else {
            alertErro(resultado.erro || 'Erro desconhecido.');
        }
    } catch (error) {
        alertErro('Falha ao salvar alterações.');
        console.error(error);
    }
}

// ===========================================
// FUNÇÕES AUXILIARES
// ===========================================

async function cancelar() {
    const confirmado = window.ui?.confirmAsync
        ? await window.ui.confirmAsync('Confirma cancelar? As alterações não serão salvas.')
        : (window.ui ? window.ui.confirm('Confirma cancelar? As alterações não serão salvas.') : confirm('Confirma cancelar? As alterações não serão salvas.'));
    if (!confirmado) return;
    window.location.assign(`/visualizarOS.html?id=${id}`);
}

// ===========================================
// INICIALIZAÇÃO
// ===========================================

document.addEventListener('DOMContentLoaded', function() {
    carregarOrdem();
    configurarEnterEditarOs();
});

// Atalhos de teclado
document.addEventListener('keydown', function(e) {
    if (e.key === 's' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        salvar();
    }
    if (e.key === 'Escape') {
        cancelar();
    }
});


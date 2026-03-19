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

function formatarData(data) {
    if (!data) return '';
    try {
        const date = new Date(data);
        return date.toLocaleDateString('pt-BR') + ' ' + date.toLocaleTimeString('pt-BR');
    } catch {
        return data;
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
        <td><input type="number" class="valor-servico" value="${valor}" placeholder="0,00" step="0.01" onchange="calcularTotais()" style="width: 100%;"></td>
        <td><button type="button" class="btn-remover" onclick="removerServico(${contadorServicos})">🗑️</button></td>
    `;
    tbody.appendChild(novaLinha);
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
    const valor = dados ? dados.valor_unitario : 0;
    
    const tbody = document.getElementById('corpo-pecas');
    const novaLinha = document.createElement('tr');
    novaLinha.id = `peca-${contadorPecas}`;
    novaLinha.innerHTML = `
        <td><input type="text" class="codigo-peca" value="${codigo}" style="width: 80px;"></td>
        <td><input type="text" class="descricao-peca" value="${descricao.replace(/"/g, '&quot;')}" placeholder="Descrição" style="width: 100%;"></td>
        <td><input type="number" class="qtd-peca" value="${quantidade}" step="0.01" onchange="calcularTotalPeca(this)" style="width: 80px;"></td>
        <td><input type="number" class="valor-unitario-peca" value="${valor}" step="0.01" onchange="calcularTotalPeca(this)" style="width: 100px;"></td>
        <td><span class="total-peca">${formatarValor(quantidade * valor)}</span></td>
        <td><button type="button" class="btn-remover" onclick="removerPeca(${contadorPecas})">🗑️</button></td>
    `;
    tbody.appendChild(novaLinha);
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
    const qtd = parseFloat(linha.querySelector('.qtd-peca').value) || 0;
    const valor = parseFloat(linha.querySelector('.valor-unitario-peca').value) || 0;
    const total = qtd * valor;
    
    linha.querySelector('.total-peca').textContent = formatarValor(total);
    calcularTotais();
}

// ===========================================
// FUNÇÕES DE CÁLCULO
// ===========================================

function calcularTotais() {
    let totalServicos = 0;
    document.querySelectorAll('.valor-servico').forEach(input => {
        totalServicos += parseFloat(input.value) || 0;
    });
    
    let totalPecas = 0;
    document.querySelectorAll('.total-peca').forEach(span => {
        const valorTexto = span.textContent.replace('R$ ', '').replace(',', '.');
        totalPecas += parseFloat(valorTexto) || 0;
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
        const valor = parseFloat(linha.querySelector('.valor-servico')?.value) || 0;
        
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
        const quantidade = parseFloat(linha.querySelector('.qtd-peca')?.value) || 0;
        const valor = parseFloat(linha.querySelector('.valor-unitario-peca')?.value) || 0;
        
        if (descricao && descricao.trim() !== '') {
            pecas.push({
                codigo_peca: codigo,
                descricao_peca: descricao,
                quantidade: quantidade,
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

document.addEventListener('DOMContentLoaded', carregarOrdem);

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

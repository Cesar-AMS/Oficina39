// consultarOS.js

let ordens = [];
let tabela;
let buscaCliente;
let profissionaisAtivos = [];

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
    if (!valor) return 'R$ 0,00';
    const num = parseFloat(valor);
    if (isNaN(num)) return 'R$ 0,00';
    return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function formatarData(data) {
    if (!data) return '';
    try {
        const date = new Date(data);
        return date.toLocaleDateString('pt-BR');
    } catch {
        return data;
    }
}

function calcularDiasGarantia(dataConclusao, dataRetirada) {
    const dataBase = dataConclusao || dataRetirada;
    
    if (!dataBase) {
        return 0;
    }
    
    try {
        let dataReferencia;
        
        if (typeof dataBase === 'string' && dataBase.includes('/')) {
            const partes = dataBase.split(' ')[0].split('/');
            dataReferencia = new Date(partes[2], partes[1] - 1, partes[0]);
        } 
        else {
            dataReferencia = new Date(dataBase);
        }
        
        const hoje = new Date();
        
        if (isNaN(dataReferencia.getTime())) {
            return 0;
        }
        
        dataReferencia.setHours(0, 0, 0, 0);
        hoje.setHours(0, 0, 0, 0);
        
        const diffTime = hoje - dataReferencia;
        const diffDias = Math.floor(diffTime / (1000 * 60 * 60 * 24));
        
        return Math.max(0, 90 - diffDias);
    } catch (error) {
        console.error('Erro ao calcular dias:', error);
        return 0;
    }
}

// Função para classe de status
function getStatusClass(status) {
    status = status ? status.toLowerCase() : '';
    if (status.includes('aguardando')) return 'status-aguardando';
    if (status.includes('andamento')) return 'status-andamento';
    if (status.includes('conclu')) return 'status-concluido';
    if (status.includes('garantia')) return 'status-garantia';
    return '';
}

function solicitarFormaPagamento() {
    return new Promise((resolve) => {
        const opcoes = ['Pix', 'Cartão', 'Dinheiro', 'Boleto', 'Transferência'];

        const overlay = document.createElement('div');
        overlay.className = 'modal-pagamento-overlay';
        overlay.innerHTML = `
            <div class="modal-pagamento-box">
                <h3>Forma de Pagamento</h3>
                <p>Selecione como o cliente pagou esta OS:</p>
                <div class="modal-pagamento-opcoes">
                    ${opcoes.map((op) => `<button type="button" class="btn-pagamento-opcao" data-op="${op}">${op}</button>`).join('')}
                </div>
                <div class="modal-pagamento-footer">
                    <button type="button" class="btn btn-cancelar" id="btnCancelarPagamento">Cancelar</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        const finalizar = (valor) => {
            overlay.remove();
            resolve(valor || null);
        };

        overlay.querySelectorAll('.btn-pagamento-opcao').forEach((btn) => {
            btn.addEventListener('click', () => finalizar(btn.getAttribute('data-op')));
        });

        overlay.querySelector('#btnCancelarPagamento')?.addEventListener('click', () => finalizar(null));
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) finalizar(null);
        });
    });
}

function extrairDataBr(dataTexto) {
    if (!dataTexto) return '';
    if (typeof dataTexto === 'string' && dataTexto.includes('/')) {
        return dataTexto.split(' ')[0];
    }
    try {
        return new Date(dataTexto).toLocaleDateString('pt-BR');
    } catch {
        return '';
    }
}

function atualizarPainelFilaDiaria(lista) {
    const hoje = new Date().toLocaleDateString('pt-BR');
    const ordensDia = (lista || []).filter((ordem) => extrairDataBr(ordem.data_entrada) === hoje);

    const abertas = ordensDia.filter((o) => o.status === 'Aguardando' || o.status === 'Aguardando peças').length;
    const execucao = ordensDia.filter((o) => o.status === 'Em andamento').length;
    const concluidas = ordensDia.filter((o) => o.status === 'Concluído' || o.status === 'Garantia').length;
    const semProfissional = ordensDia.filter((o) => !(o.profissional_responsavel || '').trim()).length;

    const elAbertas = document.getElementById('filaAbertas');
    const elExecucao = document.getElementById('filaExecucao');
    const elConcluidas = document.getElementById('filaConcluidas');
    const elTotal = document.getElementById('filaTotalDia');
    const elSemProf = document.getElementById('filaSemProfissional');

    if (elAbertas) elAbertas.textContent = String(abertas);
    if (elExecucao) elExecucao.textContent = String(execucao);
    if (elConcluidas) elConcluidas.textContent = String(concluidas);
    if (elTotal) elTotal.textContent = String(ordensDia.length);
    if (elSemProf) elSemProf.textContent = String(semProfissional);
}

// Carregar ordens da API
async function carregarOrdens() {
    try {
        const response = await fetch('/api/ordens/');
        ordens = await response.json();
        atualizarPainelFilaDiaria(ordens);
        carregarTabela(ordens);
    } catch (error) {
        console.error('Erro ao carregar ordens:', error);
        alertErro('Falha ao carregar ordens do servidor.');
    }
}

async function carregarProfissionaisAtivos() {
    try {
        const response = await fetch('/api/profissionais/?ativos=1');
        const dados = await response.json();
        profissionaisAtivos = Array.isArray(dados) ? dados : [];
    } catch (error) {
        profissionaisAtivos = [];
        console.error('Erro ao carregar profissionais:', error);
    }
}

function opcoesProfissionaisHtml(profissionalAtual) {
    const atual = (profissionalAtual || '').trim();
    let options = '<option value="">Selecione</option>';
    profissionaisAtivos.forEach((p) => {
        const nome = (p?.nome || '').trim();
        if (!nome) return;
        const selected = nome === atual ? ' selected' : '';
        options += `<option value="${nome.replace(/"/g, '&quot;')}"${selected}>${nome}</option>`;
    });
    return options;
}

async function finalizarOrdem(id) {
    const confirmado = window.ui?.confirmAsync
        ? await window.ui.confirmAsync('Confirma finalizar esta ordem?')
        : (window.ui ? window.ui.confirm('Confirma finalizar esta ordem?') : confirm('Confirma finalizar esta ordem?'));
    if (!confirmado) return;

    const formaPagamento = await solicitarFormaPagamento();
    if (!formaPagamento) {
        alertErro('Forma de pagamento inválida ou não informada.');
        return;
    }
    
    const dataConclusao = new Date().toISOString();
    
    try {
        const response = await fetch(`/api/ordens/${id}/status`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                status: 'Concluído',
                data_conclusao: dataConclusao,
                forma_pagamento: formaPagamento
            })
        });
        
        if (response.ok) {
            alertSucesso('Ordem finalizada. Garantia de 90 dias ativada.');
            carregarOrdens();
        } else {
            const erro = await response.json();
            alertErro(erro.erro || 'Erro desconhecido.');
        }
    } catch (error) {
        alertErro('Falha ao finalizar ordem.');
        console.error(error);
    }
}

async function ativarGarantia(id) {
    const confirmado = window.ui?.confirmAsync
        ? await window.ui.confirmAsync('Confirma ativar garantia para esta ordem?')
        : (window.ui ? window.ui.confirm('Confirma ativar garantia para esta ordem?') : confirm('Confirma ativar garantia para esta ordem?'));
    if (!confirmado) return;
    
    const dataConclusao = new Date().toISOString();
    
    try {
        const response = await fetch(`/api/ordens/${id}/status`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                status: 'Garantia',
                data_conclusao: dataConclusao
            })
        });
        
        if (response.ok) {
            alertSucesso('Garantia ativada. Nova validade de 90 dias a partir de hoje.');
            carregarOrdens();
        } else {
            const erro = await response.json();
            alertErro(erro.erro || 'Erro desconhecido.');
        }
    } catch (error) {
        alertErro('Falha ao ativar garantia.');
        console.error(error);
    }
}

async function reabrirOrdem(id) {
    const confirmado = window.ui?.confirmAsync
        ? await window.ui.confirmAsync('Confirma reabrir esta ordem para edição?')
        : (window.ui ? window.ui.confirm('Confirma reabrir esta ordem para edição?') : confirm('Confirma reabrir esta ordem para edição?'));
    if (!confirmado) return;

    try {
        const response = await fetch(`/api/ordens/${id}/reabrir`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const dados = await response.json().catch(() => ({}));
        if (response.ok) {
            alertSucesso('Ordem reaberta com sucesso.');
            carregarOrdens();
        } else {
            alertErro(dados.erro || 'Falha ao reabrir ordem.');
        }
    } catch (error) {
        alertErro('Falha ao reabrir ordem.');
        console.error(error);
    }
}

async function duplicarOrdem(id) {
    const confirmado = window.ui?.confirmAsync
        ? await window.ui.confirmAsync('Confirma duplicar esta OS para gerar uma nova ordem?')
        : (window.ui ? window.ui.confirm('Confirma duplicar esta OS para gerar uma nova ordem?') : confirm('Confirma duplicar esta OS para gerar uma nova ordem?'));
    if (!confirmado) return;

    try {
        const response = await fetch(`/api/ordens/${id}/duplicar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const dados = await response.json().catch(() => ({}));
        if (!response.ok) {
            alertErro(dados.erro || 'Falha ao duplicar OS.');
            return;
        }
        alertSucesso(`OS duplicada com sucesso (#${dados.nova_ordem_id}).`);
        carregarOrdens();
    } catch (error) {
        alertErro('Falha ao duplicar OS.');
        console.error(error);
    }
}

// Iniciar ordem
async function iniciarOrdem(id) {
    const confirmado = window.ui?.confirmAsync
        ? await window.ui.confirmAsync('Confirma iniciar esta ordem?')
        : (window.ui ? window.ui.confirm('Confirma iniciar esta ordem?') : confirm('Confirma iniciar esta ordem?'));
    if (!confirmado) return;
    
    try {
        const response = await fetch(`/api/ordens/${id}/status`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'Em andamento' })
        });
        
        if (response.ok) {
            alertSucesso('Ordem iniciada.');
            carregarOrdens();
        } else {
            const erro = await response.json();
            alertErro(erro.erro || 'Erro desconhecido.');
        }
    } catch (error) {
        alertErro('Falha ao iniciar ordem.');
        console.error(error);
    }
}

async function excluirOrdem(id) {
    const confirmado = window.ui?.confirmAsync
        ? await window.ui.confirmAsync(`Confirma excluir a ordem #${id}? Esta ação não pode ser desfeita.`)
        : (window.ui ? window.ui.confirm(`Confirma excluir a ordem #${id}? Esta ação não pode ser desfeita.`) : confirm(`Confirma excluir a ordem #${id}? Esta ação não pode ser desfeita.`));
    if (!confirmado) return;

    try {
        const response = await fetch(`/api/ordens/${id}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' }
        });
        const dados = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(dados.erro || 'Falha ao excluir ordem.');
        }
        alertSucesso('Ordem excluída com sucesso.');
        carregarOrdens();
    } catch (error) {
        alertErro(error.message);
    }
}

function carregarTabela(lista) {
    if (!tabela) return;
    
    tabela.innerHTML = "";
    
    if(lista.length === 0) {
        tabela.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 40px;">📭 Nenhuma ordem encontrada</td></tr>`;
        return;
    }
    
    lista.forEach(ordem => {
        const statusClass = getStatusClass(ordem.status);
        const valorFormatado = formatarValor(ordem.total_geral || ordem.valor);
        const diasRestantes = calcularDiasGarantia(ordem.data_conclusao, ordem.data_retirada);
        const profissionalAtual = (ordem.profissional_responsavel || '').trim();
        const semProfissionais = profissionaisAtivos.length === 0;
        
        let botoesAcao = '';
        
        if (ordem.status === 'Aguardando' || ordem.status === 'Aguardando peças') {
            botoesAcao = `
                <button class="btn-iniciar" onclick="iniciarOrdem(${ordem.id})">▶ INICIAR</button>
                <button class="btn-visualizar" onclick="visualizar(${ordem.id})">👁 VER</button>
                <button class="btn-excluir-os" onclick="excluirOrdem(${ordem.id})">🗑 EXCLUIR</button>
            `;
        } 
        else if (ordem.status === 'Em andamento') {
            botoesAcao = `
                <button class="btn-finalizar" onclick="finalizarOrdem(${ordem.id})">✅ FINALIZAR</button>
                <button class="btn-visualizar" onclick="visualizar(${ordem.id})">👁 VER</button>
                <button class="btn-excluir-os" onclick="excluirOrdem(${ordem.id})">🗑 EXCLUIR</button>
            `;
        } 
        else if (ordem.status === 'Concluído') {
            if (diasRestantes > 0) {
                botoesAcao = `
                    <button class="btn-garantia" onclick="ativarGarantia(${ordem.id})" title="Prazo para ativação de garantia">
                        🔧 GARANTIA (${diasRestantes}d)
                    </button>
                    <button class="btn-visualizar" onclick="visualizar(${ordem.id})">👁 VER</button>
                    <button class="btn-excluir-os" onclick="excluirOrdem(${ordem.id})">🗑 EXCLUIR</button>
                `;
            } else {
                botoesAcao = `
                    <span class="garantia-expirada" title="Prazo para ativar garantia expirado">
                        ⚠️ Prazo de garantia expirado
                    </span>
                    <button class="btn-visualizar" onclick="visualizar(${ordem.id})">👁 VER</button>
                    <button class="btn-excluir-os" onclick="excluirOrdem(${ordem.id})">🗑 EXCLUIR</button>
                `;
            }
        } 
        else if (ordem.status === 'Garantia') {
            if (diasRestantes > 0) {
                botoesAcao = `
                    <span class="status-garantia" title="Serviço em garantia por mais ${diasRestantes} dias">
                        🔧 Serviço na garantia (${diasRestantes} dias)
                    </span>
                    <button class="btn-visualizar" onclick="visualizar(${ordem.id})">👁 VER</button>
                    <button class="btn-excluir-os" onclick="excluirOrdem(${ordem.id})">🗑 EXCLUIR</button>
                `;
            } else {
                botoesAcao = `
                    <span class="garantia-expirada">⚠️ Garantia expirada</span>
                    <button class="btn-visualizar" onclick="visualizar(${ordem.id})">👁 VER</button>
                    <button class="btn-excluir-os" onclick="excluirOrdem(${ordem.id})">🗑 EXCLUIR</button>
                `;
            }
        }
        
        tabela.innerHTML += `
            <tr>
                <td><strong>#${ordem.id}</strong></td>
                <td>
                    <div class="cliente-coluna">
                        <div class="cliente-nome">${ordem.cliente_nome || ordem.cliente?.nome_cliente || '---'}</div>
                        <button class="btn-editar-cliente" onclick="editarCliente(${ordem.cliente_id})">✏ Editar Cliente</button>
                    </div>
                </td>
                <td>${ordem.cliente?.fabricante || ''} ${ordem.cliente?.modelo || ''}</td>
                <td>${ordem.cliente?.placa || '---'}</td>
                <td>
                    <div class="profissional-coluna">
                        <div class="profissional-editor">
                            <select
                                id="profissional-${ordem.id}"
                                class="input-profissional select-profissional"
                                ${semProfissionais ? 'disabled' : ''}
                            >${opcoesProfissionaisHtml(profissionalAtual)}</select>
                            <button class="btn-salvar-profissional" onclick="salvarProfissional(${ordem.id})" ${semProfissionais ? 'disabled' : ''}>Salvar</button>
                        </div>
                    </div>
                </td>
                <td>${valorFormatado}</td>
                <td><span class="status-badge ${statusClass}">${ordem.status}</span></td>
                <td class="acao-buttons">${botoesAcao}</td>
            </tr>
        `;
    });
}

async function salvarProfissional(id) {
    const input = document.getElementById(`profissional-${id}`);
    const profissional = (input?.value || '').trim();

    if (!profissionaisAtivos.length) {
        alertErro('Não há profissionais cadastrados/ativos para selecionar.');
        return;
    }
    if (!profissional) {
        alertErro('Selecione um profissional cadastrado.');
        return;
    }
    const valido = profissionaisAtivos.some((p) => (p?.nome || '').trim() === profissional);
    if (!valido) {
        alertErro('Profissional inválido. Selecione um profissional cadastrado.');
        return;
    }

    try {
        const response = await fetch(`/api/ordens/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                profissional_responsavel: profissional,
                forcar_edicao: true
            })
        });

        const dados = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(dados.erro || 'Falha ao salvar profissional.');
        }

        alertSucesso('Profissional atualizado com sucesso.');
        carregarOrdens();
    } catch (error) {
        alertErro(error.message);
    }
}

// Buscar cliente
async function buscarCliente() {
    const termo = buscaCliente.value.trim();
    if (!termo) return alertErro('Digite o nome ou CPF para busca.');
    
    try {
        const response = await fetch(`/api/ordens/busca?cliente=${encodeURIComponent(termo)}`);
        const filtradas = await response.json();
        carregarTabela(filtradas);
    } catch (error) {
        alertErro('Falha na busca.');
        console.error(error);
    }
}

async function aplicarFiltrosAvancados() {
    const params = new URLSearchParams();
    const cliente = (document.getElementById('buscaCliente')?.value || '').trim();
    const dataInicio = (document.getElementById('filtroDataInicio')?.value || '').trim();
    const dataFim = (document.getElementById('filtroDataFim')?.value || '').trim();
    const profissional = (document.getElementById('filtroProfissional')?.value || '').trim();
    const formaPagamento = (document.getElementById('filtroFormaPagamento')?.value || '').trim();

    if (cliente) params.set('cliente', cliente);
    if (dataInicio) params.set('data_inicio', dataInicio);
    if (dataFim) params.set('data_fim', dataFim);
    if (profissional) params.set('profissional', profissional);
    if (formaPagamento) params.set('forma_pagamento', formaPagamento);

    try {
        const response = await fetch(`/api/ordens/busca?${params.toString()}`);
        const filtradas = await response.json();
        carregarTabela(Array.isArray(filtradas) ? filtradas : []);
    } catch (error) {
        alertErro('Falha ao aplicar filtros avançados.');
        console.error(error);
    }
}

// Filtrar por status
function filtrarPorStatus(status) {
    let filtradas = [];
    
    if (status === 'todas') {
        filtradas = ordens;
    } else if (status === 'aguardando') {
        filtradas = ordens.filter(o => o.status === 'Aguardando' || o.status === 'Aguardando peças');
    } else if (status === 'andamento') {
        filtradas = ordens.filter(o => o.status === 'Em andamento');
    } else if (status === 'concluido') {
        filtradas = ordens.filter(o => o.status === 'Concluído');
    } else if (status === 'garantia') {
        filtradas = ordens.filter(o => o.status === 'Garantia');
    }
    
    carregarTabela(filtradas);
    
    document.querySelectorAll('.btn-filtro').forEach(btn => {
        btn.classList.remove('ativo');
    });
    event.target.classList.add('ativo');
}

// Visualizar
function visualizar(id) {
    window.location.href = `/visualizarOS.html?id=${id}`;
}

function editarCliente(id) {
    window.location.href = `/cadastroCliente.html?id=${id}`;
}

// Voltar
function voltarInicio() {
    window.location.href = "/";
}

// Mostrar todas
function carregarTodasOrdens() {
    if (buscaCliente) buscaCliente.value = '';
    carregarOrdens();
}

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    tabela = document.getElementById("tabelaOrdens");
    buscaCliente = document.getElementById("buscaCliente");
    carregarProfissionaisAtivos().finally(() => carregarOrdens());
    
    if (buscaCliente) {
        buscaCliente.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') buscarCliente();
        });
    }
});

window.reabrirOrdem = reabrirOrdem;
window.duplicarOrdem = duplicarOrdem;
window.aplicarFiltrosAvancados = aplicarFiltrosAvancados;
window.salvarProfissional = salvarProfissional;
window.excluirOrdem = excluirOrdem;

window.editarCliente = editarCliente;

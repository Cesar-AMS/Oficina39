// visualizarOS.js

const params = new URLSearchParams(window.location.search);
const id = params.get("id");
const origem = params.get("origem") || '';
const autoPrint = params.get("autoprint") === '1';

let ordem = null;

function destinoVoltar() {
    if (origem === 'debitos') return '/debitos.html';
    return '/consultarOS.html';
}

function atualizarLinksVoltar() {
    const destino = destinoVoltar();
    document.getElementById('linkVoltarVisualizacao')?.setAttribute('href', destino);
    document.getElementById('linkVoltarVisualizacaoRodape')?.setAttribute('href', destino);
}

function alertErro(mensagem) {
    if (window.ui) return window.ui.error(mensagem);
    alert(`Erro: ${mensagem}`);
}

// ===========================================
// FUNÃ‡Ã•ES DE FORMATAÃ‡ÃƒO
// ===========================================

function formatarValor(valor) {
    if (!valor && valor !== 0) return 'R$ 0,00';
    return 'R$ ' + valor.toFixed(2).replace('.', ',');
}

function formatarData(data) {
    if (!data) return '';
    try {
        if (typeof data === 'string' && data.includes('T')) {
            const date = new Date(data);
            if (isNaN(date.getTime())) return data;
            return date.toLocaleDateString('pt-BR') + ' ' + date.toLocaleTimeString('pt-BR');
        }
        else if (typeof data === 'string' && data.includes('/')) {
            return data;
        }
        return data;
    } catch {
        return data;
    }
}

function getStatusBadge(status) {
    const statusLower = (status || '').toLowerCase();
    let classe = '';
    
    if (statusLower.includes('aguardando')) classe = 'status-aguardando';
    else if (statusLower.includes('andamento')) classe = 'status-andamento';
    else if (statusLower.includes('conclu')) classe = 'status-concluido';
    else if (statusLower.includes('garantia')) classe = 'status-garantia';
    
    const statusExibicao = status === 'ConcluÃ­do' ? 'Finalizado' : (status || 'NÃ£o definido');
    return `<span class="status-badge ${classe}">${statusExibicao}</span>`;
}

// ===========================================
// FUNÃ‡ÃƒO AUXILIAR PARA SETAR VALOR
// ===========================================

function setValue(id, valor, tipo = 'input') {
    const el = document.getElementById(id);
    if (el) {
        if (tipo === 'span') {
            el.textContent = valor;
        } else {
            el.value = valor || '';
        }
    }
}

// ===========================================
// PREENCHER CAMPOS
// ===========================================

function preencherCampos() {
    if (!ordem) {
        return;
    }

    const cliente = ordem.cliente || {};
    
    setValue('ordemId', ordem.id, 'span');
    document.getElementById('statusDisplay').innerHTML = getStatusBadge(ordem.status);
    
    setValue('nome_cliente', cliente.nome_cliente);
    setValue('cpf', cliente.cpf);
    setValue('endereco', cliente.endereco);
    
    setValue('placa', cliente.placa);
    setValue('fabricante', cliente.fabricante);
    setValue('modelo', cliente.modelo);
    setValue('ano', cliente.ano);
    setValue('motor', cliente.motor);
    setValue('combustivel', cliente.combustivel);
    setValue('cor', cliente.cor);
    setValue('tanque', cliente.tanque);
    setValue('km', cliente.km);
    setValue('direcao', cliente.direcao);
    setValue('ar', cliente.ar);
    
    setValue('diagnostico', ordem.diagnostico);
    setValue('profissional_responsavel', ordem.profissional_responsavel);
    setValue('assinatura_cliente', ordem.assinatura_cliente);
    setValue('forma_pagamento', ordem.forma_pagamento || '---');
    setValue('status_financeiro', ordem.status_financeiro || '---');
    setValue('debito_valor_restante', formatarValor(ordem.saldo_pendente || 0));
    setValue('debito_vencimento', ordem.debito_vencimento || '---');
    setValue('debito_observacao', ordem.debito_observacao || (Number(ordem.saldo_pendente || 0) > 0 ? 'Pagamento pendente sem observaÃ§Ã£o.' : 'Sem dÃ©bito pendente.'));
    
    setValue('data_entrada', formatarData(ordem.data_entrada));
    setValue('data_emissao', formatarData(ordem.data_emissao));
    setValue('data_retirada', formatarData(ordem.data_retirada));
    
    const tbodyServicos = document.getElementById('tabela-servicos');
    if (tbodyServicos) {
        if (ordem.servicos && ordem.servicos.length > 0) {
            let html = '';
            ordem.servicos.forEach(s => {
                html += `
                    <tr>
                        <td>${s.codigo_servico || '---'}</td>
                        <td>${s.descricao_servico || ''}</td>
                        <td>${formatarValor(s.valor_servico)}</td>
                    </tr>
                `;
            });
            tbodyServicos.innerHTML = html;
        } else {
            tbodyServicos.innerHTML = `<tr><td colspan="3" class="text-center mensagem-vazia">Nenhum serviÃ§o registrado</td></tr>`;
        }
    }
    
    const tbodyPecas = document.getElementById('tabela-pecas');
    if (tbodyPecas) {
        if (ordem.pecas && ordem.pecas.length > 0) {
            let html = '';
            ordem.pecas.forEach(p => {
                const total = (p.quantidade || 0) * (p.valor_unitario || 0);
                html += `
                    <tr>
                        <td>${p.codigo_peca || '---'}</td>
                        <td>${p.descricao_peca || ''}</td>
                        <td>${p.quantidade || 0}</td>
                        <td>${formatarValor(p.valor_unitario)}</td>
                        <td>${formatarValor(total)}</td>
                    </tr>
                `;
            });
            tbodyPecas.innerHTML = html;
        } else {
            tbodyPecas.innerHTML = `<tr><td colspan="5" class="text-center mensagem-vazia">Nenhuma peÃ§a registrada</td></tr>`;
        }
    }
    
    setValue('total-servicos', formatarValor(ordem.total_servicos || 0), 'span');
    setValue('total-pecas', formatarValor(ordem.total_pecas || 0), 'span');
    setValue('total-geral', formatarValor(ordem.total_geral || 0), 'span');
    setValue('desconto-valor', formatarValor(ordem.desconto_valor || 0), 'span');
    setValue('total-cobrado', formatarValor(ordem.total_cobrado || ordem.total_geral || 0), 'span');
    setValue('total-pago', formatarValor(ordem.total_pago || 0), 'span');
    setValue('saldo-pendente', formatarValor(ordem.saldo_pendente || 0), 'span');

    const tbodyPagamentos = document.getElementById('tabela-pagamentos');
    if (tbodyPagamentos) {
        if (ordem.pagamentos && ordem.pagamentos.length > 0) {
            tbodyPagamentos.innerHTML = ordem.pagamentos.map((pagamento) => `
                <tr>
                    <td>${pagamento.data_pagamento || '---'}</td>
                    <td>${pagamento.forma_pagamento || '---'}</td>
                    <td>${formatarValor(pagamento.valor || 0)}</td>
                    <td>${pagamento.observacao || '---'}</td>
                </tr>
            `).join('');
        } else {
            tbodyPagamentos.innerHTML = `<tr><td colspan="4" class="text-center mensagem-vazia">Nenhum pagamento registrado</td></tr>`;
        }
    }
}

function renderTimelineStatus(logs) {
    const el = document.getElementById('timelineStatusOS');
    if (!el) return;
    if (!logs || !logs.length) {
        el.innerHTML = '<div class="timeline-vazio">Nenhum evento de status registrado.</div>';
        return;
    }

    el.innerHTML = logs.map((log) => `
        <div class="timeline-item">
            <div class="timeline-cabecalho">
                <strong>${log.status_anterior || '---'} â†’ ${log.status_novo}</strong>
                <span>${log.data_evento || '---'}</span>
            </div>
            <div class="timeline-detalhes">
                Operador: ${log.operador || 'sistema'} | Origem: ${log.origem || 'api'}
                ${log.forma_pagamento ? ` | Pagamento: ${log.forma_pagamento}` : ''}
                ${log.observacao ? `<br>${log.observacao}` : ''}
            </div>
        </div>
    `).join('');
}

// ===========================================
// MOSTRAR ERRO
// ===========================================

function mostrarErro(mensagem) {
    const container = document.querySelector('.container');
    container.innerHTML = `
        <h1 style="color: var(--danger); text-align: center; margin: 50px 0;">âŒ ${mensagem}</h1>
        <div style="text-align: center;">
            <button class="btn btn-voltar" onclick="voltar()">Voltar</button>
        </div>
    `;
}

// ===========================================
// CARREGAR ORDEM
// ===========================================

async function carregarOrdem() {
    if (!id) {
        mostrarErro("ID da ordem nao informado");
        return false;
    }

    try {
        const response = await fetch(`/api/ordens/${id}`);

        if (!response.ok) {
            if (response.status === 404) {
                mostrarErro(`Ordem #${id} nao encontrada`);
            } else {
                mostrarErro("Erro ao carregar ordem");
            }
            return false;
        }

        ordem = await response.json();
        preencherCampos();
        carregarTimelineStatus();
        return true;
    } catch (error) {
        console.error('Erro:', error);
        mostrarErro("Erro de conexao com o servidor");
        return false;
    }
}

async function carregarTimelineStatus() {
    if (!id) return;
    try {
        const response = await fetch(`/api/ordens/${id}/status-log`);
        if (!response.ok) {
            renderTimelineStatus([]);
            return;
        }
        const logs = await response.json();
        renderTimelineStatus(Array.isArray(logs) ? logs : []);
    } catch {
        renderTimelineStatus([]);
    }
}

// ===========================================
// FUNÃ‡Ã•ES DE NAVEGAÃ‡ÃƒO
// ===========================================

function voltar() {
    window.location.assign(destinoVoltar());
}

function editarOrdem() {
    if (id) {
        const queryOrigem = origem ? `&origem=${encodeURIComponent(origem)}` : '';
        window.location.assign(`/editarOS.html?id=${id}${queryOrigem}`);
    }
}

// ===========================================
// IMPRIMIR ORDEM - GERA PDF DIRETO
// ===========================================

function imprimirOrdem() {
    const ordemId = document.getElementById('ordemId').textContent;

    if (!ordemId) {
        alertErro('ID da ordem nao encontrado.');
        return;
    }

    const destinoPdf = `/api/export/gerar-pdf/${ordemId}?inline=1`;
    window.location.assign(destinoPdf);
}

// ===========================================
// ATALHOS DE TECLADO
// ===========================================

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') voltar();
    if (e.key === 'e' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        editarOrdem();
    }
    if (e.key === 'p' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        imprimirOrdem();
    }
});

// ===========================================
// INICIALIZAÃ‡ÃƒO
// ===========================================

document.addEventListener('DOMContentLoaded', async function() {
    atualizarLinksVoltar();
    const carregou = await carregarOrdem();
    if (carregou && autoPrint) {
        setTimeout(() => {
            imprimirOrdem();
        }, 250);
    }
});



// fluxoCaixa.js

const PERIODO_CAIXA = 'dia';

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

function recarregarFluxoAtivo() {
    carregarCaixaDia();
}

async function carregarCaixaDia() {
    try {
        const response = await fetch(`/api/fluxo/periodo?periodo=${PERIODO_CAIXA}`);
        
        if (!response.ok) {
            throw new Error(`Erro HTTP ${response.status}`);
        }
        
        const dados = await response.json();
        
        // Garantir que são arrays
        const entradas = Array.isArray(dados.entradas) ? dados.entradas : [];
        const saidas = Array.isArray(dados.saidas) ? dados.saidas : [];
        
        // Calcular totais
        const totalEntradas = entradas.reduce((acc, item) => acc + (item.total || 0), 0);
        const totalSaidas = saidas.reduce((acc, item) => acc + (item.valor || 0), 0);
        const saldo = totalEntradas - totalSaidas;
        
        // Atualizar elementos de resumo
        const elTotalEntradas = document.getElementById('totalEntradas');
        const elTotalSaidas = document.getElementById('totalSaidas');
        const elSaldo = document.getElementById('saldo');
        
        if (elTotalEntradas) elTotalEntradas.textContent = formatarValor(totalEntradas);
        if (elTotalSaidas) elTotalSaidas.textContent = formatarValor(totalSaidas);
        
        if (elSaldo) {
            elSaldo.textContent = formatarValor(saldo);
            elSaldo.className = 'valor ' + (saldo >= 0 ? 'valor-positivo' : 'valor-negativo');
        }
        
        // Carregar tabelas
        carregarTabelaSaidas(saidas);
        carregarTabelaEntradas(entradas);
        
    } catch (error) {
        console.error('❌ Erro detalhado:', error);
        alertErro(`Falha ao carregar dados: ${error.message}`);
    }
}

// ===========================================
// CARREGAR TABELA DE SAÍDAS
// ===========================================
function carregarTabelaSaidas(lista) {
    const tbody = document.getElementById('tabelaSaidas');
    if (!tbody) return;
    
    if (!lista || lista.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; padding: 30px;">📭 Nenhuma saída registrada</td></tr>`;
        return;
    }
    
    tbody.innerHTML = '';
    
    lista.forEach(saida => {
        tbody.innerHTML += `
            <tr>
                <td>${saida.data || '---'}</td>
                <td>${saida.categoria || '---'}</td>
                <td>${saida.descricao || '---'}</td>
                <td>${formatarValor(saida.valor)}</td>
                <td>
                    <button class="btn-excluir" onclick="excluirSaida(${saida.id})">🗑️ Excluir</button>
                </td>
            </tr>
        `;
    });
}

// ===========================================
// CARREGAR TABELA DE ENTRADAS
// ===========================================
function carregarTabelaEntradas(lista) {
    const tbody = document.getElementById('tabelaEntradas');
    if (!tbody) {
        console.error('❌ Tabela de entradas não encontrada!');
        return;
    }
    
    if (!lista || lista.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; padding: 30px;">📭 Nenhuma entrada no período</td></tr>`;
        return;
    }
    
    tbody.innerHTML = '';
    
    lista.forEach(entrada => {
        tbody.innerHTML += `
            <tr>
                <td>${entrada.data || '---'}</td>
                <td>${entrada.cliente_nome || '---'}</td>
                <td>${entrada.veiculo || '---'}</td>
                <td>${formatarValor(entrada.total)}</td>
                <td>${entrada.status || '---'}</td>
            </tr>
        `;
    });
}

// ===========================================
// MODAL DE NOVA SAÍDA
// ===========================================
function abrirModalSaida() {
    const modal = document.getElementById('modalSaida');
    if (modal) {
        modal.style.display = 'flex';
        document.getElementById('saidaData').value = new Date().toISOString().split('T')[0];
        document.getElementById('saidaDescricao').value = '';
        document.getElementById('saidaValor').value = '';
        document.getElementById('saidaCategoria').value = '';
    } else {
        console.error("❌ Modal não encontrado!");
    }
}

function fecharModalSaida() {
    const modal = document.getElementById('modalSaida');
    if (modal) {
        modal.style.display = 'none';
    }
}

// ===========================================
// MODAL CALCULADORA
// ===========================================
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
    if (!modal) return;
    modal.style.display = 'none';
}

function atualizarDisplayCalculadora(valor) {
    const display = document.getElementById('calcDisplay');
    if (!display) return;
    display.value = valor;
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
            expressaoCalculadora += expressaoCalculadora ? '0.' : '0.';
            atualizarDisplayCalculadora(expressaoCalculadora);
            return;
        }
    }

    if (expressaoCalculadora === '0' && valor !== '.') {
        expressaoCalculadora = valor;
    } else {
        expressaoCalculadora += valor;
    }
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
        if (!permitido.test(expressaoCalculadora)) {
            throw new Error('Expressao invalida');
        }
        const resultado = Function(`"use strict"; return (${expressaoCalculadora});`)();
        if (!Number.isFinite(resultado)) {
            throw new Error('Resultado invalido');
        }
        expressaoCalculadora = Number(resultado.toFixed(2)).toString();
        atualizarDisplayCalculadora(expressaoCalculadora);
    } catch (error) {
        expressaoCalculadora = '';
        atualizarDisplayCalculadora('Erro');
    }
}

// ===========================================
// SALVAR NOVA SAÍDA
// ===========================================
async function salvarSaida() {
    // Pegar valores do modal
    const descricaoInput = document.getElementById('saidaDescricao');
    const valorInput = document.getElementById('saidaValor');
    const dataInput = document.getElementById('saidaData');
    const categoriaSelect = document.getElementById('saidaCategoria');
    
    if (!descricaoInput || !valorInput) {
        console.error("❌ Campos não encontrados no DOM!");
        alertErro('Erro interno: campos não encontrados.');
        return;
    }
    
    const descricao = descricaoInput.value;
    const valor = valorInput.value;
    const data = dataInput ? dataInput.value : '';
    const categoria = categoriaSelect ? categoriaSelect.value : 'Outros';
    
    // Validações
    if (!descricao || descricao.trim() === '') {
        alertErro('Descrição é obrigatória.');
        descricaoInput.focus();
        return;
    }
    
    if (!valor || valor.trim() === '') {
        alertErro('Valor é obrigatório.');
        valorInput.focus();
        return;
    }
    
    // Converter valor (tratando vírgula)
    let valorLimpo = valor.replace(',', '.');
    const valorNumerico = parseFloat(valorLimpo);
    
    if (isNaN(valorNumerico) || valorNumerico <= 0) {
        alertErro('Valor inválido.');
        return;
    }
    
    // Preparar dados
    const saida = {
        descricao: descricao.trim(),
        valor: valorNumerico,
        data: data || new Date().toISOString().split('T')[0],
        categoria: categoria || 'Outros'
    };
    
    try {
        const response = await fetch('/api/fluxo/saidas', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(saida)
        });
        
        if (response.ok) {
            await response.json();
            alertSucesso('Saída registrada com sucesso.');
            fecharModalSaida();
            recarregarFluxoAtivo();
        } else {
            const erro = await response.json();
            console.error("❌ Erro da API:", erro);
            alertErro(erro.erro || 'Erro desconhecido.');
        }
    } catch (error) {
        console.error('❌ Erro na requisição:', error);
        alertErro('Falha ao conectar com o servidor.');
    }
}

// ===========================================
// EXCLUIR SAÍDA
// ===========================================
async function excluirSaida(id) {
    const confirmado = window.ui?.confirmAsync
        ? await window.ui.confirmAsync('Confirma excluir esta saída?')
        : (window.ui ? window.ui.confirm('Confirma excluir esta saída?') : confirm('Confirma excluir esta saída?'));
    if (!confirmado) return;
    
    try {
        const response = await fetch(`/api/fluxo/saidas/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            alertSucesso('Saída excluída.');
            recarregarFluxoAtivo();
        } else {
            const erro = await response.json();
            alertErro(erro.erro || 'Erro desconhecido.');
        }
    } catch (error) {
        console.error('❌ Erro:', error);
        alertErro('Falha ao excluir saída.');
    }
}

// ===========================================
// INICIALIZAÇÃO
// ===========================================
document.addEventListener('DOMContentLoaded', function() {
    carregarCaixaDia();
});

// ===========================================
// EXPORTAR FUNÇÕES PARA O ESCOPO GLOBAL
// ===========================================
window.carregarFluxo = carregarCaixaDia; // compatibilidade retroativa
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
